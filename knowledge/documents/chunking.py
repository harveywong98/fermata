"""按模型 token 预算将父单元切成子块，保留字符范围与来源。"""
import re
from knowledge.embedding.tokenizer import tokens


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
