from datetime import datetime
from pydantic import BaseModel


class BorrowRequest(BaseModel):
    book_id: int
    


class BorrowingResponse(BaseModel):
    id: int
    book_id: int
    user_id:int
    borrowed_at: datetime | None
    returned_at: datetime | None

    class ConfigDict:
        from_attributes = True
