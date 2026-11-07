"""Docling结构解析；按父单元生成有来源关联的检索子块。"""
from functools import lru_cache
from pathlib import Path
from threading import Lock
import re

from config import MODEL_DIR
PARSE_LOCK = Lock()


@lru_cache
def tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(MODEL_DIR / 'tokenizer', local_files_only=True)


def tokens(text):
    return len(tokenizer().encode(text, add_special_tokens=True))


@lru_cache
def converter():
    from docling.document_converter import DocumentConverter, NativePdfFormatOption
    from docling.datamodel.base_models import InputFormat
    return DocumentConverter(format_options={InputFormat.PDF: NativePdfFormatOption()})


def parse_file(path):
    """父单元为标题下的连续正文或一张表；TXT按非空段/行保留。"""
    if path.suffix.lower() == '.txt':
        text = path.read_text(encoding='utf-8-sig').replace('\x00', '')
        return [{'title': '', 'content': p.strip(), 'metadata': {'block_type': 'text'}}
                for p in re.split(r'\n\s*\n' if '\n\n' in text else r'\n', text) if p.strip()]
    from docling_core.types.doc import TableItem, TextItem
    with PARSE_LOCK:
        result = converter().convert(path, raises_on_error=False)
    if result.status.value != 'success':
        raise ValueError('Docling解析未完整成功，请检查文件或转换日志')
    doc = result.document
    sections, headings, current = [], [], None
    for item, _ in doc.iterate_items():
        if isinstance(item, TextItem) and item.label.value in {'page_header', 'page_footer'}:
            continue
        if isinstance(item, TextItem) and item.label.value in {'title', 'section_header'}:
            level = getattr(item, 'level', 1) or 1
            headings = headings[:max(0, level - 1)] + [item.text]
            current = None
            continue
        if isinstance(item, TableItem):
            text, kind = item.export_to_markdown(doc=doc), 'table'
        elif isinstance(item, TextItem):
            text, kind = item.text, 'text'
        else:
            continue
        text = text.replace('\x00', '').strip()
        if not text:
            continue
        if current is None or kind == 'table':
            current = {'title': ' / '.join(headings), 'content': '', 'metadata': {
                'heading_path': headings[:], 'block_type': kind, 'sources': []}}
            sections.append(current)
        current['content'] += ('\n\n' if current['content'] else '') + text
        current['metadata']['sources'].extend(p.model_dump(mode='json') for p in item.prov)
        if kind == 'table':
            current = None
    return sections


def split_section(section, size=400, overlap=40):
    """size包含标题/表头和特殊token；保存字符区间，不静默截断正文。"""
    title = section['title']
    while title and tokens(title) > min(64, size // 4):
        title = title[1:]  # 超长路径优先保留靠近当前单元的标题
    prefix = f'标题：{title}\n' if title else ''
    text = section['content']
    if section['metadata'].get('block_type') == 'table':
        lines = text.splitlines(keepends=True)
        if len(lines) > 2 and re.match(r'^\s*\|?\s*:?-', lines[1]):
            header = ''.join(lines[:2])
            if tokens(prefix + header) < size // 2:
                prefix += header
                offset, text = len(header), ''.join(lines[2:])
            else:
                offset = 0  # 表头本身过长，按通用逻辑拆，回读父表补上下文
        else:
            offset = 0
        overlap = 0  # 表格不重复相邻行，表头单独携带
    else:
        offset = 0
    chunks, start = [], 0
    while start < len(text):
        lo, hi = start + 1, len(text)
        end = start
        while lo <= hi:
            mid = (lo + hi) // 2
            if tokens(prefix + text[start:mid]) <= size:
                end, lo = mid, mid + 1
            else:
                hi = mid - 1
        if end == start:
            raise ValueError('标题或表头占用过多，请增大切块预算')
        reason = 'complete'
        if end < len(text):
            boundaries = [m.end() + start for m in re.finditer(r'[。！？；\n]', text[start:end])]
            boundary = next((b for b in reversed(boundaries) if b > start + (end-start)//2), None)
            end, reason = (boundary, 'sentence_boundary') if boundary else (end, 'token_limit')
        content = text[start:end]
        if content.strip():
            encoded = prefix + content
            chunks.append({'content': content, 'embedding_text': encoded,
                           'metadata': {**section['metadata'], 'char_start': start + offset,
                                        'char_end': end + offset, 'split_reason': reason,
                                        'token_count': tokens(encoded)}})
        if end == len(text):
            break
        # 最长的、不超过overlap预算的尾部；确保每轮推进。
        lo, hi = start + 1, end
        while lo < hi:
            mid = (lo + hi) // 2
            if tokens(text[mid:end]) - 2 <= overlap:
                hi = mid
            else:
                lo = mid + 1
        start = lo if overlap else end
    return chunks
