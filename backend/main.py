from fastapi import FastAPI
from pydantic import BaseModel
from agents.coordinator import TravelPlannerCoordinator
 

app = FastAPI()

class TravelRequest(BaseModel):
    user_input: str

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/plan-trip")
def plan_trip(request: TravelRequest):
    coordinator = TravelPlannerCoordinator()
    result = coordinator.run(request.user_input)
    return result