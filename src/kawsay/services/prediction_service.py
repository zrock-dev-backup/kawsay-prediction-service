# src/kawsay/services/prediction_service.py
import pandas as pd
import numpy as np
from typing import List, Dict, Any

from kawsay.models.domain import (
    PredictionRequest,
    PredictionResponse,
    Prediction,
    PredictedOutcome,
    GradeRecord,
)
from kawsay.infrastructure.onnx_model import StudentOutcomePredictor

class PredictionService:
    """Orchestrates the prediction workflow."""

    def __init__(self, predictor: StudentOutcomePredictor):
        self.predictor = predictor

    def generate_predictions(self, request: PredictionRequest) -> PredictionResponse:
        """
        Processes a prediction request to generate outcomes for each record.
        1. Prepares raw records into numpy arrays for the model.
        2. Runs the inputs through the model.
        3. Generates human-readable drivers for each prediction.
        4. Assembles the final response object.
        """
        # 1. Prepare model inputs
        model_inputs = self._prepare_model_inputs(request.records)
        
        # 2. Model Prediction
        labels, probabilities = self.predictor.predict(model_inputs)

        # 3. Driver Generation & Response Assembly
        predictions: List[Prediction] = []
        for i, record in enumerate(request.records):
            outcome = PredictedOutcome.PASS if labels[i] == 1 else PredictedOutcome.FAIL
            confidence = float(probabilities[i][int(labels[i])])

            drivers = self._generate_drivers(outcome, record)

            predictions.append(
                Prediction(
                    studentId=record.studentId,
                    courseId=record.courseId,
                    semester=record.semester,
                    predictedOutcome=outcome,
                    confidence=confidence,
                    drivers=drivers,
                )
            )

        return PredictionResponse(predictions=predictions)

    def _prepare_model_inputs(self, records: List[GradeRecord]) -> Dict[str, np.ndarray]:
        """Transforms a list of Pydantic models into a dictionary of numpy arrays."""
        df = pd.DataFrame([r.model_dump() for r in records])
        
        # The keys MUST match the model's input names from the graph
        input_dict = {
            'courseId': df[['courseId']].to_numpy(),
            'semester': df[['semester']].to_numpy(),
            'grade_lab': df[['grade_lab']].to_numpy(),
            'grade_masterclass': df[['grade_masterclass']].to_numpy(),
        }
        return input_dict

    def _generate_drivers(self, outcome: PredictedOutcome, record: GradeRecord) -> List[str]:
        """Generates human-readable explanations based on the record's data."""
        drivers = []
        avg_grade = (record.grade_lab + record.grade_masterclass) / 2

        if outcome == PredictedOutcome.PASS:
            drivers.append(f"Strong overall grade ({avg_grade:.1f})")
            if record.grade_lab > 85 and record.grade_masterclass > 85:
                drivers.append("Excellent performance in both lab and masterclass.")
        else: # FAIL
            drivers.append(f"Low overall grade ({avg_grade:.1f})")
            if record.grade_lab < 70:
                drivers.append(f"Lab grade ({record.grade_lab:.1f}) is below passing threshold.")
            if record.grade_masterclass < 70:
                drivers.append(f"Masterclass grade ({record.grade_masterclass:.1f}) is below passing threshold.")
        
        return drivers
