from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(description="Total number of items matching query")
    page: int = Field(description="Current page number (1-based)")
    page_size: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")


class MessageResponse(BaseModel):
    message: str
    detail: str | None = None
