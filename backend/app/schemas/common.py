from pydantic import BaseModel
from typing import Optional, Any, Dict

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    ai_backend: str
    device: str
    storage_backend: str

class ErrorDetail(BaseModel):
    code: str
    message: str
    path: Optional[str] = None
    details: Optional[Any] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail

