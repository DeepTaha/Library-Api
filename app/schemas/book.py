from pydantic import BaseModel, Field


class BookBase(BaseModel):
    title: str
    author: str
    total_copies: int = Field(..., ge=0)
    available_copies: int = Field(..., ge=0)
    genre: str | None = None
    is_age_restricted: bool = False


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    total_copies: int | None = Field(None, ge=0)
    available_copies: int | None = Field(None, ge=0)
    genre: str | None = None
    is_age_restricted: bool | None = None


class BookResponse(BookBase):
    id: int

    class Config:
        from_attributes = True
