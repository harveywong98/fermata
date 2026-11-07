"""真实服务验证：确认前PG零写入，确认后原子发布，父子召回与删除。"""
from io import BytesIO
from pathlib import Path
import sys
from uuid import uuid4
from unittest.mock import patch
import httpx
from docx import Document
from openpyxl import Workbook
from reportlab.pdfgen.canvas import Canvas

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rag.application import service as app
from rag.contracts import KnowledgeError
from rag.contracts import PublishRequest

base = '__smoke_' + uuid4().hex
ids, draft_ids = [], []

def checked(r):
    r.raise_for_status()
    return r.json()

def snapshot(kb):
    with app.db() as conn:
        return [conn.execute(sql,(kb,)).fetchall() for sql in [
            'SELECT d.* FROM knowledge.document d WHERE knowledge_base_id=%s ORDER BY id',
            'SELECT c.* FROM knowledge.document_chunk c JOIN knowledge.document d ON d.id=c.document_id WHERE d.knowledge_base_id=%s ORDER BY c.id']]

with httpx.Client(base_url='http://127.0.0.1:8018/api',timeout=180) as c:
    try:
        marker='唯一待删除文字'
        raw=''.join(f'第{i}条规则，设备编号需结合业务用途判断。'+(marker+'。' if i==20 else '') for i in range(50))
        word=BytesIO();d=Document();d.add_heading('身份识别',1);d.add_paragraph('设备编号应排除，不能仅凭数字长度判断身份证。');d.save(word)
        excel=BytesIO();w=Workbook();w.active.append(['类型','说明']);w.active.append(['设备编号','标识设备']);w.save(excel)
        pdf=BytesIO();p=Canvas(pdf);p.drawString(50,750,'Equipment identifiers require business context.');p.save()
        for i,(name,data) in enumerate([('rules.txt',raw.encode()),('rules.docx',word.getvalue()),('types.xlsx',excel.getvalue()),('rules.pdf',pdf.getvalue())]):
            kb=base+str(i)
            result=checked(c.post('/documents',files={'file':(name,data)},data={'knowledge_base':kb}))
            draft=result['draft_id'];draft_ids.append(draft)
            assert snapshot(kb)==[[],[]]
            first=checked(c.post(f'/drafts/{draft}/preview',json={'size':128,'overlap':20}))
            second=checked(c.post(f'/drafts/{draft}/preview',json={'size':160,'overlap':20}))
            assert snapshot(kb)==[[],[]]
            assert c.post(f'/drafts/{draft}/publish',json={'preview_id':first['preview_id']}).status_code==409
            if i==0:
                info=checked(c.get(f'/drafts/{draft}'))
                target=next(x for x in info['chunks'] if marker in x['content'])
                checked(c.delete(f"/drafts/{draft}/chunks/{target['id']}",params={'preview_id':second['preview_id']}))
                second=checked(c.post(f'/drafts/{draft}/preview',json={'size':180,'overlap':20}))
                info=checked(c.get(f'/drafts/{draft}'))
                assert all(marker not in x['content'] for x in info['parents'])
                assert all(marker not in x['embedding_text'] for x in info['chunks'])
                assert snapshot(kb)==[[],[]]
                with patch.object(app,'embed',side_effect=KnowledgeError(502,'simulated failure')):
                    try:app.publish(app.UUID(draft),PublishRequest(preview_id=second['preview_id']))
                    except KnowledgeError as e:assert e.status_code==502
                    else:raise AssertionError('Expected failure')
                assert snapshot(kb)==[[],[]]
            published=checked(c.post(f'/drafts/{draft}/publish',json={'preview_id':second['preview_id']}))
            id=published['id'];ids.append(id)
            before=snapshot(kb);assert all(before)
            assert checked(c.post(f'/drafts/{draft}/publish',json={'preview_id':second['preview_id']}))['id']==id
            assert snapshot(kb)==before
            duplicate=checked(c.post('/documents',files={'file':(name,data)},data={'knowledge_base':kb}))
            assert duplicate['id']==id and duplicate['duplicate']
            hits=checked(c.post('/search',json={'query':'设备编号如何识别','knowledge_base':kb}))
            assert hits and all(h['parent_content'] and h['matched_content'] for h in hits)
            if i==0:assert all(marker not in h['parent_content'] for h in hits)
            edit=checked(c.post(f'/documents/{id}/draft'))['draft_id'];draft_ids.append(edit)
            assert snapshot(kb)==before  # 打开编辑也不写PG
            info=checked(c.get(f'/drafts/{edit}'))
            ch=info['chunks'][0];revision=info['document']['processing_config']['preview_id']
            b=checked(c.delete(f"/drafts/{edit}/chunks/{ch['id']}",params={'preview_id':revision}))
            assert snapshot(kb)==before  # 删除预览不改已发布内容
            checked(c.post(f'/drafts/{edit}/publish',json={'preview_id':b['preview_id']}))
            if len(info['chunks'])==1:
                assert checked(c.post('/search',json={'query':'设备编号','knowledge_base':kb}))==[]
            print(name,'PASS: no PG writes before confirm; publish/edit/delete/retrieval',flush=True)
        print('PASS: two-table snapshots unchanged before confirm, embedding failure rollback, stale preview, idempotency, parent/overlap cleanup and empty publication.')
    finally:
        for id in ids:checked(c.delete(f'/documents/{id}'))
        for id in draft_ids:checked(c.delete(f'/drafts/{id}'))
