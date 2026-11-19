"""Met en page le DAT Markdown avec ReportLab. Une section balisée correspond à une page."""
import argparse
import os
import re
from html import escape
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

PROJECT = Path(__file__).resolve().parents[2]
SOURCE = PROJECT/'travail'/'DAT_Retail_Intelligence_J1.md'
OUTPUT = PROJECT/'DAT_Retail_Intelligence_J1.pdf'
NAVY, TEAL = '#102A43','#086F69'
INK, MUTED = '#20384D','#436079'
PALE, LINE = '#F0F5F8','#D6E3E8'
WIDTH, HEIGHT = A4
MARGIN = 46
WRITABLE = WIDTH - 2*MARGIN
LANDSCAPE_PROOFS = {'Annexe A · P01', 'Annexe A · P03', 'Annexe A · P04', 'Annexe A · P05'}

def font_setup():
    fonts = Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'
    for name,filename in [('Segoe','segoeui.ttf'),('Segoe-Bold','segoeuib.ttf'),
                          ('Segoe-Italic','segoeuii.ttf'),('Segoe-BoldItalic','segoeuiz.ttf'),
                          ('Consolas','consola.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(fonts/filename)))
    pdfmetrics.registerFontFamily('Segoe', normal='Segoe', bold='Segoe-Bold', italic='Segoe-Italic', boldItalic='Segoe-BoldItalic')

def style(name, size, leading, color=INK, font='Segoe'):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                          alignment=TA_LEFT, textColor=colors.HexColor(color), allowWidows=0)

def inline(source):
    value = escape(source,quote=False).replace('\u202f','\u00a0').replace('\u200b','')
    value = re.sub(r'\[([^\]]+)\]\((https?://[^)]+|#p\d{2})\)',
                   r'<link color="#086F69" href="\2"><u>\1</u></link>',value)
    value = re.sub(r'\x60([^\x60]+)\x60',r'<font name="Consolas" color="#07544F">\1</font>', value)
    value = re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',value)
    return re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<i>\1</i>',value)

def table_rows(text):
    return [[v.strip().replace(r'\|','|') for v in re.split(r'(?<!\\)\|', l[1:-1])]
            for l in text.splitlines() if not re.fullmatch(r'[\s|:-]+',l)]

def page_blocks(text):
    return text.strip().split('\n\n')

def footer(pdf, n, total, page_width):
    pdf.setStrokeColor(LINE)
    pdf.line(MARGIN,39,page_width-MARGIN,39)
    pdf.setFillColor(MUTED)
    pdf.setFont('Segoe',8)
    pdf.drawString(MARGIN,24,'IPSSI  /  Retail Intelligence Platform  /  DAT Jour 1')
    pdf.drawRightString(page_width-MARGIN,24,f'{n:02d} / {total:02d}')

def cover(pdf, text, total):
    title, subtitle, uc, summary, school, date, authors = page_blocks(text)
    pdf.setFillColor(NAVY)
    pdf.rect(0,0,WIDTH,HEIGHT,stroke=0,fill=1)
    pdf.setFillColor('#123652')
    pdf.rect(WIDTH-134,0,134,HEIGHT,stroke=0,fill=1)
    pdf.setFillColor('#18827C')
    pdf.rect(MARGIN,HEIGHT-107,58,4,stroke=0,fill=1)
    pdf.setFillColor('#D8EBF0')
    pdf.setFont('Segoe-Bold',11)
    pdf.drawString(MARGIN,HEIGHT-88,'IPSSI  /  MASTÈRE DÉVELOPPEMENT, DATA & IA')
    blocks = [
        (uc,12,18,'#8FD7CE','Segoe-Bold',HEIGHT-223),
        (title[2:],49,55,'#FFFFFF','Segoe-Bold',HEIGHT-268),
        (subtitle[3:],22,29,'#E3F6F5','Segoe-Bold',HEIGHT-400),
        (summary,15,22,'#D8EBF0','Segoe',HEIGHT-462),
        (school,10,15,'#D8EBF0','Segoe',210),
        (date,10,15,'#D8EBF0','Segoe',185),
        (authors,11,16,'#FFFFFF','Segoe',143),
    ]
    for content,size,leading,color,font,top in blocks:
        p = Paragraph(inline(content),style('cover',size,leading,color,font))
        _,h = p.wrap(WRITABLE-32,HEIGHT)
        p.drawOn(pdf,MARGIN,top-h)
    pdf.setStrokeColor('#457287')
    pdf.line(MARGIN,67,WIDTH-MARGIN,67)
    pdf.setFillColor('#D8EBF0')
    pdf.setFont('Segoe',9)
    pdf.drawString(MARGIN,46,'Architecture de données  /  Jour 1')
    pdf.drawRightString(WIDTH-MARGIN,46,f'01 / {total:02d}')

def table_widths(header, writable):
    weights = {
        'Fichier': [.28,.18,.135,.15,.12,.135],
        'Profil · ID':[.20,.14,.25,.24,.17],
        'Pages':[.11,.62,.27],
        'ID · statut':[.21,.37,.42],
        'Table':[.22,.49,.29],
        'Référence':[.30,.18,.12,.14,.26],
        'Contrôle':[.33,.1675,.1675,.1675,.1675] if len(header)==5 else [.24,.39,.37],
        'Composant':[.19,.25,.24,.32],
        'Flux batch':[.17,.29,.28,.26],
        'Élément obligatoire TP1 §8.1':[.47,.14,.39],
        'Événement':[.19,.24,.24,.33],
        'Jeu Gold':[.25,.29,.46],
        'Type de décision':[.19,.29,.52],
        'Indicateur':[.23,.43,.17,.17],
        'Snapshot du 12/12/2005':[.235,.165,.165,.10,.205,.13],
        'Niveau de lecture':[.23,.30,.47],
        'Ce que montrent les fichiers':[.49,.51],
        'Objet d’analyse':[.25,.33,.42],
        'Périmètre':[.52,.12,.18,.18],
    }.get(header[0],[1/len(header)]*len(header))
    return [writable*w for w in weights]

def make_table(rows, compact, writable):
    widths=table_widths(rows[0],writable)
    sz,ld = (8.15,10.55) if compact else (9.05,12.3)
    styles=(style('th',sz,ld,'#FFFFFF','Segoe-Bold'),style('td',sz,ld))
    content=[[Paragraph(inline(x),styles[bool(i)]) for x in row] for i,row in enumerate(rows)]
    table=Table(content,colWidths=widths)
    padding = 4 if compact else 5
    table.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),padding),('BOTTOMPADDING',(0,0),(-1,-1),padding+1),
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor(NAVY)),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),(colors.white,colors.HexColor(PALE))),
        ('LINEBELOW',(0,-1),(-1,-1),0.6,colors.HexColor(LINE)),
    ]))
    return table

