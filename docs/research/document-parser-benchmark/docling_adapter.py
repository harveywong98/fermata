"""Benchmark adapter: native structured output plus common scoring representation."""
import time
_cache={}
def parse(source,native=False):
 from docling.document_converter import DocumentConverter,PdfFormatOption
 from docling.datamodel.base_models import InputFormat
 from docling.datamodel.pipeline_options import PdfPipelineOptions
 from docling.datamodel.accelerator_options import AcceleratorOptions,AcceleratorDevice
 from docling_core.types.doc import TableItem,TextItem
 key='native' if native else 'converter'
 if key not in _cache:
  opts=PdfPipelineOptions(do_ocr=False,do_table_structure=True)
  opts.accelerator_options=AcceleratorOptions(num_threads=4,device=AcceleratorDevice.CPU)
  if native:
   from docling.document_converter import NativePdfFormatOption
   _cache[key]=DocumentConverter(format_options={InputFormat.PDF:NativePdfFormatOption()})
  else:_cache[key]=DocumentConverter(format_options={InputFormat.PDF:PdfFormatOption(pipeline_options=opts)})
 started=time.perf_counter()
 result=_cache[key].convert(source,raises_on_error=False)
 converted=time.perf_counter()
 doc=result.document;blocks=[]
 for item,level in doc.iterate_items():
  if isinstance(item,TableItem):
   rows=[['' for _ in range(item.data.num_cols)] for _ in range(item.data.num_rows)]
   for cell in item.data.table_cells:
    for ri in range(cell.start_row_offset_idx,cell.end_row_offset_idx):
     for ci in range(cell.start_col_offset_idx,cell.end_col_offset_idx):rows[ri][ci]=cell.text
   blocks.append({'kind':'table','type':'Table','text':'\n'.join(' | '.join(r) for r in rows),'rows':rows,'metadata':{'text_as_html':item.export_to_html(doc=doc)},'source':[p.model_dump(mode='json') for p in item.prov]})
  elif isinstance(item,TextItem):
   blocks.append({'kind':'heading' if item.label.value in {'title','section_header'} else 'paragraph','type':item.label.value,'text':item.text,'source':[p.model_dump(mode='json') for p in item.prov]})
 return {'blocks':blocks,'native':doc.export_to_dict(),'conversion_status':result.status.value,'conversion_errors':[str(e) for e in result.errors],'convert_s':converted-started,'adapter_s':time.perf_counter()-converted,'config':{'pdf_ocr':False,'pdf_table_structure':not native,'native':native,'device':'cpu','threads':4}}
