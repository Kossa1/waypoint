import uuid
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Base, City, UserComparison
from app.schemas import PreferenceVector, ComparisonCreate, CityOut
from app.recommender import recommend, infer_preferences_from_comparisons, FEATURE_FIELDS

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Waypoint")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    cities = db.query(City).order_by(City.name).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "fields": FEATURE_FIELDS, "cities": cities},
    )


@app.post("/recommend", response_class=HTMLResponse)
def get_recommendations(
    request: Request,
    cost_index: float = Form(0.5),
    safety_index: float = Form(0.5),
    tourism_volume: float = Form(0.5),
    warmth_index: float = Form(0.5),
    outdoor_score: float = Form(0.5),
    food_score: float = Form(0.5),
    nightlife_score: float = Form(0.5),
    walkability: float = Form(0.5),
    english_friendly: float = Form(0.5),
    db: Session = Depends(get_db),
):
    prefs = PreferenceVector(
        cost_index=cost_index,
        safety_index=safety_index,
        tourism_volume=tourism_volume,
        warmth_index=warmth_index,
        outdoor_score=outdoor_score,
        food_score=food_score,
        nightlife_score=nightlife_score,
        walkability=walkability,
        english_friendly=english_friendly,
    )
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
