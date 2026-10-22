from fastapi import FastAPI

app = FastAPI(
    title="Appointment Scheduling API",
    description="An API for scheduling appointments with service providers.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}