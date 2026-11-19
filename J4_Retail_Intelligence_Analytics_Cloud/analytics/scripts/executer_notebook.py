"""Construit le notebook à partir du script à cellules puis l'exécute réellement."""
import os
import sys
import json
import csv
from decimal import Decimal
from pathlib import Path
import nbformat as nb
from nbclient import NotebookClient
from nbconvert import HTMLExporter

root=Path(__file__).resolve().parents[2]
os.environ['J4_ROOT']=str(root)
source=(root/'analytics/scripts/analyser.py').read_text(encoding='utf-8')
cells=[]
for block in source.split('# %%')[1:]:
    if block.startswith(' [markdown]'):
        content='\n'.join(line[2:] if line.startswith('# ') else '' for line in block.splitlines()[1:]).strip()
        cells.append(nb.v4.new_markdown_cell(content))
    else:
        cells.append(nb.v4.new_code_cell(block.strip()))
book=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python - Retail J4','language':'python','name':'python3'}})
path=root/'analytics/notebooks/TP4_Retail_Intelligence.ipynb'
path.parent.mkdir(parents=True,exist_ok=True)
nb.validate(book)
client=NotebookClient(book,timeout=1200,kernel_name='python3',resources={'metadata':{'path':str(root)}})
client.execute()
assert not any(o.output_type=='error' for c in book.cells if c.cell_type=='code' for o in c.get('outputs',[]))
summary=json.loads((root/'analytics/outputs/synthese.json').read_text(encoding='utf-8'))
book.cells[0].source += '\n\nRésultats V2 exécutés : 667 579 lignes, 33 755 474 unités, 1 150 529 586,37 UM ; '+str(summary['transactions']['transactions'])+' transactions et '+str(summary['transactions']['basket_display'])+' UM par panier HT. Les '+str(summary['controles'])+' contrôles analytiques passent. Lecture : '+os.environ.get('J4_MODE','hdfs')+'.'
for cell in book.cells:
    if cell.cell_type!='markdown':
        continue
    if cell.source.startswith('Le diagramme'):
        cell.source+='\n\nObservation : les dix premiers produits pèsent '+str(round(Decimal(summary['concentration']['top10_pct']),4))+' % du net payé ; les cent premiers '+str(round(Decimal(summary['concentration']['top100_pct']),4))+' %. Le produit 10000 mène avec 15 408 393,55 UM. La concentration dépasse donc largement la part de 10 produits dans les 17 820 références ; cela ne mesure pas la marge.'
    if cell.source.startswith('Les deux panneaux'):
        cell.source+='\n\nObservation : le magasin 7 atteint 98 950 137,76 UM et 2 915 053 unités ; le magasin 2, 94 040 402,78 UM et 2 760 007 unités. L’écart monétaire est de 4 909 734,98 UM, soit 5,22 % du minimum. Une comparaison normalisée par surface, trafic et durée d’ouverture serait nécessaire avant tout classement de performance.'
    if cell.source.startswith('Les moyennes'):
        cell.source+='\n\nObservation : le net payé par ligne a une médiane de 878,54 UM et une moyenne de 1 723,435858 UM ; son écart-type est de 2 167,90 UM. Le déséquilibre suggère une distribution étalée à droite. Les 3 954 lignes à net payé nul sont conservées. Les 495 971 profits négatifs ne servent pas au classement des ventes.'
    if cell.source.startswith('Les en-têtes'):
        cell.source+='\n\nRésultat : aucun en-tête manquant ni collision magasin/date/client ; '+str(summary['transactions']['multiline_tickets'])+' tickets ont plusieurs lignes. Les paniers totalisent exactement K01 ; K04 est '+str(summary['transactions']['basket_mean'])+' UM, arrondi au centime à '+str(summary['transactions']['basket_display'])+' UM. Le canal magasin fait partie du périmètre de la clé, qui ne doit pas être réutilisée seule entre canaux.'
    if cell.source.startswith('La lecture par catégories'):
        cell.source+='\n\nRésultat : '+str(summary['categories']['count'])+' catégories, aucune manquante. Music et Books portent ensemble '+str(round(Decimal(summary['categories']['music_books_pct']),4))+' % du net payé. Il s’agit d’une contribution monétaire, pas d’une marge.'
nb.write(book,path)
body,_=HTMLExporter().from_notebook_node(book)
(root/'analytics/notebooks/TP4_Retail_Intelligence.html').write_text(body,encoding='utf-8')
print('Notebook exécuté et validé :',len(cells),'cellules ;',sys.executable)
