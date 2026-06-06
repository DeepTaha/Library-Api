from exceptions import BookNotFound, BookNotAvailable, BorrowingNotFound, BorrowLimitExceeded, DuplicateActiveBorrowing
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from repository import BookRepository, BorrowingRepository
import schemas
MAX_ACTIVE_BORROWINGS_PER_USER = 3
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
    
        if not book:
            raise BookNotFound()
        if book.available_copies < 1:
            raise BookNotAvailable()
    
        # New rule 1: max 3 active borrowings per user
        active_count = await self.borrow_repo.count_active_by_user(request.user_name)
        if active_count >= MAX_ACTIVE_BORROWINGS_PER_USER:
            raise BorrowLimitExceeded()
    
        # New rule 2: no duplicate active borrowing of the same book
        existing = await self.borrow_repo.find_active_by_user_and_book(
            request.user_name, request.book_id
    )
        if existing is not None:
            raise DuplicateActiveBorrowing()
    
    # All rules passed — do the work
        book.available_copies -= 1
        borrowing = await self.borrow_repo.create(request.book_id, request.user_name)
    
        await self.db.commit()
        await self.db.refresh(borrowing)
        return borrowing