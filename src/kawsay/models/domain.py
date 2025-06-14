# src/kawsay/models/domain.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import List

# --- Input Models (BREAKING CHANGE) ---

class GradeRecord(BaseModel):
    """A single grade entry for a student in a course for a specific semester."""
    studentId: int = Field(..., description="The unique identifier for the student. Used for tracking, not by the model.")
    courseId: int = Field(..., description="The identifier for the course. Must be one of the values the model was trained on.")
    semester: int = Field(..., description="The semester identifier. Must be one of the values the model was trained on.")
    grade_lab: float = Field(..., ge=0, le=100, description="The grade for the lab component.")
    grade_masterclass: float = Field(..., ge=0, le=100, description="The grade for the masterclass component.")

class PredictionRequest(BaseModel):
    """The request body for the /bulk-predict endpoint."""
    records: List[GradeRecord] = Field(..., min_length=1)

# --- Output Models (UPDATED) ---

class PredictedOutcome(str, Enum):
    """The possible prediction outcomes."""
    PASS = "PASS"
    FAIL = "FAIL"

class Prediction(BaseModel):
    """A single prediction result for a student's course record."""
    studentId: int
    courseId: int
    semester: int
    predictedOutcome: PredictedOutcome
    confidence: float = Field(..., ge=0.0, le=1.0)
    drivers: List[str] = Field(..., description="Human-readable reasons for the prediction.")

class PredictionResponse(BaseModel):
    """The success response body for the /bulk-predict endpoint."""
    predictions: List[Prediction]
