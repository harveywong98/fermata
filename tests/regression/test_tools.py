import unittest
from unittest.mock import patch
import psycopg

from tools import AGENT_TOOLS, search_knowledge
from rag.contracts import KnowledgeError


class KnowledgeToolTest(unittest.TestCase):
    def test_scope_and_evidence_are_preserved(self):
        evidence = {'document_id': 1, 'chunk_id': 2, 'parent_id': 3,
                    'file_name': '规则.txt', 'parent_content': '排除设备编号',
                    'parent_truncated': True, 'score': 0.8}
        with patch.dict('os.environ', {'KNOWLEDGE_BASE': '指定场景'}):
            with patch('tools.knowledge.search', return_value=[evidence]) as call:
                result = search_knowledge.invoke({'query': '设备编号'})
        self.assertEqual(call.call_args.args[0].model_dump(),
                         {'query': '设备编号', 'knowledge_base': '指定场景', 'top_k': 5})
        self.assertEqual(set(search_knowledge.args), {'query'})
        self.assertEqual(result['results'], [evidence])
        self.assertEqual(result['status'], 'success')
        self.assertIn(search_knowledge, AGENT_TOOLS)

    def test_empty_is_distinct_from_failure(self):
        with patch('tools.knowledge.search', return_value=[]):
            self.assertEqual(search_knowledge.invoke({'query': 'test'})['status'], 'no_results')
        for error in [KnowledgeError(502, 'offline'), psycopg.OperationalError('offline'),
                      FileNotFoundError('model'), KeyError('DATABASE_URL')]:
            with patch('tools.knowledge.search', side_effect=error):
                self.assertEqual(search_knowledge.invoke({'query': 'test'})['status'], 'error')
        with patch('tools.knowledge.search', return_value={'invalid': True}):
            self.assertEqual(search_knowledge.invoke({'query': 'test'})['status'], 'error')

    def test_invalid_query_does_not_search(self):
        for query in ['  ', 'x' * 2001]:
            with patch('tools.knowledge.search') as call:
                self.assertEqual(search_knowledge.invoke({'query': query})['status'], 'error')
                call.assert_not_called()
