from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services import LibraryService
import schemas

router = APIRouter(prefix="/borrowings", tags=["Borrowings"])

@router.post("/borrow", response_model=schemas.BorrowingResponse)
async def borrow_book(request: schemas.BorrowRequest, db: AsyncSession = Depends(get_db)):
    service = LibraryService(db)
    return await service.borrow_book(request)

@router.post("/return/{borrowing_id}", response_model=schemas.BorrowingResponse)
async def return_book(borrowing_id: int, db: AsyncSession = Depends(get_db)):
    service = LibraryService(db)
    return await service.return_book(borrowing_id)
