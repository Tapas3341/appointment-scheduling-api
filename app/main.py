from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.routers.auth import router as auth_router

app = FastAPI(
    title="Appointment Scheduling API",
    description="An API for scheduling appointments with service providers.",
    version="0.1.0",
)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}