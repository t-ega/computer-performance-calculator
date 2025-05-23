from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class PerformanceMetrics:
    timestamp: str
    lower_bound: int
    upper_bound: int
    processing_mode: str
    execution_time: float
    cpu_time: float
    memory_usage: float
    cpu_utilization: float
    result_value: float
    cores_used: int = 1


class CalculationResponse(BaseModel):
    metrics: dict
    success: bool
    message: str
