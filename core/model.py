from pydantic import BaseModel, Field


class CalculationRequest(BaseModel):
    lower_bound: int = Field(..., ge=1, description="Lower bound (i) must be >= 1")
    upper_bound: int = Field(..., description="Upper bound (j)")
    processing_mode: str = Field(..., regex="^(sequential|threading|multiprocessing)$")