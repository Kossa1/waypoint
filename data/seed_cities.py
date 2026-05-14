"""Run with: python -m data.seed_cities from the project root."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal, engine
from app.models import Base, City

Base.metadata.create_all(bind=engine)

# fmt: off
CITIES = [
    # name,            country,       region,          cost, safety, tourism, warmth, outdoor, food,  night, walk,  english
    ("Lisbon",         "Portugal",    "Europe",         0.38,  0.82,   0.72,   0.62,   0.60,   0.85,  0.75,  0.78,  0.80),
    ("Tokyo",          "Japan",       "Asia",           0.65,  0.95,   0.90,   0.52,   0.55,   0.97,  0.70,  0.92,  0.45),
    ("Medellín",       "Colombia",    "South America",  0.25,  0.55,   0.50,   0.78,   0.72,   0.80,  0.82,  0.65,  0.30),
    ("Chiang Mai",     "Thailand",    "Asia",           0.18,  0.72,   0.65,   0.85,   0.80,   0.82,  0.55,  0.58,  0.62),
    ("Cape Town",      "South Africa","Africa",         0.30,  0.48,   0.68,   0.65,   0.92,   0.78,  0.72,  0.60,  0.90),
    ("Vienna",         "Austria",     "Europe",         0.68,  0.93,   0.75,   0.40,   0.55,   0.88,  0.68,  0.85,  0.82),
    ("Mexico City",    "Mexico",      "North America",  0.28,  0.42,   0.62,   0.60,   0.45,   0.93,  0.85,  0.70,  0.40),
    ("Tbilisi",        "Georgia",     "Europe/Asia",    0.20,  0.75,   0.38,   0.55,   0.70,   0.88,  0.72,  0.65,  0.50),
    ("Barcelona",      "Spain",       "Europe",         0.62,  0.78,   0.88,   0.65,   0.68,   0.90,  0.92,  0.82,  0.70),
    ("Reykjavik",      "Iceland",     "Europe",         0.88,  0.98,   0.58,   0.10,   0.95,   0.72,  0.60,  0.72,  0.98),
    ("Hanoi",          "Vietnam",     "Asia",           0.15,  0.70,   0.62,   0.80,   0.55,   0.90,  0.60,  0.68,  0.42),
    ("Budapest",       "Hungary",     "Europe",         0.32,  0.82,   0.70,   0.42,   0.50,   0.85,  0.80,  0.80,  0.72),
    ("Queenstown",     "New Zealand", "Oceania",        0.72,  0.95,   0.60,   0.38,   0.98,   0.75,  0.55,  0.52,  0.98),
    ("Marrakech",      "Morocco",     "Africa",         0.22,  0.62,   0.72,   0.72,   0.52,   0.88,  0.35,  0.60,  0.55),
    ("Porto",          "Portugal",    "Europe",         0.35,  0.88,   0.65,   0.58,   0.55,   0.87,  0.68,  0.75,  0.78),
]
# fmt: on


def seed():
    db = SessionLocal()
    try:
        existing = db.query(City).count()
        if existing > 0:
            print(f"Database already has {existing} cities — skipping seed.")
            return

        for row in CITIES:
            city = City(
                name=row[0],
                country=row[1],
                region=row[2],
                cost_index=row[3],
                safety_index=row[4],
                tourism_volume=row[5],
                warmth_index=row[6],
                outdoor_score=row[7],
                food_score=row[8],
                nightlife_score=row[9],
                walkability=row[10],
                english_friendly=row[11],
            )
            db.add(city)
        db.commit()
        print(f"Seeded {len(CITIES)} cities.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
