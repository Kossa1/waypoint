import uuid
from typing import Annotated, List
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import numpy as np

from app.database import engine, get_db
from app.models import Base, City, UserComparison
from app.schemas import PreferenceVector, CityOut
from app.recommender import (
    recommend, infer_preferences_from_comparisons,
    explain_match, city_to_vector, FEATURE_FIELDS,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Waypoint")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/recommend", response_class=HTMLResponse)
def get_recommendations(
    request: Request,
    city_ids: Annotated[List[int], Form()] = [],
    db: Session = Depends(get_db),
):
    if not city_ids:
        raise HTTPException(status_code=400, detail="Select at least one city you've loved.")

    source_cities = db.query(City).filter(City.id.in_(city_ids)).all()
    if not source_cities:
        raise HTTPException(status_code=400, detail="None of the provided city IDs were found.")

    vectors = np.array([city_to_vector(c) for c in source_cities])
    mean_vec = vectors.mean(axis=0)
    prefs = PreferenceVector(**{f: float(mean_vec[i]) for i, f in enumerate(FEATURE_FIELDS)})
    pref_vec = mean_vec

    raw_results = recommend(prefs, db, top_n=5, exclude_ids=city_ids)

    results = []
    for city, score in raw_results:
        c = CityOut.model_validate(city)
        c.similarity = score
        results.append({
            "city": c,
            "score": score,
            "reasons": explain_match(pref_vec, city),
            "underrated": round((1 - city.tourism_volume) * 100),
        })

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "results": results,
            "source_cities": [c.name for c in source_cities],
        },
    )


@app.post("/compare", response_class=HTMLResponse)
def record_comparison(
    request: Request,
    session_id: str = Form(...),
    city_a_id: int = Form(...),
    city_b_id: int = Form(...),
    preferred_city_id: int = Form(...),
    db: Session = Depends(get_db),
):
    if preferred_city_id not in (city_a_id, city_b_id):
        raise HTTPException(status_code=400, detail="preferred_city_id must be one of the two cities")

    comparison = UserComparison(
        session_id=session_id,
        city_a_id=city_a_id,
        city_b_id=city_b_id,
        preferred_city_id=preferred_city_id,
    )
    db.add(comparison)
    db.commit()
    return RedirectResponse(url=f"/compare/next?session_id={session_id}", status_code=303)


@app.get("/compare/start", response_class=HTMLResponse)
def compare_start(request: Request, db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    cities = db.query(City).order_by(City.name).all()
    if len(cities) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 cities to compare")
    city_a, city_b = cities[0], cities[1]
    return templates.TemplateResponse(
        "compare.html",
        {
            "request": request,
            "session_id": session_id,
            "city_a": city_a,
            "city_b": city_b,
            "round": 1,
        },
    )


@app.get("/compare/next", response_class=HTMLResponse)
def compare_next(request: Request, session_id: str, db: Session = Depends(get_db)):
    comparisons = (
        db.query(UserComparison)
        .filter(UserComparison.session_id == session_id)
        .all()
    )
    seen_pairs = {(c.city_a_id, c.city_b_id) for c in comparisons}
    all_cities = db.query(City).order_by(City.id).all()

    # Find next unseen pair
    next_pair = None
    for i, a in enumerate(all_cities):
        for b in all_cities[i + 1:]:
            if (a.id, b.id) not in seen_pairs and len(comparisons) < 5:
                next_pair = (a, b)
                break
        if next_pair:
            break

    if not next_pair:
        prefs = infer_preferences_from_comparisons(session_id, db)
        results = recommend(prefs, db, top_n=5)
        cities_out = []
        for city, score in results:
            c = CityOut.model_validate(city)
            c.similarity = score
            cities_out.append(c)
        return templates.TemplateResponse(
            "results.html",
            {"request": request, "results": cities_out, "prefs": prefs},
        )

    return templates.TemplateResponse(
        "compare.html",
        {
            "request": request,
            "session_id": session_id,
            "city_a": next_pair[0],
            "city_b": next_pair[1],
            "round": len(comparisons) + 1,
        },
    )


@app.get("/api/cities")
def api_cities(db: Session = Depends(get_db)):
    return [CityOut.model_validate(c) for c in db.query(City).order_by(City.name).all()]
