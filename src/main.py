import logging
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .models.domain import PredictionRequest, PredictionResponse # <- FIX
from .services.prediction_service import PredictionService      # <- FIX
from .infrastructure.onnx_model import StudentOutcomePredictor  # <- FIX

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kawsay Prediction Service",
    description="Provides student outcome predictions based on grade data.",
    version="1.0.0",
)

try:
    MODEL_PATH = Path("student_pass_predictor.onnx")
    predictor = StudentOutcomePredictor(model_path=MODEL_PATH)
    prediction_service = PredictionService(predictor=predictor)
except (FileNotFoundError, RuntimeError) as e:
    logger.critical(f"CRITICAL: Could not load the model. Service cannot start. Error: {e}")
    predictor = None
    prediction_service = None

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
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
    is_model_loaded = predictor is not None
    return {
        "status": "ok" if is_model_loaded else "degraded",
        "services": {
            "model": "loaded" if is_model_loaded else "unavailable"
        }
    }
