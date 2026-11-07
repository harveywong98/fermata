"""评测评分器不能把错误来源、缺失证据或部分召回算作全部通过。"""
import json
import pytest
from evals.rag.score import get_assert


def test_evidence_requires_correct_source_and_complete_coverage():
    context = {'vars': {'expected_evidence': [
        {'file_name': 'a.txt', 'quote': '人工确认'},
        {'file_name': 'b.txt', 'quote': '6000 字符'},
    ]}}
    hits = [{'file_name': 'wrong.txt', 'parent_content': '人工确认'},
            {'file_name': 'a.txt', 'parent_content': '人工\n确认'}]
    result = get_assert({'hits': hits}, context)
    assert result['score'] == 0.5 and not result['pass']
    assert result['namedScores']['first_evidence_rr'] == 0.5
    hits.append({'file_name': 'b.txt', 'parent_content': '最多 6000 字符'})
    result = get_assert(json.dumps({'hits': hits}), context)
    assert result['score'] == 1 and result['pass']


def test_empty_retrieval_fails_and_invalid_labels_are_errors():
    context = {'vars': {'expected_evidence': [{'file_name': 'a.txt', 'quote': '证据'}]}}
    result = get_assert({'hits': []}, context)
    assert not result['pass'] and result['score'] == 0
    with pytest.raises(ValueError):
        get_assert({'hits': []}, {'vars': {'expected_evidence': []}})
