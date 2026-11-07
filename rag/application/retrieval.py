"""应用内部检索入口，供 Agent 工具与 Web 共用。"""
from rag.embedding.client import embed, profile
from rag.storage.repository import db
from rag.contracts import SearchRequest

def search(request: SearchRequest):
    vector = embed(['为这个句子生成表示以用于检索相关文章：' + request.query])[0]
    with db() as conn:
        rows = conn.execute('''SELECT c.id AS chunk_id,c.parent_id,c.document_id,c.file_name,c.content AS matched_content,
            c.metadata,1-(c.embedding <=> %s::vector) AS score,s.title,s.content AS parent_content
            FROM knowledge.searchable_chunk c JOIN knowledge.document_chunk s ON s.id=c.parent_id AND s.chunk_role='parent'
            WHERE c.knowledge_base_id=%s AND c.embedding_profile=%s
            ORDER BY c.embedding <=> %s::vector LIMIT %s''',
            (vector,request.knowledge_base,profile(),vector,request.top_k)).fetchall()
    results = {}
    for row in rows:
        if row['parent_id'] not in results:
            row['parent_truncated'] = len(row['parent_content']) > 6000
            row['parent_content'] = row['parent_content'][:6000]
            results[row['parent_id']] = row
    return list(results.values())
