from datetime import datetime
from pydantic import BaseModel, Field

class BookBase(BaseModel):
    title: str
    author: str
    total_copies: int = Field(..., ge=0)
    available_copies: int = Field(..., ge=0)

class BookCreate(BookBase):
    pass

class BookResponse(BookBase):
    id: int
    class ConfigDict:
        from_attributes = True

class BorrowRequest(BaseModel):
    book_id: int
    user_name: str

class BorrowingResponse(BaseModel):
    id: int
    book_id: int
    user_name: str
    borrowed_at: datetime | None
    returned_at: datetime | None
    class ConfigDict:
        from_attributes = True
