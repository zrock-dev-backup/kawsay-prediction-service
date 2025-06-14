# src/kawsay/services/prediction_service.py
import pandas as pd
import numpy as np
from typing import List, Dict, Any

from kawsay.models.domain import (
    PredictionRequest,
    PredictionResponse,
    Prediction,
    PredictedOutcome,
)
from kawsay.infrastructure.onnx_model import StudentOutcomePredictor

class PredictionService:
    """Orchestrates the prediction workflow."""

    def __init__(self, predictor: StudentOutcomePredictor):
        self.predictor = predictor
        self.PASSING_THRESHOLD = 70.0 # Domain knowledge: grade required to pass a course

    def generate_predictions(self, request: PredictionRequest) -> PredictionResponse:
        """
        Processes a prediction request to generate outcomes for each student.
        1. Performs feature engineering from raw grade records.
        2. Runs the engineered features through the model.
        3. Generates human-readable drivers for each prediction.
        4. Assembles the final response object.
        """
        # 1. Feature Engineering
        features_df, student_ids = self._engineer_features(request)
        
        # 2. Model Prediction
        # The model expects a numpy array, not a DataFrame
        feature_array = features_df.to_numpy()
        labels, probabilities = self.predictor.predict(feature_array)

        # 3. Driver Generation & Response Assembly
        predictions: List[Prediction] = []
        for i, student_id in enumerate(student_ids):
            outcome = PredictedOutcome.PASS if labels[i] == 1 else PredictedOutcome.FAIL
            confidence = float(probabilities[i][int(labels[i])]) # Probability of the predicted class
            
            # Get the raw features for this student to generate drivers
            student_features = features_df.iloc[i].to_dict()

            drivers = self._generate_drivers(outcome, student_features)

            predictions.append(
                Prediction(
                    studentId=student_id,
                    predictedOutcome=outcome,
                    confidence=confidence,
                    drivers=drivers,
                )
            )

        return PredictionResponse(predictions=predictions)

    def _engineer_features(self, request: PredictionRequest) -> tuple[pd.DataFrame, list]:
        """
        Transforms raw grade records into a feature matrix for the model.
        This is the most critical pre-processing step.
        """
        df = pd.DataFrame([r.model_dump() for r in request.records])
        
        # Aggregate data per student
        student_agg = df.groupby('studentId').agg(
            avg_grade=('finalGrade', 'mean'),
            course_count=('courseId', 'count'),
            min_grade=('finalGrade', 'min'),
            failing_courses_count=('finalGrade', lambda x: (x < self.PASSING_THRESHOLD).sum())
        ).reset_index()

        # The order of columns MUST match the model's training order.
        # Let's assume the model was trained on: [avg_grade, failing_courses_count]
        feature_columns = ['avg_grade', 'failing_courses_count']
        features_df = student_agg[feature_columns]
        
        # Keep track of the student IDs in the correct order
        student_ids = student_agg['studentId'].tolist()

        return features_df, student_ids

    def _generate_drivers(self, outcome: PredictedOutcome, features: Dict[str, Any]) -> List[str]:
        """
        Generates human-readable explanations for a prediction based on simple rules.
        This simulates a real-world explainability (XAI) feature.
        """
        drivers = []
        avg_grade = features.get('avg_grade', 0)
        failing_courses = features.get('failing_courses_count', 0)

        if outcome == PredictedOutcome.PASS:
            drivers.append(f"High average grade ({avg_grade:.1f})")
            if failing_courses == 0:
                drivers.append("No failing grades detected")
        else: # FAIL
            drivers.append(f"Low average grade ({avg_grade:.1f})")
            if failing_courses > 0:
                drivers.append(f"{int(failing_courses)} course(s) below passing threshold")
        
        return drivers
