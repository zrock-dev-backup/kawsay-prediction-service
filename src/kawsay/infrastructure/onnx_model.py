# src/kawsay/infrastructure/onnx_model.py
import numpy as np
import onnxruntime as ort
from pathlib import Path
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class StudentOutcomePredictor:
    """A wrapper for the ONNX student pass/fail prediction model."""

    def __init__(self, model_path: Path):
        # ... (init code remains the same) ...
        try:
            self.session = ort.InferenceSession(str(model_path))
            self.input_names = [inp.name for inp in self.session.get_inputs()]
            self.output_names = [out.name for out in self.session.get_outputs()]
            logger.info(f"ONNX model loaded. Input names: {self.input_names}")
        except Exception as e:
            logger.exception("Failed to load ONNX model.")
            raise RuntimeError("Could not initialize ONNX model session.") from e

    def predict(self, model_inputs: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Runs batch prediction on the provided dictionary of feature columns.

        Args:
            model_inputs: A dictionary where keys are model input names and
                          values are numpy arrays of shape (n_records, 1).

        Returns:
            A tuple of numpy arrays: (labels, probabilities).
        """
        try:
            # Ensure all inputs are float32, as required by the ONNX graph
            prepared_inputs = {
                name: arr.astype(np.float32) for name, arr in model_inputs.items()
            }
            result = self.session.run(self.output_names, prepared_inputs)
            return result
        except Exception as e:
            logger.exception(f"Error during model inference.")
            raise
