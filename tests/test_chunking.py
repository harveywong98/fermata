from knowledge.chunking import split_section, tokens


def test_budget_coverage_and_overlap():
    text = '18位设备编号需要结合字段用途判断，不应直接认定为身份证。' * 60
    section = {'title': '隐私 / 身份识别', 'content': text, 'metadata': {'block_type': 'text'}}
    chunks = split_section(section, 128, 20)
    assert len(chunks) > 1
    covered = set()
    for c in chunks:
        assert tokens(c['embedding_text']) <= 128
        m = c['metadata']
        assert c['content'] == text[m['char_start']:m['char_end']]
        covered.update(range(m['char_start'], m['char_end']))
    assert covered == set(range(len(text)))
    assert chunks[1]['metadata']['char_start'] < chunks[0]['metadata']['char_end']


def test_table_headers_and_no_cross_row_overlap():
    text = '|类型|级别|\n|---|---|\n' + ''.join(f'|设备编号{i}|内部|\n' for i in range(80))
    chunks = split_section({'title': '目录', 'content': text, 'metadata': {'block_type': 'table'}}, 128, 20)
    assert len(chunks) > 1
    assert all('|类型|级别|' in c['embedding_text'] and tokens(c['embedding_text']) <= 128 for c in chunks)
    assert all(a['metadata']['char_end'] == b['metadata']['char_start'] for a,b in zip(chunks,chunks[1:]))
