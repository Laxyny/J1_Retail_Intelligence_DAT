"""Extraction, contrôles de contenu et rendu PDF en PNG pour inspection visuelle."""
import json
from pathlib import Path
from pypdf import PdfReader
import pypdfium2 as pdfium
from PIL import Image, ImageOps, ImageDraw

root=Path(__file__).resolve().parents[1]
path=root/'rapport/DAT_Retail_Intelligence_J3.pdf'
reader=PdfReader(path)
captures=list((root/'preuves/captures').glob('*.jpg'))
streams=[obj.get_object().get_data() for page in reader.pages
         for obj in page['/Resources'].get('/XObject',{}).values()
         if obj.get_object().get('/Subtype')=='/Image']
assert len(captures)==3
for capture in captures:
    assert capture.read_bytes() in streams, 'Capture originale non conservée : '+str(capture)
text='\n'.join(p.extract_text() for p in reader.pages)
for expected in ['667 579','17 820','33 755 474','1 150 529 586,37','495 971','2 575','73','Parquet']:
    assert expected in text,expected
for unexpected in ['TODO','[À compléter]','{{','lorem ipsum','�','Ã','Â','â€']:
    assert unexpected not in text,unexpected
output=root/'preuves/relecture_pdf'
output.mkdir(exist_ok=True)
pdf=pdfium.PdfDocument(path)
counts=[]
for i,page in enumerate(pdf):
    image=page.render(scale=1.5).to_pil().convert('RGB')
    image.save(output/f'page-{i+1:02}.png')
    count=len(reader.pages[i].extract_text())
    assert count>100,(i,count)
    counts.append(count)
for start in range(0,len(pdf),12):
    chosen=list(range(start,min(start+12,len(pdf))))
    sheet=Image.new('RGB',(1000,380*((len(chosen)+3)//4)),'#dedede')
    draw=ImageDraw.Draw(sheet)
    for k,i in enumerate(chosen):
        image=Image.open(output/f'page-{i+1:02}.png')
        image.thumbnail((240,350))
        x=(k%4)*250+(250-image.width)//2
        y=(k//4)*380+22
        sheet.paste(image,(x,y))
        draw.text(((k%4)*250+10,(k//4)*380+3),f'Page {i+1}',fill='black')
    sheet.save(output/f'contact-{start+1:02}.png')
result=dict(status='OK',pages=len(reader.pages),characters_per_page=counts,
            rendered_pages=len(pdf),authentic_capture_streams_unchanged=len(captures),
            visual_inspection='Rendus disponibles pour inspection ; ce champ seul ne prouve pas la lecture visuelle')
(root/'preuves/controles/verification_pdf.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
