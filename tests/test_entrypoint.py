"""统一入口不能在导入时调用模型、读取权重或连接数据库。"""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_import_without_runtime_assets(tmp_path):
    env = {**os.environ, 'KNOWLEDGE_MODEL_DIR': str(tmp_path / 'missing-models'),
           'DATABASE_URL': 'postgresql://unused:unused@127.0.0.1:1/unused'}
    result = subprocess.run(
        [sys.executable, '-c', 'import main, agent.runtime; from web.app import app; app.openapi()'],
        cwd=ROOT, env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_unfinished_agent_exits_with_todo():
    result = subprocess.run([sys.executable, 'main.py', 'agent'], cwd=ROOT,
                            text=True, capture_output=True, timeout=30)
    assert result.returncode == 2
    assert 'Agent 尚未完成' in result.stderr
    assert 'Traceback' not in result.stderr


def test_paths_resolve_from_project_root(tmp_path):
    env = {**os.environ, 'PYTHONPATH': os.pathsep.join([str(ROOT), os.environ.get('PYTHONPATH', '')]),
           'KNOWLEDGE_DATA_DIR': 'knowledge/data'}
    result = subprocess.run([sys.executable, '-c',
                             'from config import DATA_DIR; print(DATA_DIR)'],
                            cwd=tmp_path, env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(ROOT / 'knowledge/data')
