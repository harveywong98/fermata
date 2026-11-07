"""文档与草稿业务逻辑；不依赖 FastAPI 或 HTTP 路由。"""
from hashlib import sha256
from pathlib import Path
import shutil
from uuid import UUID, uuid4
from psycopg.types.json import Jsonb
from config import DATA_DIR as DATA
from knowledge.application import drafts
from knowledge.documents.parsing import parse_file
from knowledge.embedding.client import embed, MODEL, profile
from knowledge.contracts import KnowledgeError
from knowledge.storage.repository import db
from knowledge.contracts import SplitRequest, PublishRequest

def digest(text):
    return sha256(text.encode()).hexdigest()


def document(conn, id, lock=False):
    row = conn.execute('SELECT * FROM knowledge.document WHERE id=%s' + (' FOR UPDATE' if lock else ''), (id,)).fetchone()
    if row is None:
        raise KnowledgeError(404, '文档不存在')
    return row


def documents():
    with db() as conn:
        return conn.execute('SELECT id,file_name,knowledge_base_id,status,active_chunk_set_id,created_at FROM knowledge.document ORDER BY id DESC').fetchall()


def upload(file, knowledge_base: str = '电力'):
    name = Path((file.filename or '').replace('\\', '/')).name
    if Path(name).suffix.lower() not in {'.pdf', '.docx', '.xlsx', '.txt', '.md'}:
        raise KnowledgeError(400, '支持PDF、DOCX、XLSX、TXT、MD')
    raw = file.file.read(20 * 1024 * 1024 + 1)
    file.file.close()
    if not raw or len(raw) > 20 * 1024 * 1024:
        raise KnowledgeError(400, '文件为空或超过20MiB')
    file_hash = sha256(raw).hexdigest()
    with db() as conn:  # 只读重复检查；此阶段不插入文档
        old = conn.execute('SELECT id FROM knowledge.document WHERE knowledge_base_id=%s AND file_hash=%s', (knowledge_base,file_hash)).fetchone()
    if old:
        return {**old, 'duplicate': True}
    draft_id = str(uuid4())
    directory = drafts.ROOT / draft_id
    directory.mkdir(parents=True)
    path = directory / ('source' + Path(name).suffix.lower())
    try:
        path.write_bytes(raw)
        sections = parse_file(path)
        if not sections:
            raise ValueError('没有可提取文本；扫描PDF需要OCR，本版未启用')
        drafts.save({'draft_id':draft_id, 'base_batch':None, 'chunks':[], 'parents':sections,
            'document':{'id':None,'knowledge_base_id':knowledge_base,'file_name':name,'file_uri':str(path),
                'file_hash':file_hash,'file_size':len(raw),'mime_type':file.content_type,'processing_config':{}}})
    except Exception as exc:
        shutil.rmtree(directory)
        raise KnowledgeError(400, f'解析失败：{exc}') from exc
    return {'draft_id':draft_id}


def detail(id: int):
    with db() as conn:
        doc = document(conn,id)
        parents = conn.execute("SELECT * FROM knowledge.document_chunk WHERE document_id=%s AND chunk_set_id=%s AND chunk_role='parent' ORDER BY ordinal", (id,doc['active_chunk_set_id'])).fetchall()
        chunks = conn.execute("SELECT id,parent_id,ordinal,content,embedding_text,metadata,embedding_status FROM knowledge.document_chunk WHERE document_id=%s AND chunk_set_id=%s AND chunk_role='child' ORDER BY ordinal",(id,doc['active_chunk_set_id'])).fetchall()
    return {'document':doc,'parents':parents,'parsed':parents,'chunks':chunks}


def edit_document(id: int):
    info = detail(id)
    draft = {'draft_id':str(uuid4()),'document':info['document'],'parents':info['parents'],
             'base_batch':str(info['document']['active_chunk_set_id'])}
    config = info['document']['processing_config']
    with drafts.LOCK:
        drafts.build(draft,config.get('size',400),config.get('overlap',40))
    return {'draft_id':draft['draft_id']}


def list_drafts():
    with drafts.LOCK:
        rows = [drafts.load(p.parent.name) for p in drafts.ROOT.glob('*/draft.json')]
    return [{'draft_id':d['draft_id'],'file_name':d['document']['file_name']} for d in rows
            if not d.get('published_preview') or d['published_preview'] != d['document']['processing_config'].get('preview_id')]


def get_draft(id: UUID):
    with drafts.LOCK:
        return drafts.view(drafts.load(id))


def preview(id: UUID, request: SplitRequest):
    with drafts.LOCK:
        draft = drafts.build(drafts.load(id),request.size,request.overlap)
    return {'preview_id':draft['document']['processing_config']['preview_id'],'chunks':len(draft['chunks'])}


def delete_chunk(id: UUID, chunk_id: int, preview_id: UUID):
    with drafts.LOCK:
        draft = drafts.load(id)
        config = draft['document']['processing_config']
        if config.get('preview_id') != str(preview_id):
            raise KnowledgeError(409,'预览已改变，请刷新')
        chunk = next((c for c in draft['chunks'] if c['id']==chunk_id),None)
        if chunk is None:
            raise KnowledgeError(409,'块已改变，请刷新')
        remaining = []
        for section in draft['parents']:
            if section['id']==chunk['parent_id']:
                start,end = chunk['metadata']['char_start'],chunk['metadata']['char_end']
                if section['content'][start:end] != chunk['content']:
                    raise KnowledgeError(409,'父子内容不一致，不能安全删除')
                section['content'] = (section['content'][:start].rstrip()+'\n'+section['content'][end:].lstrip()).strip()
                section['metadata'] = {**section['metadata'],'manually_edited':True}
                if not section['content'] or (section['metadata'].get('block_type')=='table' and len(section['content'].splitlines())<=2):
                    continue
            remaining.append(section)
        draft['parents'] = remaining
        drafts.build(draft,config['size'],config['overlap'])
    return {'preview_id':draft['document']['processing_config']['preview_id'],'chunks':len(draft['chunks'])}


