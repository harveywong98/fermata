"""重构边界回归：HTTP 合约、内部共享检索、导入副作用与草稿状态。"""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient
from rag.application import drafts, service, retrieval
from rag.contracts import KnowledgeError
from rag.contracts import SplitRequest, PublishRequest
from tools import search_knowledge
from web.app import app


def test_http_contract_unchanged():
    before = json.loads((Path(__file__).parent / 'fixtures/knowledge-openapi.json').read_text())
    after = app.openapi()
    assert after['paths'] == before['paths']
    assert after['components'] == before['components']


def test_web_and_agent_use_same_retrieval():
    row = {'document_id': 1, 'chunk_id': 2, 'parent_id': 3, 'file_name': '规则.txt',
           'matched_content': '命中正文', 'parent_content': '父' * 6100, 'score': 0.8}
    conn = MagicMock()
    conn.__enter__.return_value.execute.return_value.fetchall.side_effect = [
        [dict(row), dict(row)], [dict(row), dict(row)]]
    with patch.object(retrieval, 'db', return_value=conn), \
         patch.object(retrieval, 'embed', return_value=['[1]']), \
         patch.object(retrieval, 'profile', return_value='test-profile'), \
         patch.dict('os.environ', {'KNOWLEDGE_BASE': '电力'}):
        # 不进入 lifespan：本测试隔离数据库，不声明验证了真实服务。
        client = TestClient(app)
        response = client.post('/api/search', json={'query': '设备编号'})
        tool_result = search_knowledge.invoke({'query': '设备编号'})
    assert response.status_code == 200
    assert response.json() == tool_result['results']
    assert len(response.json()) == 1
    assert response.json()[0]['parent_truncated'] is True
    assert len(response.json()[0]['parent_content']) == 6000


def test_web_error_mapping_validation_and_page():
    client = TestClient(app)
    with patch.object(retrieval, 'search', side_effect=KnowledgeError(502, '向量服务失败')):
        response = client.post('/api/search', json={'query': '设备编号'})
    assert response.status_code == 502
    assert response.json() == {'detail': '向量服务失败'}
    with patch.object(retrieval, 'search') as search:
        assert client.post('/api/search', json={'query': ''}).status_code == 422
        search.assert_not_called()
    assert client.get('/').status_code == 200
    assert 'text/html' in client.get('/').headers['content-type']


def test_preview_remains_local_and_failure_does_not_publish(tmp_path):
    draft_id = uuid4()
    data = {'draft_id': str(draft_id), 'base_batch': None,
            'parents': [{'title': '', 'content': '设备编号需要业务上下文。' * 100,
                         'metadata': {'block_type': 'text'}}],
            'chunks': [], 'document': {'id': None, 'processing_config': {}}}
    with patch.object(drafts, 'ROOT', tmp_path), patch.object(service, 'db') as db:
        drafts.save(data)
        first = service.preview(draft_id, SplitRequest(size=128, overlap=20))
        second = service.preview(draft_id, SplitRequest(size=160, overlap=20))
        try:
            service.publish(draft_id, PublishRequest(preview_id=first['preview_id']))
        except KnowledgeError as exc:
            assert exc.status_code == 409
        else:
            raise AssertionError('旧预览必须被拒绝')
        with patch.object(service, 'embed', side_effect=KnowledgeError(502, 'offline')):
            try:
                service.publish(draft_id, PublishRequest(preview_id=second['preview_id']))
            except KnowledgeError as exc:
                assert exc.status_code == 502
            else:
                raise AssertionError('编码失败必须停止发布')
        db.assert_not_called()
        assert 'published_preview' not in drafts.load(draft_id)