def render_page(pdf, category, text, n, total, page_size):
    page_width, page_height = page_size
    writable = page_width - 2*MARGIN
    proof = category.startswith('Annexe A · ')
    footer(pdf,n,total,page_width)
    pdf.setFillColor(TEAL)
    pdf.setFont('Segoe-Bold',9)
    pdf.drawString(MARGIN,page_height-45,category.upper())
    pdf.setStrokeColor(LINE)
    pdf.line(MARGIN,page_height-54,page_width-MARGIN,page_height-54)
    y = page_height-69
    title_style=style('title',27,33,NAVY,'Segoe-Bold')
    original_page = n - 3 if n >= 14 else n
    compact = n == 6 or (category != 'UC-01 · KPI'
                         and original_page in {3,12,14,18,20,21,23,26,29,31,33,34,35})
    body_style=style('body',10.1 if compact else 10.7,14.2 if compact else 15.55)
    sub_style=style('h2',13,17,TEAL,'Segoe-Bold')
    caption_style=style('caption',9.5,13.1,MUTED,'Segoe-Italic')

    def para(content, pstyle, gap=9, indent=0):
        nonlocal y
        p=Paragraph(inline(content),pstyle)
        _,h=p.wrap(writable-indent,page_height)
        p.drawOn(pdf,MARGIN+indent,y-h)
        y -= h+gap

    for block in page_blocks(text):
        if block.startswith('# '):
            para(block[2:],title_style,16)
        elif block == f'<a id="p{n:02d}"></a>':
            continue
        elif block.startswith('## '):
            para(block[3:],sub_style,6)
        elif block.startswith('|'):
            table=make_table(table_rows(block),compact,writable)
            _,h=table.wrap(writable,page_height)
            table.drawOn(pdf,MARGIN,y-h)
            y -= h+13
        elif block.startswith('!['):
            figure = re.fullmatch(r'!\[([^\]]+)\]\(([^)]+)\)',block)
            caption, relative=figure.groups()
            path=(SOURCE.parent/relative).resolve(strict=True)
            with Image.open(path) as img:
                width,height=img.size
            limit = 420 if proof else {22:363,24:348,25:214,32:338}.get(original_page,223)
            scale=min((writable-14)/width,limit/height)
            dw,dh=width*scale,height*scale
            pdf.setStrokeColor(LINE)
            pdf.roundRect(MARGIN,y-dh-12,writable,dh+12,4,stroke=1,fill=0)
            pdf.drawImage(str(path),(page_width-dw)/2,y-dh-6,width=dw,height=dh,mask='auto')
            y-=dh+19
            para(caption,caption_style,10)
        elif block.startswith('- ') or re.match(r'\d+\. ',block):
            for line in block.splitlines():
                formatted = '•  '+line[2:] if line.startswith('- ') else line
                para(formatted,body_style,4,6)
            y -= 5
        else:
            para(' '.join(block.splitlines()),body_style)
    if y < 47:
        raise ValueError(f'Page {n} déborde : bas du contenu à {y:.1f} pt.')
    return y

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output',type=Path,default=OUTPUT)
    args=cli.parse_args()
    font_setup()
    text=SOURCE.read_text(encoding='utf-8')
    parts=re.split(r'<!-- page: (.*?) -->\s*',text)[1:]
    pages=list(zip(parts[::2],parts[1::2],strict=True))
    assert len(pages)==44, len(pages)
    pdf=canvas.Canvas(str(args.output),pagesize=A4,pageCompression=1)
    pdf.setTitle('Retail Intelligence Platform — Dossier d’architecture technique J1')
    pdf.setAuthor('Kevin GREGOIRE')
    pdf.setSubject('IPSSI · UC-01 et UC-02 · Analyse et conception')
    for n,(category, text) in enumerate(pages,1):
        page_size = (HEIGHT, WIDTH) if category in LANDSCAPE_PROOFS else A4
        pdf.setPageSize(page_size)
        title=text.strip().splitlines()[0][2:]
        pdf.bookmarkPage(f'p{n:02d}')
        pdf.addOutlineEntry(title,f'p{n:02d}')
        if n == 1:
            cover(pdf,text,len(pages))
        else:
            y = render_page(pdf,category,text,n,len(pages),page_size)
            print(f'p{n:02d} • {title} • bas {y:.0f} pt')
        pdf.showPage()
    pdf.save()

if __name__ == '__main__':
    main()