def discard(id: UUID):
    with drafts.LOCK:
        drafts.load(id)
        shutil.rmtree(drafts.ROOT / str(id))
    return {'discarded':str(id)}


def publish(id: UUID, request: PublishRequest):
    with drafts.LOCK:
        draft = drafts.load(id)
        config = draft['document']['processing_config']
        if config.get('preview_id') != str(request.preview_id):
            raise KnowledgeError(409,'预览已过期，请重新查看')
        if draft.get('published_preview') == str(request.preview_id):
            with db() as conn:
                document(conn,draft['document']['id'])
            return {'id':draft['document']['id'],'status':'ready'}
    vectors = embed([c['embedding_text'] for c in draft['chunks']])
    copied = None
    with drafts.LOCK:
        current = drafts.load(id)
        if current['document']['processing_config'] != config:
            raise KnowledgeError(409,'编码期间预览已改变，请重新确认')
        if current.get('published_preview') == str(request.preview_id):
            return {'id':current['document']['id'],'status':'ready'}
        doc = draft['document']
        try:
            with db() as conn:
                if doc['id'] is None:
                    existing = conn.execute('SELECT * FROM knowledge.document WHERE knowledge_base_id=%s AND file_hash=%s FOR UPDATE', (doc['knowledge_base_id'],doc['file_hash'])).fetchone()
                    if existing:
                        if existing['active_chunk_set_id'] == request.preview_id:
                            # 数据库已提交、草稿回写中断时，恢复确认结果，不再插入。
                            draft['document']['id'] = existing['id']
                            draft['document']['file_uri'] = existing['file_uri']
                            draft['base_batch'] = draft['published_preview'] = str(request.preview_id)
                            drafts.save(draft)
                            return {'id':existing['id'],'status':'ready'}
                        raise KnowledgeError(409,'相同文件已入库，请从文件列表打开编辑')
                    copied = DATA / ('published-' + str(id) + Path(doc['file_uri']).suffix)
                    shutil.copy2(doc['file_uri'],copied)
                    row = conn.execute('''INSERT INTO knowledge.document(knowledge_base_id,file_name,file_uri,file_hash,file_size,mime_type,status)
                        VALUES (%s,%s,%s,%s,%s,%s,'ready') ON CONFLICT (knowledge_base_id,file_hash) DO NOTHING RETURNING id''',
                        (doc['knowledge_base_id'],doc['file_name'],str(copied),doc['file_hash'],doc['file_size'],doc['mime_type'])).fetchone()
                    if row is None:
                        raise KnowledgeError(409,'相同文件已入库，请从文件列表打开编辑')
                    document_id = row['id']
                else:
                    document_id = doc['id']
                    latest = document(conn,document_id,lock=True)
                    if str(latest['active_chunk_set_id']) != draft['base_batch']:
                        raise KnowledgeError(409,'已发布版本发生变化，请重新打开文档')
                parent_ids = {}
                for index,s in enumerate(draft['parents']):
                    parent_ids[index] = conn.execute('''INSERT INTO knowledge.document_chunk(document_id,chunk_set_id,ordinal,title,content,metadata,content_hash,chunk_role,embedding_model,embedding_profile,embedding_status)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,'parent','not_applicable','not_applicable','not_required') RETURNING id''',
                        (document_id,request.preview_id,index,s['title'],s['content'],Jsonb(s['metadata']),digest(s['content']))).fetchone()['id']
                for c,v in zip(draft['chunks'],vectors):
                    conn.execute('''INSERT INTO knowledge.document_chunk
                        (document_id,chunk_set_id,parent_id,ordinal,content,content_hash,embedding_model,embedding_profile,embedding_text,input_hash,metadata,embedding,embedding_status)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::vector,'ready')''',
                        (document_id,request.preview_id,parent_ids[c['parent_id']],c['ordinal'],c['content'],digest(c['content']),MODEL,profile(),
                         c['embedding_text'],digest(c['embedding_text']),Jsonb(c['metadata']),v))
                conn.execute("UPDATE knowledge.document SET active_chunk_set_id=%s,processing_config=%s,status='ready',updated_at=now() WHERE id=%s",
                             (request.preview_id,Jsonb({**config,'profile':profile()}),document_id))
                conn.execute('DELETE FROM knowledge.document_chunk WHERE document_id=%s AND chunk_set_id<>%s',(document_id,request.preview_id))
        except Exception:
            if copied:
                copied.unlink(missing_ok=True)
            raise
        doc['id'] = document_id
        if copied:
            doc['file_uri'] = str(copied)
        draft['base_batch'] = draft['published_preview'] = str(request.preview_id)
        drafts.save(draft)
    return {'id':document_id,'status':'ready','chunks':len(vectors)}


def delete(id: int):
    with db() as conn:
        doc = document(conn, id, lock=True)
        conn.execute('DELETE FROM knowledge.document WHERE id=%s', (id,))
    path = Path(doc['file_uri'])
    path.unlink(missing_ok=True); path.with_suffix('.json').unlink(missing_ok=True)
    return {'deleted': id}
