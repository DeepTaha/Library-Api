from datetime import datetime
from pydantic import BaseModel


class FineResponse(BaseModel):
    id: int
    borrowing_id: int
    user_id: int
    days_overdue: int
    amount: int
    status: str
    created_at: datetime
    paid_at: datetime | None

    class Config:
        from_attributes = True


class FineWaiveRequest(BaseModel):
    reason: str
