"""Rapport académique blanc/noir : conversion des sections Markdown et captures réelles."""
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, CondPageBreak, Image

ROOT=Path(__file__).resolve().parents[1]
FONT_DIR=Path('C:/Windows/Fonts')


def main():
    pdfmetrics.registerFont(TTFont('Traditional',str(FONT_DIR/'times.ttf')))
    pdfmetrics.registerFont(TTFont('TraditionalBold',str(FONT_DIR/'timesbd.ttf')))
    pdfmetrics.registerFontFamily('Traditional',normal='Traditional',bold='TraditionalBold')
    styles={
        'body':ParagraphStyle('body',fontName='Traditional',fontSize=10.5,leading=14,spaceAfter=7),
        'h1':ParagraphStyle('h1',fontName='TraditionalBold',fontSize=16,leading=20,spaceAfter=13,keepWithNext=True),
        'h2':ParagraphStyle('h2',fontName='TraditionalBold',fontSize=12,leading=16,spaceBefore=9,spaceAfter=7,keepWithNext=True),
        'cell':ParagraphStyle('cell',fontName='Traditional',fontSize=9,leading=11.5,spaceAfter=0),
        'code':ParagraphStyle('code',fontName='Courier',fontSize=8,leading=10,spaceAfter=5),
        'caption':ParagraphStyle('caption',fontName='Traditional',fontSize=9,leading=12,spaceAfter=8),
    }
    def inline(text):
        text=html.escape(text).replace('`','')
        text=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',text)
        text=re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<link href="\2" color="black">\1</link>',text)
        return text
    width=A4[0]-96
    story=[]
    sections=json.loads((ROOT/'rapport/sections.json').read_text(encoding='utf-8'))
    for section_number,section in enumerate(sections):
        if section_number==1:
            story.append(PageBreak())
        elif section_number:
            story.extend([Spacer(1,12),CondPageBreak(180)])
        lines=section.splitlines()
        i=0
        while i<len(lines):
            line=lines[i].strip()
            if not line:
                i+=1;continue
            if line.startswith('|'):
                rows=[]
                while i<len(lines) and lines[i].strip().startswith('|'):
                    row=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                    if not all(re.fullmatch(r':?-+:?',c) for c in row):
                        rows.append([Paragraph(inline(c),styles['cell']) for c in row])
                    i+=1
                n=len(rows[0])
                if n==2: widths=[width*.29,width*.71]
                elif n==3: widths=[width*.19,width*.34,width*.47]
                elif n==4: widths=[width*.23,width*.25,width*.26,width*.26]
                else: widths=[width/n]*n
                tbl=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
                tbl.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                    ('LINEABOVE',(0,0),(-1,0),.7,colors.black),('LINEBELOW',(0,0),(-1,0),.7,colors.black),
                    ('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#bbbbbb')),
                    ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
                    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
                story.extend([tbl,Spacer(1,9)])
                continue
            if line.startswith('```'):
                i+=1
                while i<len(lines) and not lines[i].startswith('```'):
                    for part in textwrap.wrap(lines[i],width=95,replace_whitespace=False) or [' ']:
                        story.append(Paragraph(html.escape(part),styles['code']))
                    i+=1
                i+=1;continue
            if line.startswith('#'):
                level=len(line)-len(line.lstrip('#'))
                story.append(Paragraph(inline(line.lstrip('#').strip()),styles['h1' if level==1 else 'h2']))
            else:
                paragraph=[line]
                while i+1<len(lines) and lines[i+1].strip() and not lines[i+1].lstrip().startswith(('#','|','- ','```')):
                    i+=1;paragraph.append(lines[i].strip())
                story.append(Paragraph(inline(' '.join(paragraph)),styles['body']))
            i+=1
    captures=[('J3-P01-hdfs.jpg','J3-P01 - Interface réelle du NameNode : Hadoop 3.5.0 actif et mode sûr désactivé.'),
              ('J3-P04-notebook.jpg','J3-P04 - Export HTML du notebook réellement exécuté : Spark 3.5.7 et Python 3.12.3.'),
              ('J3-P05-bilan.jpg','J3-P05 - Bilan réel du notebook : clés, cardinalité et anomalies conservées.')]
    for name,caption in captures:
        path=ROOT/'preuves/captures'/name
        assert path.is_file(),path
        story.append(PageBreak())
        story.append(Paragraph('Annexe - Preuve visuelle',styles['h1']))
        story.append(Paragraph(caption,styles['caption']))
        image=Image(str(path))
        scale=min(width/image.imageWidth,650/image.imageHeight)
        image.drawWidth=image.imageWidth*scale
        image.drawHeight=image.imageHeight*scale
        story.append(image)
        story.append(Spacer(1,9))
        story.append(Paragraph('Capture authentique du navigateur, conservée sans reconstruction de terminal. Les résultats numériques détaillés et les commandes sont disponibles dans le registre des preuves.',styles['caption']))
    def footer(canvas,doc):
        canvas.saveState()
        canvas.setFont('Traditional',8.5)
        canvas.drawString(48,24,'Retail Intelligence Platform - Jour 3 - UC-06')
        canvas.drawRightString(A4[0]-48,24,str(doc.page))
        canvas.restoreState()
    pdf=ROOT/'rapport/DAT_Retail_Intelligence_J3.pdf'
    doc=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=42,bottomMargin=42,
                          title='Retail Intelligence Platform - Jour 3 - UC-06',author='Kevin GREGOIRE')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(pdf)


if __name__=='__main__':
    main()
