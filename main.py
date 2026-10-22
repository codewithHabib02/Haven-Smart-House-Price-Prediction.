import json
import math
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

MODEL_PATH = Path(os.getenv("MODEL_PATH", str(BASE_DIR / "house.pkl"))).expanduser()
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "predictions.db"))).expanduser()

# These names and their order were inspected from the supplied trained pipeline.
FEATURES = [
    "OverallQual",
    "YearBuilt",
    "YearRemodAdd",
    "GrLivArea",
    "TotalBsmtSF",
    "GarageCars",
    "FullBath",
    "TotRmsAbvGrd",
]

class HouseFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    OverallQual: int = Field(ge=1, le=10)
    YearBuilt: int = Field(ge=1800, le=2035)
    YearRemodAdd: int = Field(ge=1800, le=2035)
    GrLivArea: float = Field(gt=0, le=20000)
    TotalBsmtSF: float = Field(ge=0, le=10000)
    GarageCars: int = Field(ge=0, le=10)
    FullBath: int = Field(ge=0, le=10)
    TotRmsAbvGrd: int = Field(ge=1, le=30)

    def validate_years(self) -> None:
        if self.YearRemodAdd < self.YearBuilt:
            raise ValueError("YearRemodAdd cannot be earlier than YearBuilt.")

class PredictionResponse(BaseModel):
    id: int
    predicted_price: float
    input_features: dict[str, Any]
    created_at: str

model = None
model_error = None

def database_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DATABASE_PATH), timeout=15)
    connection.row_factory = sqlite3.Row
    return connection

def initialize_database() -> None:
    with database_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_features TEXT NOT NULL,
                predicted_price REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at)"
        )

def load_model() -> None:
    global model, model_error
    model = None
    model_error = None
    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
        loaded = joblib.load(MODEL_PATH)
        if not hasattr(loaded, "predict"):
            raise TypeError("The saved object does not expose a predict() method.")
        model = loaded
    except Exception as exc:
        model_error = f"{type(exc).__name__}: {exc}"
        # Keep the service available for health diagnostics, but never fake a prediction.

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    load_model()
    yield

app = FastAPI(
    title="Haven House Price Prediction API",
    description="API for the existing trained house-price prediction pipeline.",
    version="1.0.0",
    lifespan=lifespan,
)

configured_origins = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5173,http://127.0.0.1:5173,https://haven-smart-house-price-prediction.mhabibulie02.workers.dev",
)
origins = [origin.strip().rstrip("/") for origin in configured_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

@app.get("/")
def root():
    return {
        "service": "Haven House Price Prediction API",
        "status": "running",
        "docs": "/docs",
    }

@app.get("/health")
def health():
    return {
        "status": "ok" if model is not None else "degraded",
        "model_loaded": model is not None,
        "database_configured": True,
        "model_error": model_error if model is None else None,
    }

@app.post("/predict", response_model=PredictionResponse)
def predict(features: HouseFeatures):
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="The trained model is not available. Check the backend logs and model file.",
        )

    data = features.model_dump()
    if data["YearRemodAdd"] < data["YearBuilt"]:
        raise HTTPException(
            status_code=422,
            detail="YearRemodAdd cannot be earlier than YearBuilt.",
        )

    try:
        # Pass a DataFrame with the exact feature names and order used during training.
        frame = pd.DataFrame([[data[name] for name in FEATURES]], columns=FEATURES)
        raw_prediction = model.predict(frame)
        predicted_price = float(raw_prediction[0])
        if not math.isfinite(predicted_price):
            raise ValueError("The model returned a non-finite prediction.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Check that the backend dependencies match the saved model.",
        )

    created_at = datetime.now(timezone.utc).isoformat()
    try:
        with database_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO predictions (input_features, predicted_price, created_at) VALUES (?, ?, ?)",
                (json.dumps(data, separators=(",", ":")), predicted_price, created_at),
            )
            record_id = cursor.lastrowid
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="The prediction was calculated, but it could not be saved to the database.",
        )

    return PredictionResponse(
        id=record_id,
        predicted_price=predicted_price,
        input_features=data,
        created_at=created_at,
    )

@app.get("/predictions")
def list_predictions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        with database_connection() as connection:
            total = connection.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
            rows = connection.execute(
                "SELECT id, input_features, predicted_price, created_at "
                "FROM predictions ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Could not read prediction history.")

    items = [
        {
            "id": row["id"],
            "input_features": json.loads(row["input_features"]),
            "predicted_price": row["predicted_price"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@app.get("/predictions/{prediction_id}")
def get_prediction(prediction_id: int):
    try:
        with database_connection() as connection:
            row = connection.execute(
                "SELECT id, input_features, predicted_price, created_at FROM predictions WHERE id = ?",
                (prediction_id,),
            ).fetchone()
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Could not read the requested prediction.")

    if row is None:
        raise HTTPException(status_code=404, detail="Prediction record not found.")

    return {
        "id": row["id"],
        "input_features": json.loads(row["input_features"]),
        "predicted_price": row["predicted_price"],
        "created_at": row["created_at"],
    }
