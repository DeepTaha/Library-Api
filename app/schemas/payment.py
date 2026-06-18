from datetime import datetime
from pydantic import BaseModel, Field


class PaymentInitiateRequest(BaseModel):
    fine_id: int


class PaymentInitiateResponse(BaseModel):
    payment_id: int
    order_id: str
    checkout_url: str   # full Safepay URL the frontend redirects Ahmed to


class PaymentStatusResponse(BaseModel):
    payment_id: int = Field(alias="id")
    fine_id: int
    amount: int
    status: str
    safepay_tracker: str | None
    completed_at: datetime | None

    model_config = {"from_attributes": True, "populate_by_name": True}
