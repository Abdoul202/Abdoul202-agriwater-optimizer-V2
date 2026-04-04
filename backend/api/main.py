"""
AgriWater Dashboard - FastAPI Backend.

Exposes the MILP optimizer, weather, and config as REST endpoints.
Run with: uvicorn api.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import config, optimize, weather

app = FastAPI(
    title="AgriWater API",
    description="Optimisation energetique pour l'irrigation agricole au Sahel",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(optimize.router)
app.include_router(weather.router)
app.include_router(config.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.2.0"}
