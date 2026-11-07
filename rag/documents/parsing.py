"""将文档解析为带来源信息的父单元，不切分或向量化。"""
from functools import lru_cache
from threading import Lock
import re

PARSE_LOCK = Lock()


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
