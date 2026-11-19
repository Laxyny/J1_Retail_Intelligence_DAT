"""Rapport académique blanc et noir, images réelles et tableaux qui se répartissent sur les pages."""
import html
import json
import re
import textwrap
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, CondPageBreak, Image, PageBreak
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
FONT=Path('C:/Windows/Fonts')

def main():
    if FONT.exists():
        pdfmetrics.registerFont(TTFont('Academic',str(FONT/'times.ttf')))
        pdfmetrics.registerFont(TTFont('AcademicBold',str(FONT/'timesbd.ttf')))
        pdfmetrics.registerFontFamily('Academic',normal='Academic',bold='AcademicBold')
        normal,bold='Academic','AcademicBold'
    else:
        normal,bold='Times-Roman','Times-Bold'
    styles={
        'body':ParagraphStyle('body',fontName=normal,fontSize=10.5,leading=14,spaceAfter=7),
        'h1':ParagraphStyle('h1',fontName=bold,fontSize=16,leading=19,spaceBefore=8,spaceAfter=12,keepWithNext=True),
        'h2':ParagraphStyle('h2',fontName=bold,fontSize=12,leading=15,spaceBefore=9,spaceAfter=7,keepWithNext=True),
        'cell':ParagraphStyle('cell',fontName=normal,fontSize=8.5,leading=11),
        'headcell':ParagraphStyle('headcell',fontName=bold,fontSize=8.5,leading=11),
        'code':ParagraphStyle('code',fontName='Courier',fontSize=8,leading=10,spaceAfter=2)}
    def inline(text):
        text=html.escape(text).replace('`','')
        text=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',text)
        text=re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<link href="\2" color="black">\1</link>',text)
        return text
    width=A4[0]-96
    story=[]
    sections=json.loads((ROOT/'rapport/sections.json').read_text(encoding='utf-8'))
    for index,section in enumerate(sections):
        if index and section.startswith(('# Environnement réellement utilisé','# Visualisation ','# Schémas d’architecture','# Justification du parcours B','# Les quatorze questions','# Schémas lus par Spark')):
            story.append(PageBreak())
        elif index:
            story.extend([Spacer(1,10),CondPageBreak(140)])
        lines=section.splitlines(); i=0
        while i<len(lines):
            line=lines[i].strip()
            if not line:
                i+=1; continue
            if line.startswith('!['):
                match=re.fullmatch(r'!\[([^]]*)\]\(([^)]+)\)',line)
                assert match,line
                p=(ROOT/'rapport'/match[2]).resolve()
                assert p.is_file(),p
                im=Image(str(p))
                scale=min(width/im.imageWidth,590/im.imageHeight)
                im.drawWidth=im.imageWidth*scale; im.drawHeight=im.imageHeight*scale
                story.extend([im,Spacer(1,9),Paragraph(inline(match[1]),styles['cell']),Spacer(1,8)])
                i+=1;continue
            if line.startswith('|'):
                rows=[]
                while i<len(lines) and lines[i].strip().startswith('|'):
                    cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                    if not all(re.fullmatch(r':?-+:?',c) for c in cells):
                        rows.append([Paragraph(inline(c),styles['headcell' if not rows else 'cell']) for c in cells])
                    i+=1
                n=len(rows[0]); assert all(len(r)==n for r in rows)
                widths=([width*.28,width*.72] if n==2 else [width/n]*n)
                tbl=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
                tbl.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEABOVE',(0,0),(-1,0),.7,colors.black),
                    ('LINEBELOW',(0,0),(-1,0),.7,colors.black),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#bbbbbb')),
                    ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
                    ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
                story.extend([tbl,Spacer(1,9)]);continue
            if line.startswith('```'):
                i+=1
                while i<len(lines) and not lines[i].strip().startswith('```'):
                    for part in textwrap.wrap(lines[i].strip(),width=94,replace_whitespace=False) or [' ']:
                        story.append(Paragraph(html.escape(part),styles['code']))
                    i+=1
                i+=1;continue
            if line.startswith('#'):
                level=len(line)-len(line.lstrip('#'))
                story.append(Paragraph(inline(line.lstrip('#').strip()),styles['h1' if level==1 else 'h2']))
                i+=1;continue
            paragraphs=[line]
            while i+1<len(lines) and lines[i+1].strip() and not lines[i+1].lstrip().startswith(('#','|','```','![')):
                i+=1;paragraphs.append(lines[i].strip())
            story.append(Paragraph(inline(' '.join(paragraphs)),styles['body']))
            i+=1
    output=ROOT/'rapport/DAT_Retail_Intelligence_J4.pdf'
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont(normal,8.5)
        canvas.drawString(48,25,'Retail Intelligence Platform - Jour 4 - UC-08 / UC-07 - Parcours B')
        canvas.drawRightString(A4[0]-48,25,str(doc.page));canvas.restoreState()
    document=SimpleDocTemplate(str(output),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=42,bottomMargin=43,
        title='Retail Intelligence Platform - Jour 4',author='Kevin GREGOIRE',pageCompression=1)
    document.build(story,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(output)
    text='\n'.join(p.extract_text() for p in reader.pages)
    assert '1 150 529 586,37' in text
    assert 'Architecture proposée' in text
    qa=ROOT/'verification/pdf';qa.mkdir(parents=True,exist_ok=True)
    pdf=pdfium.PdfDocument(str(output))
    for i,page in enumerate(pdf):
        page.render(scale=1.35).to_pil().save(qa/f'page-{i+1:02}.png')
    pdf.close()
    (qa/'texte_extrait.txt').write_text(text,encoding='utf-8')
    print('PDF généré et rendu :',len(reader.pages),'pages')

if __name__=='__main__':
    main()
