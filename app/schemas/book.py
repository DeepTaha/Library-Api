from pydantic import BaseModel, Field, model_validator


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    total_copies: int = Field(..., ge=0, le=10000)
    available_copies: int = Field(..., ge=0, le=10000)
    genre: str | None = Field(None, max_length=100)
    is_age_restricted: bool = False

    @model_validator(mode="after")
    def available_cannot_exceed_total(self):
        if self.available_copies > self.total_copies:
            raise ValueError("available_copies cannot exceed total_copies")
        return self


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    author: str | None = Field(None, min_length=1, max_length=255)
    total_copies: int | None = Field(None, ge=0, le=10000)
    available_copies: int | None = Field(None, ge=0, le=10000)
    genre: str | None = Field(None, max_length=100)
    is_age_restricted: bool | None = None

    @model_validator(mode="after")
    def available_cannot_exceed_total(self):
        if self.total_copies is not None and self.available_copies is not None:
            if self.available_copies > self.total_copies:
                raise ValueError("available_copies cannot exceed total_copies")
        return self


class BookResponse(BookBase):
    id: int

    class Config:
        from_attributes = True
