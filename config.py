"""应用配置：统一从项目根目录 .env 加载，不依赖启动工作目录。"""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')

def local_path(name, default):
    path = Path(os.getenv(name, default)).expanduser()
    return path if path.is_absolute() else ROOT / path

# 知识能力的本地资源目录；可通过环境变量覆盖。
DATA_DIR = local_path('KNOWLEDGE_DATA_DIR', 'rag/data')
MODEL_DIR = local_path('KNOWLEDGE_MODEL_DIR', 'rag/models')
EMBEDDING_URL = os.getenv('EMBEDDING_URL', 'http://127.0.0.1:18087').rstrip('/')
