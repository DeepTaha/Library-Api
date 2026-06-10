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
