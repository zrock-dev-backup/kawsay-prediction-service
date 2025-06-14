# src/kawsay/infrastructure/onnx_model.py
import numpy as np
import onnxruntime as ort
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class StudentOutcomePredictor:
    """A wrapper for the ONNX student pass/fail prediction model."""

    def __init__(self, model_path: Path):
        if not model_path.exists():
            logger.error(f"Model file not found at path: {model_path}")
            raise FileNotFoundError(f"Model file not found: {model_path}")

        try:
            # Create an inference session for the model
            self.session = ort.InferenceSession(str(model_path))
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            logger.info(f"ONNX model loaded successfully from {model_path}")
            logger.info(f"Model Input Name: {self.input_name}")
            logger.info(f"Model Output Names: {self.output_names}")
        except Exception as e:
            logger.exception("Failed to load ONNX model.")
            raise RuntimeError("Could not initialize ONNX model session.") from e

    def predict(self, features: np.ndarray) -> np.ndarray:
        """
        Runs batch prediction on the provided feature vectors.

        Args:
            features: A numpy array of shape (n_students, n_features).

        Returns:
            A tuple of numpy arrays: (labels, probabilities).
        """
        if features.ndim == 1: # Handle single prediction case
            features = features.reshape(1, -1)
        
        if features.dtype != np.float32:
            features = features.astype(np.float32)

        try:
            # The model is expected to return two outputs: label and probability
            result = self.session.run(self.output_names, {self.input_name: features})
            return result
        except Exception as e:
            logger.exception(f"Error during model inference for input shape {features.shape}")
            raise
