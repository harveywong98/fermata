"""返回父上下文的证据覆盖率；不等同于 LLM Context Recall 或答案正确率。"""
import json


def get_assert(output, context):
    if isinstance(output, str):
        output = json.loads(output)
    expected = context['vars']['expected_evidence']
    if not expected or any(not e.get('file_name') or not e.get('quote', '').strip() for e in expected):
        raise ValueError('expected_evidence 需要非空的文件名与原文证据')
    hits = output['hits']
    ranks = []
    for evidence in expected:
        # 忽略换行/空白差异，仍要求同一来源文档中的实际原文，不做模型推断。
        quote = ''.join(evidence['quote'].split())
        rank = next((i for i, hit in enumerate(hits, 1)
                     if hit['file_name'] == evidence['file_name']
                     and quote in ''.join(hit['parent_content'].split())), None)
        ranks.append(rank)
    found = [rank for rank in ranks if rank is not None]
    coverage = len(found) / len(expected)
    missing = [e['file_name'] + ': ' + e['quote'] for e, rank in zip(expected, ranks) if rank is None]
    return {'pass': not missing, 'score': coverage,
            'reason': f'证据覆盖 {len(found)}/{len(expected)}；缺失：{missing}',
            'namedScores': {'evidence_coverage': coverage,
                            'first_evidence_rr': 1 / min(found) if found else 0}}
