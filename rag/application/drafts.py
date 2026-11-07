"""预览草稿仅在本机临时目录保存，不写PostgreSQL；单进程使用。"""
import json
from pathlib import Path
from threading import RLock
from uuid import uuid4
from rag.contracts import KnowledgeError
from rag.documents.chunking import split_section
from config import DATA_DIR

ROOT = DATA_DIR / 'drafts'
LOCK = RLock()


def load(id):
    path = ROOT / str(id) / 'draft.json'
    if not path.exists():
        raise KnowledgeError(404, '临时草稿不存在')
    return json.loads(path.read_text())


def save(draft):
    directory = ROOT / draft['draft_id']
    directory.mkdir(parents=True, exist_ok=True)
    temp = directory / 'draft.tmp'
    temp.write_text(json.dumps(draft, ensure_ascii=False, default=str))
    temp.replace(directory / 'draft.json')


def build(draft, size=400, overlap=40):
    children = []
    for index, section in enumerate(draft['parents']):
        section['id'] = index
        for child in split_section(section, size, overlap):
            children.append({**child, 'id': len(children), 'ordinal': len(children),
                             'parent_id': index, 'embedding_status': 'pending'})
    if len(children) > 5000:
        raise KnowledgeError(400, '分块超过5000，请调整文档或分块大小')
    draft['chunks'] = children
    draft['document']['processing_config'] = {'size': size, 'overlap': overlap,
        'preview_id': str(uuid4()), 'expected_chunks': len(children)}
    save(draft)
    return draft


def view(draft):
    return {**draft, 'parsed': draft['parents']}
