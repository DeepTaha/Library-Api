from pydantic import BaseModel


class TopBook(BaseModel):
    book_id: int
    title: str
    author: str
    borrow_count: int


class AnalyticsSummaryResponse(BaseModel):
    borrowed_this_month: int
    borrowed_last_month: int
    readers_with_overdue: int
    avg_days_kept: float | None
    top_5_books: list[TopBook]
