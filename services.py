from exceptions import BookNotFound, BookNotAvailable, BorrowingNotFound
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from repository import BookRepository, BorrowingRepository
import schemas

class LibraryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.book_repo = BookRepository(db)
        self.borrow_repo = BorrowingRepository(db)

    async def add_book(self, book_data: schemas.BookCreate):
        book = await self.book_repo.create(book_data.model_dump())
        await self.db.commit()
        await self.db.refresh(book)
        return book

    async def get_all_books(self, available,author, skip: int, limit: int):
        return await self.book_repo.list_all(available, author, skip, limit)

    async def borrow_book(self, request: schemas.BorrowRequest):
        book = await self.book_repo.get_by_id_locked(request.book_id)
        
        # Business logic validation
        if not book:
            raise BookNotFound()
        if book.available_copies < 1:
            raise BookNotAvailable()

        # Mutate models
        book.available_copies -= 1
        borrowing = await self.borrow_repo.create(request.book_id, request.user_name)
        
        await self.db.commit()
        await self.db.refresh(borrowing)
        return borrowing

    async def return_book(self, borrowing_id: int):
        borrowing = await self.borrow_repo.get_by_id(borrowing_id)
        # print(f"borrowing: id={borrowing.id}, book_id={borrowing.book_id}, user_name={borrowing.user_name}, borrowed_at={borrowing.borrowed_at}, returned_at={borrowing.returned_at}")
        # Business logic validation
        if not borrowing:
            raise BorrowingNotFound
        if borrowing.returned_at is not None:
            raise BookNotAvailable
        # Mutate models
        borrowing.returned_at = datetime.utcnow()
        book = await self.book_repo.get_by_id(borrowing.book_id)
        if book:
            book.available_copies += 1

        await self.db.commit()
        await self.db.refresh(borrowing)
        return borrowing
