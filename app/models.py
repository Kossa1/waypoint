from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    country = Column(String, nullable=False)
    region = Column(String, nullable=False)

    # All scores normalized 0.0–1.0
    cost_index = Column(Float, nullable=False)        # 0 = very cheap, 1 = very expensive
    safety_index = Column(Float, nullable=False)      # 0 = unsafe, 1 = very safe
    tourism_volume = Column(Float, nullable=False)    # 0 = off-the-beaten-path, 1 = very touristy
    warmth_index = Column(Float, nullable=False)      # 0 = cold, 1 = very warm
    outdoor_score = Column(Float, nullable=False)
    food_score = Column(Float, nullable=False)
    nightlife_score = Column(Float, nullable=False)
    walkability = Column(Float, nullable=False)
    english_friendly = Column(Float, nullable=False)


class UserComparison(Base):
    __tablename__ = "user_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    city_a_id = Column(Integer, nullable=False)
    city_b_id = Column(Integer, nullable=False)
    preferred_city_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
