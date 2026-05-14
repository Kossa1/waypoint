from pydantic import BaseModel, Field


class CityBase(BaseModel):
    name: str
    country: str
    region: str
    cost_index: float = Field(ge=0.0, le=1.0)
    safety_index: float = Field(ge=0.0, le=1.0)
    tourism_volume: float = Field(ge=0.0, le=1.0)
    warmth_index: float = Field(ge=0.0, le=1.0)
    outdoor_score: float = Field(ge=0.0, le=1.0)
    food_score: float = Field(ge=0.0, le=1.0)
    nightlife_score: float = Field(ge=0.0, le=1.0)
    walkability: float = Field(ge=0.0, le=1.0)
    english_friendly: float = Field(ge=0.0, le=1.0)


class CityOut(CityBase):
    id: int
    similarity: float | None = None

    model_config = {"from_attributes": True}


class PreferenceVector(BaseModel):
    cost_index: float = Field(default=0.5, ge=0.0, le=1.0)
    safety_index: float = Field(default=0.5, ge=0.0, le=1.0)
    tourism_volume: float = Field(default=0.5, ge=0.0, le=1.0)
    warmth_index: float = Field(default=0.5, ge=0.0, le=1.0)
    outdoor_score: float = Field(default=0.5, ge=0.0, le=1.0)
    food_score: float = Field(default=0.5, ge=0.0, le=1.0)
    nightlife_score: float = Field(default=0.5, ge=0.0, le=1.0)
    walkability: float = Field(default=0.5, ge=0.0, le=1.0)
    english_friendly: float = Field(default=0.5, ge=0.0, le=1.0)


class ComparisonCreate(BaseModel):
    session_id: str
    city_a_id: int
    city_b_id: int
    preferred_city_id: int
