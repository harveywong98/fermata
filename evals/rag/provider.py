"""promptfoo Python provider：调用真实检索，不生成答案或改写知识库。"""
from pathlib import Path
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from knowledge.application.retrieval import search
from knowledge.contracts import SearchRequest
from knowledge.embedding.client import MODEL, profile


def call_api(prompt, options, context):
    config = options['config']
    request = SearchRequest(query=prompt, knowledge_base=config['knowledge_base'], top_k=config['top_k'])
    start = perf_counter()
    hits = search(request)  # 失败让 promptfoo 记录为执行错误，不伪装成无结果。
    return {
        'output': {'query': request.query, 'knowledge_base': request.knowledge_base,
                   'top_k': request.top_k, 'hits': hits,
                   'context': [hit['parent_content'] for hit in hits]},
        'metadata': {'model': MODEL, 'embedding_profile': profile(),
                     'retrieval_ms': round((perf_counter() - start) * 1000, 2)},
    }
