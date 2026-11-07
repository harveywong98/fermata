"""知识库数据库连接与 schema 初始化。"""
import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from config import DATA_DIR

def db():
    return psycopg.connect(os.environ['DATABASE_URL'], row_factory=dict_row, connect_timeout=5)


def initialize():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with db() as conn:
        if conn.execute("SELECT to_regclass('knowledge.document') AS t").fetchone()['t'] is None:
            conn.execute((Path(__file__).parent / 'sql/schema.sql').read_text())
        if not conn.execute("SELECT 1 FROM information_schema.columns WHERE table_schema='knowledge' AND table_name='document_chunk' AND column_name='chunk_role'").fetchone():
            raise RuntimeError('旧表结构需要显式迁移；不会自动删除数据')
