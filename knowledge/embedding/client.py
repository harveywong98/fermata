"""BGE 编码与索引版本；仅在实际使用时读取模型文件。"""
from functools import lru_cache
from hashlib import sha256
import json
import math
import httpx
from config import EMBEDDING_URL, MODEL_DIR
from knowledge.embedding.tokenizer import tokens
from knowledge.contracts import KnowledgeError

MODEL = 'BAAI/bge-base-zh-v1.5'

@lru_cache
def profile():
    return 'bge-base:' + sha256((MODEL_DIR / 'bge-base-zh-v1.5-f16.gguf').read_bytes()).hexdigest()[:16] + ':cls:context-v1'

def embed(texts):
    if any(tokens(t) > 512 for t in texts):
        raise KnowledgeError(400, '输入超过512 tokens，请缩短问题或重新切块')
    vectors = []
    try:
        with httpx.Client(timeout=120) as client:
            for start in range(0, len(texts), 8):
                part = texts[start:start + 8]
                response = client.post(EMBEDDING_URL + '/v1/embeddings', json={'input': part, 'model': MODEL})
                response.raise_for_status()
                rows = sorted(response.json()['data'], key=lambda row: row['index'])
                if [r['index'] for r in rows] != list(range(len(part))):
                    raise ValueError('向量返回数量或顺序异常')
                for row in rows:
                    v = row['embedding']
                    if len(v) != 768 or not all(math.isfinite(x) for x in v):
                        raise ValueError('需要有效的768维BGE-base向量')
                    norm = math.sqrt(sum(x*x for x in v))
                    if not norm:
                        raise ValueError('收到零向量')
                    vectors.append(json.dumps([x/norm for x in v]))
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise KnowledgeError(502, '向量服务失败：' + str(exc)) from exc
    return vectors
