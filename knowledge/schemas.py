from uuid import UUID
from pydantic import BaseModel, Field


class SplitRequest(BaseModel):
    size: int = Field(400, ge=128, le=480)
    overlap: int = Field(40, ge=0, le=80)


class PublishRequest(BaseModel):
    preview_id: UUID


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    knowledge_base: str = '电力'
    top_k: int = Field(5, ge=1, le=20)
