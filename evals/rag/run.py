"""运行 promptfoo 基线并保留本次配置、索引信息和结果；不自动准备或改写索引。"""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from evals.rag.prepare import CORPUS, KNOWLEDGE_BASE
from knowledge.embedding.client import MODEL, profile
from knowledge.storage.repository import db

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main():
    cli = shutil.which('promptfoo')
    if not cli:
        raise SystemExit('请先安装 CLI：npm install -g promptfoo@0.125.1')
    expected = {p.name: sha256(p.read_bytes()).hexdigest() for p in CORPUS.glob('*.txt')}
    with db() as conn:
        docs = conn.execute('SELECT file_name,file_hash,active_chunk_set_id,processing_config FROM knowledge.document WHERE knowledge_base_id=%s',
                            (KNOWLEDGE_BASE,)).fetchall()
    if {d['file_name']: d['file_hash'] for d in docs} != expected or any(not d['active_chunk_set_id'] for d in docs):
        raise SystemExit('演示索引与 corpus 不一致。先运行 python -m evals.rag.prepare；已有旧版本请在知识管理页处理后重建。')
    current_profile = profile()
    if any(d['processing_config'].get('profile') != current_profile for d in docs):
        raise SystemExit('演示索引使用了不同模型版本，请重新入库后再评测。')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = HERE / 'results' / stamp
    out.mkdir(parents=True)
    # 仅复制公开评测配置，绝不复制 .env 或数据库连接串。
    for name in ['promptfooconfig.yaml', 'cases.yaml', 'provider.py', 'score.py']:
        shutil.copy2(HERE / name, out / name)
    version = subprocess.check_output([cli, '--version'], text=True).strip()
    manifest = {'started_at': stamp, 'promptfoo_version': version,
                'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)),
                'model': MODEL, 'profile': current_profile, 'knowledge_base': KNOWLEDGE_BASE,
                'corpus_sha256': expected, 'documents': docs,
                'code_sha256': {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
                                for base in [ROOT / 'knowledge', HERE]
                                for p in base.rglob('*.py') if 'results' not in p.parts}}
    manifest_path = out / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str))
    env = {**os.environ, 'PROMPTFOO_PYTHON': sys.executable, 'PROMPTFOO_DISABLE_TELEMETRY': '1'}
    result = subprocess.run([cli, 'eval', '-c', str(HERE / 'promptfooconfig.yaml'), '--no-cache', '--no-share',
                             '--no-progress-bar', '--no-table', '-o', str(out / 'results.json')], cwd=ROOT, env=env)
    manifest['exit_code'] = result.returncode
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str))
    print(f'本次配置与结果：{out}')
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
