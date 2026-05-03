import json
import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel
from agents.coordinator import TravelPlannerCoordinator
from config import settings
 

app = FastAPI()
logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))
logger = logging.getLogger(__name__)

class TravelRequest(BaseModel):
    request_id: Optional[str] = None
    user_input: str
    previous_result: Optional[Dict[str, Any]] = None
    raw_user_input: Optional[str] = None

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/plan-trip")
def plan_trip(request: TravelRequest):
    logger.info(
        json.dumps(
            {
                "event": "plan_trip_started",
                "request_id": request.request_id,
                "has_previous_result": bool(request.previous_result),
            }
        )
    )
    coordinator = TravelPlannerCoordinator()
    result = coordinator.run(
        user_input=request.user_input,
        previous_result=request.previous_result,
        raw_user_input=request.raw_user_input,
    )
    result["request_id"] = request.request_id
    logger.info(
        json.dumps(
            {
                "event": "plan_trip_completed",
                "request_id": request.request_id,
                "status": result.get("status"),
                "response_focus": result.get("response_focus"),
            }
        )
    )
    return result
