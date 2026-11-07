"""观察真实 Search 及评测 provider 的输入输出，不验证检索正确性。

依赖：根 .env 数据库配置、Embedding 服务和演示知识库。
准备：uv run python -m evals.rag.scripts.prepare
运行：uv run pytest tests/learning/test_search_api.py -q -s
"""
from evals.rag.scripts.provider import call_api
from evals.rag.scripts.prepare import KNOWLEDGE_BASE


def test_search_result_structure():
    options = {'config': {'knowledge_base': KNOWLEDGE_BASE, 'top_k': 5}}
    result = call_api('上传完文档就能搜到了吗？', options, {})
    output = result['output']
    print('参数:', options['config'])
    print('结果字段类型:', {k: type(v).__name__ for k, v in output.items()})
    print('模型与耗时:', result['metadata'])
    print('命中数量:', len(output['hits']))
    if output['hits']:
        hit = output['hits'][0]
        print('命中字段类型:', {k: type(v).__name__ for k, v in hit.items()})
        print('第一条命中:', hit)
