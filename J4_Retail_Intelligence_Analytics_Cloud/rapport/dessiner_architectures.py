"""Schémas vectoriels reproductibles ; aucune image de portail reconstruite."""
from pathlib import Path
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics import renderPDF, renderSVG
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cloud/architecture'
OUT.mkdir(parents=True,exist_ok=True)

def diagram(name,title,boxes,arrows,notes):
    d=Drawing(700,440)
    d.add(Rect(0,0,700,440,fillColor=None,strokeColor=None))
    d.add(String(350,417,title,textAnchor='middle',fontName='Helvetica-Bold',fontSize=16))
    for key,(x,y,lines) in boxes.items():
        d.add(Rect(x,y,200,75,fillColor=None,strokeWidth=1))
        for i,line in enumerate(lines):
            d.add(String(x+100,y+54-i*15,line,textAnchor='middle',fontName='Helvetica',fontSize=11))
    for start,end in arrows:
        sx,sy,_=boxes[start]; ex,ey,_=boxes[end]
        if sy==ey:
            x1,y1,x2,y2=(sx+200,sy+37.5,ex,ey+37.5) if ex>sx else (sx,sy+37.5,ex+200,ey+37.5)
        else:
            x1,y1,x2,y2=sx+100,sy,ex+100,ey+75
        d.add(Line(x1,y1,x2,y2,strokeWidth=1))
        if y1==y2:
            direction=1 if x2>x1 else -1
            d.add(Polygon([x2,y2,x2-6*direction,y2+3,x2-6*direction,y2-3],fillColor=None))
        else:
            d.add(Polygon([x2,y2,x2-3,y2+6,x2+3,y2+6],fillColor=None))
    for i,line in enumerate(notes):
        d.add(String(20,55-i*15,line,fontName='Helvetica',fontSize=10))
    renderSVG.drawToFile(d,str(OUT/(name+'.svg')))
    renderPDF.drawToFile(d,str(OUT/(name+'.pdf')))
    pdf=pdfium.PdfDocument(str(OUT/(name+'.pdf')))
    pdf[0].render(scale=2.6).to_pil().save(OUT/(name+'.png'))
    pdf.close()

diagram('architecture_locale','Architecture locale réellement utilisée',{
    'source':(20,305,['Sources TPCx-BB','DAT initiaux','Fichiers Windows préservés']),
    'raw':(250,305,['HDFS Raw - Jour 3','Copie manuelle contrôlée','NameNode et DataNode J2']),
    'spark3':(480,305,['PySpark - Jour 3','Typage et contrôles','Traitements déjà terminés']),
    'lake':(480,185,['HDFS Silver / Gold','Parquet Snappy du lot r3','Résultats J3 conservés']),
    'spark4':(250,185,['PySpark - Jour 4','Lecture HDFS réelle','KPI, statistiques, contrôles']),
    'viz':(20,185,['Petits agrégats Pandas','Notebook et Matplotlib','CSV, JSON et deux PNG']),
    'history':(20,85,['Historique J2 distinct','NiFi : reason.dat vers HDFS','NiFi reste arrêté au J4'])},
    [('source','raw'),('raw','spark3'),('spark3','lake'),('lake','spark4'),('spark4','viz')],
    ['Docker Desktop / WSL2 ; Spark local[2] ; volumes HDFS existants, réplication 1.',
     'J4 écrit seulement ses résultats analytiques ; aucune transformation J3 relancée.',
     'Schéma documentaire fondé sur les exécutions et manifestes, sans service Azure.'])

diagram('architecture_azure','Architecture proposée - Aucun service Azure déployé',{
    'source':(20,305,['Sources TPCx-BB','Fichiers autorisés uniquement','Arrivées identifiées par lot']),
    'adf':(250,305,['Azure Data Factory envisagé','Copie / orchestration','Identité de service dédiée']),
    'bronze':(480,305,['ADLS Gen2 - Bronze','Compte StorageV2 avec HNS','Conteneur privé']),
    'spark':(480,185,['Synapse Spark envisagé','Bronze vers Silver / Gold','Contrôles avant publication']),
    'gold':(250,185,['ADLS Silver / Gold','store_sales, item','Produits et agrégats KPI']),
    'sql':(20,185,['SQL / restitution envisagés','Synapse SQL selon besoin','Exports ou outil BI autorisé']),
    'identity':(20,85,['Sécurité transversale','Entra ID ; RBAC ; ACL','Réseau privé et journaux']),
    'control':(250,85,['Pilotage proposé','Abonnement / quotas / budget','Groupe de ressources dédié']),
    'studio':(480,85,['Synapse Studio envisagé','Interface workspace','Notebooks et requêtes'])},
    [('source','adf'),('adf','bronze'),('bronze','spark'),('spark','gold'),('gold','sql')],
    ['Les flèches indiquent des flux proposés ; aucune création ni requête Azure exécutée.',
     'ADLS conserve ; ADF orchestre ; Spark calcule ; SQL explore les résultats.',
     'Identités et permissions seraient testées après un déploiement autorisé.'])
print('Deux schémas produits en SVG, PDF et PNG.')
