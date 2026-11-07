"""HTTP 适配层；知识业务逻辑位于 knowledge 包。"""
from uuid import UUID
from fastapi import APIRouter, File, Form, UploadFile
from knowledge.application import service, retrieval
from knowledge.contracts import SplitRequest, PublishRequest, SearchRequest

router = APIRouter()

@router.get('/api/documents')
def documents():
    return service.documents()


@router.post('/api/documents')
def upload(file: UploadFile=File(...), knowledge_base: str=Form('电力')):
    return service.upload(file, knowledge_base)


@router.get('/api/documents/{id}')
def detail(id: int):
    return service.detail(id)


@router.post('/api/documents/{id}/draft')
def edit_document(id: int):
    return service.edit_document(id)


@router.get('/api/drafts')
def list_drafts():
    return service.list_drafts()


@router.get('/api/drafts/{id}')
def get_draft(id: UUID):
    return service.get_draft(id)


@router.post('/api/drafts/{id}/preview')
def preview(id: UUID, request: SplitRequest):
    return service.preview(id, request)


@router.delete('/api/drafts/{id}/chunks/{chunk_id}')
def delete_chunk(id: UUID, chunk_id: int, preview_id: UUID):
    return service.delete_chunk(id, chunk_id, preview_id)


@router.delete('/api/drafts/{id}')
def discard(id: UUID):
    return service.discard(id)


@router.post('/api/drafts/{id}/publish')
def publish(id: UUID, request: PublishRequest):
    return service.publish(id, request)


@router.post('/api/search')
def search(request: SearchRequest):
    return retrieval.search(request)


@router.delete('/api/documents/{id}')
def delete(id: int):
    return service.delete(id)


