"""学习 Embedding 的 HTTP API 与项目封装：真实服务，不使用 mock。

依赖：本地 BGE tokenizer、模型及 llama.cpp；无需数据库。
先运行：docker compose up -d embedding
运行：uv run pytest tests/learning/test_embedding_api.py -q -s
地址从根 .env 的 EMBEDDING_URL 读取；服务未启动时测试失败，不静默跳过。
"""
import json

import httpx

from config import EMBEDDING_URL
from knowledge.embedding.client import MODEL, embed


def test_embedding_request_and_result_structure():
    texts = ['上传文档后检查切分结果。', '确认发布后才能检索到文档。']
    request = {'model': MODEL, 'input': texts}
    # 模型由服务实际加载的权重决定；当前是 BGE-base，固定 768 维。
    # 这里没有可任意设置的 dimensions 参数，每条输入上限为 512 tokens。
    with httpx.Client(timeout=120) as client:
        response = client.post(f'{EMBEDDING_URL}/v1/embeddings', json=request)
        response.raise_for_status()
    payload = response.json()
    rows = payload['data']
    print('请求:', request)
    print('请求字段类型:', {key: type(value).__name__ for key, value in request.items()})
    print('HTTP 响应字段类型:', {key: type(value).__name__ for key, value in payload.items()})
    print('data 元素字段类型:', {key: type(value).__name__ for key, value in rows[0].items()})
    print('向量维度:', len(rows[0]['embedding']), '数值类型:', type(rows[0]['embedding'][0]).__name__)

    # embed(list[str]) -> list[str]：按输入顺序返回归一化向量的 JSON 字符串。
    # 封装内部最多每批 8 条；模型和地址来自模块配置，不是函数参数。
    serialized_vectors = embed(texts)
    vector = json.loads(serialized_vectors[0])
    print('embed 返回:', type(serialized_vectors).__name__, '元素类型:', type(serialized_vectors[0]).__name__)
    print('解码后:', type(vector).__name__, '数值类型:', type(vector[0]).__name__)
    print('向量数量:', len(serialized_vectors), '维度:', len(vector), '前 5 个值:', vector[:5])
