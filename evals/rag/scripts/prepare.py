"""准备专用演示知识库；复用应用上传/预览/发布，不修改其他知识库。

运行：uv run python -m evals.rag.scripts.prepare
需要根 .env 数据库配置、本地 tokenizer 和运行中的 Embedding。
"""
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

from rag.application import service
from rag.contracts import PublishRequest, SplitRequest
from rag.storage.repository import initialize

KNOWLEDGE_BASE = '__eval_fermata_demo_v1'
CORPUS = Path(__file__).resolve().parents[1] / 'corpus'


def main():
    initialize()
    for path in sorted(CORPUS.glob('*.txt')):
        draft = None
        try:
            with path.open('rb') as handle:
                result = service.upload(SimpleNamespace(filename=path.name, file=handle, content_type='text/plain'),
                                        knowledge_base=KNOWLEDGE_BASE)
            if result.get('duplicate'):
                print(f'{path.name}: 已存在，保持原样')
                continue
            draft = UUID(result['draft_id'])
            preview = service.preview(draft, SplitRequest(size=400, overlap=40))
            service.publish(draft, PublishRequest(preview_id=UUID(preview['preview_id'])))
            print(f'{path.name}: 已发布到 {KNOWLEDGE_BASE}')
        finally:
            if draft is not None:
                service.discard(draft)


if __name__ == '__main__':
    main()
