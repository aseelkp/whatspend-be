from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class SpendingSummary(BaseModel):
    total_amount: float
    transaction_count: int
    period_start: datetime
    period_end: datetime

class CategorySpending(BaseModel):
    category_name: str
    total_amount: float
    transaction_count: int

class MonthlyAnalytics(BaseModel):
    month: str
    year: int
    spending_summary: SpendingSummary
    category_breakdown: List[CategorySpending]
    
class AnalyticsResponse(BaseModel):
    user_id: int
    analytics: MonthlyAnalytics