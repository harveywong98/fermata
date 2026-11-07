"""知识模块共享的请求模型与业务异常。"""
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


class KnowledgeError(Exception):
    """知识模块错误；由工具和 Web 各自转换为对外响应。"""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
