"""学习文档解析与切分 API：真实调用，不使用 mock。

依赖：本地 BGE tokenizer（KNOWLEDGE_MODEL_DIR/tokenizer），无需数据库或服务。
运行：uv run pytest tests/learning/test_chunking_api.py -q -s
"""
import json

from rag.documents.parsing import parse_file
from rag.documents.chunking import split_section


def test_parse_and_split_api(tmp_path):
    path = tmp_path / 'guide.txt'
    path.write_text('上传文档后，先检查解析内容和切分结果。' * 12, encoding='utf-8')
    sections = parse_file(path)
    section = sections[0]
    print('parse_file 返回:', type(sections).__name__)
    print('父单元字段类型:', {key: type(value).__name__ for key, value in section.items()})

    # TXT 不含结构化标题；补一个标题，观察它怎样进入 embedding_text。
    section['title'] = '知识库使用说明'
    size, overlap = 128, 20  # size 包括标题与特殊 token；overlap 是重叠预算。
    chunks = split_section(section, size=size, overlap=overlap)
    chunk = chunks[0]
    print('切分参数:', {'size': size, 'overlap': overlap})
    print('split_section 返回:', type(chunks).__name__, '块数:', len(chunks))
    print('子块字段类型:', {key: type(value).__name__ for key, value in chunk.items()})
    print('元数据字段类型:', {key: type(value).__name__ for key, value in chunk['metadata'].items()})
    # 字符范围为父正文中的左闭右开区间；这里只展示第一块。
    # 此时尚无数据库 ID，父子 ID 由后续草稿/发布流程分配。
    print('第一块:', json.dumps(chunk, ensure_ascii=False, indent=2))
