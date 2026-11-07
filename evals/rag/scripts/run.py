"""检查索引并运行 promptfoo 基线；文件引用和结果输出由 YAML 配置。"""
from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
import sys

from evals.rag.scripts.prepare import CORPUS, KNOWLEDGE_BASE
from rag.embedding.client import profile
from rag.storage.repository import db

HERE = Path(__file__).resolve().parents[1]


def main():
    cli = shutil.which('promptfoo')
    if not cli:
        raise SystemExit('请先安装 CLI：npm install -g promptfoo@0.125.1')
    expected = {p.name: sha256(p.read_bytes()).hexdigest() for p in CORPUS.glob('*.txt')}
    with db() as conn:
        docs = conn.execute('SELECT file_name,file_hash,active_chunk_set_id,processing_config FROM knowledge.document WHERE knowledge_base_id=%s',
                            (KNOWLEDGE_BASE,)).fetchall()
    if {d['file_name']: d['file_hash'] for d in docs} != expected or any(not d['active_chunk_set_id'] for d in docs):
        raise SystemExit('演示索引与 corpus 不一致。先运行 python -m evals.rag.scripts.prepare；已有旧版本请在知识管理页处理后重建。')
    current_profile = profile()
    if any(d['processing_config'].get('profile') != current_profile for d in docs):
        raise SystemExit('演示索引使用了不同模型版本，请重新入库后再评测。')
    env = {**os.environ, 'PROMPTFOO_PYTHON': sys.executable, 'PROMPTFOO_DISABLE_TELEMETRY': '1'}
    result = subprocess.run([cli, 'eval', '-c', str(HERE / 'retrieval.yaml'), '--no-cache', '--no-share',
                             '--no-progress-bar', '--no-table'], cwd=HERE, env=env)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
