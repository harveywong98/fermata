"""Agent 的知识工具：直接调用本项目知识模块，无内部 HTTP 跳转。"""
import os
import httpx
import psycopg
from langchain_core.tools import tool
from knowledge.errors import KnowledgeError
from knowledge.retrieval import search
from knowledge.schemas import SearchRequest


@tool
def search_knowledge(query: str) -> dict:
    """检索当前业务知识库的字段定义、分类标准、降噪规则及已核验案例。

    query 应描述业务对象、上下文和疑问。返回命中片段、父正文和来源 ID；
    候选证据不代表已验证结论。parent_truncated 为真时上下文不完整。
    no_results 是没有候选，error 是工具失败，均不能作为业务否定结论。
    已入库的表结构可供查证，但本工具不能获取实时记录或统计数量。
    """
    query = query.strip()
    if not query or len(query) > 2000:
        return {'status': 'error', 'error': '查询内容须为1～2000个字符'}
    knowledge_base = os.getenv('KNOWLEDGE_BASE', '电力')
    try:
        results = search(SearchRequest(query=query, knowledge_base=knowledge_base, top_k=5))
        if not isinstance(results, list) or not all(isinstance(r, dict) for r in results):
            raise ValueError('检索返回格式异常')
    except KnowledgeError as exc:
        return {'status': 'error', 'error': '知识库检索失败', 'error_code': exc.status_code}
    except (psycopg.Error, httpx.HTTPError, OSError, ValueError, KeyError) as exc:
        return {'status': 'error', 'error': f'知识库不可用或配置无效：{type(exc).__name__}'}
    return {'status': 'success' if results else 'no_results',
            'knowledge_base': knowledge_base, 'results': results}
