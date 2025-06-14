# src/main.py
import logging
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from kawsay.models.domain import PredictionRequest, PredictionResponse
from kawsay.services.prediction_service import PredictionService
from kawsay.infrastructure.onnx_model import StudentOutcomePredictor

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Application Setup ---
app = FastAPI(
    title="Kawsay Prediction Service",
    description="Provides student outcome predictions based on grade data.",
    version="1.0.0",
)

# --- Global Resources (Load Once at Startup) ---
# This is a lean way to handle resource loading in a microservice.
# For more complex apps, dependency injection frameworks could be used.
try:
    MODEL_PATH = Path("student_pass_predictor.onnx")
    predictor = StudentOutcomePredictor(model_path=MODEL_PATH)
    prediction_service = PredictionService(predictor=predictor)
except (FileNotFoundError, RuntimeError) as e:
    logger.critical(f"CRITICAL: Could not load the model. Service cannot start. Error: {e}")
    # In a real system, this would prevent the service from reporting as "healthy"
    predictor = None
    prediction_service = None

# --- Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Customizing FastAPI's default 422 error for the format in api-design.md
    details = []
    for error in exc.errors():
        field = ".".join(map(str, error["loc"][1:])) # "body.records.0.finalGrade" -> "records.0.finalGrade"
        details.append({"field": field, "issue": error["msg"]})
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed.",
                "details": details,
            }
        },
    )

# --- API Endpoints ---
@app.post("/bulk-predict", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
async def bulk_predict(request: PredictionRequest):
    """
    Accepts a list of student grade records and returns pass/fail predictions.
    """
    if not prediction_service:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": {"code": "MODEL_NOT_LOADED", "message": "Prediction model is not available."}}
        )
    
    logger.info(f"Received prediction request for {len(request.records)} records.")
    response = prediction_service.generate_predictions(request)
    logger.info(f"Successfully generated {len(response.predictions)} predictions.")
    return response

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for monitoring."""
    is_model_loaded = predictor is not None
    return {
        "status": "ok" if is_model_loaded else "degraded",
        "services": {
            "model": "loaded" if is_model_loaded else "unavailable"
        }
    }
