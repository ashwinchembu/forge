from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from enum import Enum


# ---- Workout Models ----

class ExerciseSet(BaseModel):
    set_number: int
    weight_lbs: float
    reps: int
    rpe: Optional[float] = None


class Exercise(BaseModel):
    name: str
    sets: list[ExerciseSet]
    notes: Optional[str] = None


class WorkoutSource(str, Enum):
    hevy = "hevy"
    manual = "manual"


class Workout(BaseModel):
    date: datetime
    name: str  # "Upper A", "Lower B", etc.
    duration_minutes: Optional[int] = None
    exercises: list[Exercise]
    total_volume_lbs: Optional[float] = None
    calories_burned: Optional[int] = None
    source: WorkoutSource = WorkoutSource.manual
    source_id: Optional[str] = None  # hevy workout id


class WorkoutInDB(Workout):
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---- Nutrition Models ----

class Meal(BaseModel):
    name: str  # "Breakfast", "Lunch", etc.
    foods: list[str] = []
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None


class DailyNutrition(BaseModel):
    date: date
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    water_ml: Optional[float] = None
    meals: list[Meal] = []
    source: str = "health_auto_export"


class DailyNutritionInDB(DailyNutrition):
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---- Recovery Models (Oura + Apple Health) ----

class SleepData(BaseModel):
    total_hours: Optional[float] = None
    deep_hours: Optional[float] = None
    rem_hours: Optional[float] = None
    light_hours: Optional[float] = None
    awake_hours: Optional[float] = None
    sleep_score: Optional[int] = None


class DailyRecovery(BaseModel):
    date: date
    sleep: Optional[SleepData] = None
    resting_heart_rate: Optional[int] = None
    hrv_ms: Optional[float] = None
    body_temp_deviation: Optional[float] = None
    readiness_score: Optional[int] = None
    activity_score: Optional[int] = None
    steps: Optional[int] = None
    source: str = "health_auto_export"


class DailyRecoveryInDB(DailyRecovery):
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---- Body Metrics ----

class BodyMetrics(BaseModel):
    date: date
    weight_lbs: Optional[float] = None
    body_fat_pct: Optional[float] = None
    lean_mass_lbs: Optional[float] = None


# ---- Program Target Models ----

class TargetSet(BaseModel):
    sets: int
    rep_low: int
    rep_high: int
    target_weight: float
    rest_seconds: int


class ProgramDay(BaseModel):
    day_name: str  # "Upper A (Mon)"
    exercises: dict[str, TargetSet]  # exercise_name -> targets


class WeeklyTargets(BaseModel):
    week_number: int
    days: list[ProgramDay]
    calories: int
    protein_g: int
    phase: str  # "cut", "reverse", "bulk"
    target_weight_lbs: float


# ---- Analysis Response Models ----

class ExerciseComparison(BaseModel):
    exercise: str
    target_weight: float
    actual_weight: Optional[float] = None
    target_reps: str
    actual_reps: Optional[list[int]] = None
    status: str  # "hit", "close", "missed", "no_data"
    volume_delta_pct: Optional[float] = None


class DailyAnalysis(BaseModel):
    date: date
    workout_adherence: Optional[list[ExerciseComparison]] = None
    nutrition: Optional[dict] = None
    recovery: Optional[dict] = None
    recommendations: list[str] = []
    overall_score: Optional[float] = None  # 0-100


# ---- Health Auto Export Payload ----

class HAEMetricDataPoint(BaseModel):
    date: str
    qty: Optional[float] = None
    value: Optional[float] = None
    source: Optional[str] = None


class HAEMetric(BaseModel):
    name: str
    units: Optional[str] = None
    data: list[HAEMetricDataPoint] = []


class HAEPayload(BaseModel):
    data: dict  # {"metrics": [...], "workouts": [...]}
