"""Small controlled fixtures; expectations are independent of parser output."""
import json
from pathlib import Path
from docx import Document
from openpyxl import Workbook
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
from PIL import Image,ImageDraw
B=Path(__file__).resolve().parent; F=B/'fixtures';F.mkdir(exist_ok=True)
expect={}
d=Document();d.add_heading('Privacy Classification',1);d.add_paragraph('Account ID is not automatically a national identity number.')
t=d.add_table(rows=1,cols=2);t.rows[0].cells[0].text='Field';t.rows[0].cells[1].text='Classification'
c=t.add_row().cells;c[0].text='customer_phone';c[1].text='Sensitive'
d.add_paragraph('END_OF_DOCUMENT');d.save(F/'structured.docx')
expect['structured.docx']={'terms':['Privacy Classification','customer_phone','Sensitive','END_OF_DOCUMENT'],'table_required':True,'heading_required':True}
w=Workbook();s=w.active;s.title='Classification';s.append(['Business','Identity',None,'Value']);s.merge_cells('B1:C1');s.append(['System','Field','Level','Sample']);s.append(['Power','account_id','Internal','00123']);s.append(['Power','enabled','Internal',False]);s.append(['Power','count','Internal',0]);s.append(['Power','formula','Internal','=1+1']);w.save(F/'merged.xlsx')
expect['merged.xlsx']={'terms':['account_id','00123','enabled','count'],'table_required':True,'formula_expected':'=1+1'}
c=Canvas(str(F/'text-table.pdf'));c.setFont('Helvetica-Bold',16);c.drawString(50,780,'Privacy Classification');c.setFont('Helvetica',12);c.drawString(50,740,'Field');c.drawString(260,740,'Classification');c.drawString(50,710,'customer_phone');c.drawString(260,710,'Sensitive');c.line(40,730,420,730);c.drawString(50,650,'END_OF_DOCUMENT');c.showPage();c.save()
expect['text-table.pdf']={'terms':['Privacy Classification','customer_phone','Sensitive','END_OF_DOCUMENT'],'table_required':True}
im=Image.new('RGB',(1200,400),'white');draw=ImageDraw.Draw(im);draw.text((60,100),'SCANNED PRIVACY POLICY',fill='black',font_size=50);draw.text((60,200),'Customer phone is sensitive data.',fill='black',font_size=38)
c=Canvas(str(F/'scan.pdf'));c.drawImage(ImageReader(im),30,450,width=540,height=180);c.showPage();c.save()
expect['scan.pdf']={'terms':['SCANNED PRIVACY POLICY','Customer phone'],'ocr_required':True}
(F/'expected.json').write_text(json.dumps(expect,indent=2))
print('created',len(expect),'controlled documents')
