from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class BorrowRequest(BaseModel):
    book_id: int


class ExtendRequest(BaseModel):
    days: int = Field(..., ge=1, le=30)


class BorrowingResponse(BaseModel):
    id: int
    book_id: int
    user_id: int
    borrowed_at: datetime | None
    due_date: datetime | None
    returned_at: datetime | None
    fine: FineResponse | None = None  # populated if book was returned late

    class Config:
        from_attributes = True


# Imported after BorrowingResponse to avoid circular import
from app.schemas.fine import FineResponse  # noqa: E402
BorrowingResponse.model_rebuild()


class BulkReturnRequest(BaseModel):
    borrowing_ids: list[int] = Field(..., min_length=1, max_length=100)
    reader_id: int | None = None  # if set, IDs not belonging to this reader fail


class BulkReturnFailure(BaseModel):
    borrowing_id: int
    reason: str  # "not_found" | "already_returned" | "wrong_reader" | "duplicate_in_request"


class BulkReturnResponse(BaseModel):
    succeeded: list[BorrowingResponse]
    failed: list[BulkReturnFailure]
    success_count: int
    failure_count: int
