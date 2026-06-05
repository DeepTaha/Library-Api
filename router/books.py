from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services import LibraryService
from typing import Optional
import schemas

router = APIRouter(prefix="/books", tags=["Books"])

@router.post("/", response_model=schemas.BookResponse, status_code=status.HTTP_201_CREATED)
async def add_book(book_data: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    service = LibraryService(db)
    return await service.add_book(book_data)

@router.get("/", response_model=list[schemas.BookResponse])
async def list_books(
    available: Optional[bool]= None,
    author: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    
    db: AsyncSession = Depends(get_db)
    ):
    service = LibraryService(db)
    return await service.get_all_books(available, author, skip, limit)
