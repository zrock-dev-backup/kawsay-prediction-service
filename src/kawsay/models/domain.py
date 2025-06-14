# src/kawsay/models/domain.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import List

# --- Input Models ---

class GradeRecord(BaseModel):
    """A single grade entry for a student in a course."""
    studentId: int = Field(..., description="The unique identifier for the student.")
    courseId: int = Field(..., description="The identifier for the course.")
    finalGrade: float = Field(..., ge=0, le=100, description="The numerical grade for that course.")

class PredictionRequest(BaseModel):
    """The request body for the /bulk-predict endpoint."""
    records: List[GradeRecord] = Field(..., min_length=1)

# --- Output Models ---

class PredictedOutcome(str, Enum):
    """The possible prediction outcomes."""
    PASS = "PASS"
    FAIL = "FAIL"

class Prediction(BaseModel):
    """A single prediction result for a student."""
    studentId: int
    predictedOutcome: PredictedOutcome
    confidence: float = Field(..., ge=0.0, le=1.0)
    drivers: List[str] = Field(..., description="Human-readable reasons for the prediction.")

class PredictionResponse(BaseModel):
    """The success response body for the /bulk-predict endpoint."""
    predictions: List[Prediction]
