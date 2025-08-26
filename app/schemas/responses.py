import uuid

from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime

class ErrorDetail(BaseModel):
    field : Optional[str] = None
    code : str
    message : str

class PaginationInfo(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int

class StandardResponse(BaseModel):
    success: bool
    message : str
    data : Optional[Any] = None
    errors : Optional[list[ErrorDetail]] = None
    pagination : Optional[PaginationInfo] = None

    class Config:
        arbitrary_types_allowed = True