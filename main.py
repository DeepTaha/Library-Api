from fastapi import FastAPI
from database import engine, Base
from router import books, borrowings
from exceptions import BookNotFound, BookNotAvailable, BorrowingNotFound

app = FastAPI(title="Library System Architecture")

# 1. App starts & creates database tables
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 2. Register routers
app.include_router(books.router)
app.include_router(borrowings.router)

@app.exception_handler(BookNotFound)
async def handle_book_not_found(request: Request, exc: BookNotFound):
    return JSONResponse(status_code=404, content={"detail": "Book not found"})

@app.exception_handler(BorrowingNotFound)
async def handle_borrowing_not_found(request: Request, exc: BorrowingNotFound):
    return JSONResponse(status_code=404, content={"detail": "Borrowing record not found"})

@app.exception_handler(BookNotAvailable)
async def handle_book_not_available(request: Request, exc: BookNotAvailable):
    return JSONResponse(status_code=400, content={"detail": "No copies available"})