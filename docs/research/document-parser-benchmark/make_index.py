"""Human-readable index; names link to content-addressed local copies."""
import csv,html,json
from pathlib import Path
B=Path(__file__).resolve().parent
m=json.loads((B/'manifest.json').read_text())
with (B/'FILES.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['filename','format','bytes','local_copy','original_path'])
 for d in m['documents']:
  for s in d['sources']:w.writerow([Path(s).name,d['extension'],d['bytes'],d['file'],s])
rows=[]
for d in sorted(m['documents'],key=lambda x:(x['extension'],x['sources'][0])):
 s=d['sources'][0]
 rows.append('<tr><td>'+html.escape(d['extension'])+'</td><td><a href="'+html.escape(d['file'],quote=True)+'">'+html.escape(Path(s).name)+'</a></td><td>'+f"{d['bytes']/1024:.1f} KB"+'</td><td>'+str(len(d['sources']))+'</td><td>'+html.escape(s)+'</td></tr>')
(B/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>文档测试集</title><style>body{font:15px system-ui;margin:30px}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #ddd;text-align:left}input{width:600px;padding:10px;margin-bottom:20px}</style><h1>文档测试集</h1><p>仅本机文件副本。原路径和全部重复来源见 FILES.csv；解析结果见 REPORT.md。</p><input id="q" placeholder="按文件名、格式、路径筛选"><table><thead><tr><th>格式</th><th>文件名（点击打开副本）</th><th>大小</th><th>来源数</th><th>首个来源</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table><script>document.querySelector('#q').oninput=e=>{let q=e.target.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))}</script>''')
print('Indexed',len(rows),'unique documents')
