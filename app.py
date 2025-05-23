from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import psutil
import os
from dataclasses import asdict
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from core.db import get_db, PerformanceResult, init_db
from core.performance_calculator import PerformanceCalculator
from core.model import CalculationRequest
from core.utils import CalculationResponse

PORT = int(os.environ.get("PORT", 8080))

@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Starting lifespan")
    init_db()
    yield


app = FastAPI(title="Performance Comparison API", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/calculate", response_model=CalculationResponse)
async def calculate_performance(request: CalculationRequest, db: Session = Depends(get_db)):
    if request.upper_bound <= request.lower_bound:
        raise HTTPException(status_code=400, detail="Upper bound must be greater than lower bound")

    if request.upper_bound - request.lower_bound > 10_000_000:
        raise HTTPException(status_code=400, detail="Range too large. Maximum range is 10 million")

    try:
        calculator = PerformanceCalculator()

        if request.processing_mode == "sequential":
            metrics = calculator.calculate_sequential(request.lower_bound, request.upper_bound)
        elif request.processing_mode == "threading":
            metrics = calculator.calculate_threading(request.lower_bound, request.upper_bound)
        elif request.processing_mode == "multiprocessing":
            metrics = calculator.calculate_multiprocessing(request.lower_bound, request.upper_bound)
        else:
            raise HTTPException(status_code=400, detail="Invalid processing mode")

        db_result = PerformanceResult(
            timestamp=metrics.timestamp,
            lower_bound=metrics.lower_bound,
            upper_bound=metrics.upper_bound,
            processing_mode=metrics.processing_mode,
            execution_time=metrics.execution_time,
            cpu_time=metrics.cpu_time,
            memory_usage=metrics.memory_usage,
            cpu_utilization=metrics.cpu_utilization,
            result_value=metrics.result_value,
            cores_used=metrics.cores_used
        )

        db.add(db_result)
        db.commit()
        db.refresh(db_result)

        return CalculationResponse(
            metrics=asdict(metrics),
            success=True,
            message="Calculation completed successfully"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@app.get("/api/results")
async def get_historical_results(
        limit: Optional[int] = 100,
        offset: Optional[int] = 0,
        processing_mode: Optional[str] = None,
        db: Session = Depends(get_db)
):
    query = db.query(PerformanceResult)

    # Apply filter if processing_mode is specified
    if processing_mode:
        query = query.filter(PerformanceResult.processing_mode == processing_mode)

    # Get total count
    total_count = query.count()

    # Apply pagination and ordering
    results = query.order_by(PerformanceResult.id.desc()).offset(offset).limit(limit).all()

    # Convert to dict format
    results_data = [
        {
            "id": result.id,
            "timestamp": result.timestamp,
            "lower_bound": result.lower_bound,
            "upper_bound": result.upper_bound,
            "processing_mode": result.processing_mode,
            "execution_time": result.execution_time,
            "cpu_time": result.cpu_time,
            "memory_usage": result.memory_usage,
            "cpu_utilization": result.cpu_utilization,
            "result_value": result.result_value,
            "cores_used": result.cores_used
        }
        for result in results
    ]

    return {
        "results": results_data,
        "total_count": total_count,
        "offset": offset,
        "limit": limit,
        "filter": {"processing_mode": processing_mode} if processing_mode else None
    }


@app.get("/api/system-info")
async def get_system_info():
    return {
        "cpu_count": os.cpu_count(),
        "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
        "memory": {
            "total": psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
            "available": psutil.virtual_memory().available / 1024 / 1024 / 1024,  # GB
        },
        "platform": {
            "platform": os.name
        }
    }


@app.get("/", response_class=HTMLResponse)
async def get_home():
    with open("static/index.html") as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
        log_level="info"
    )
