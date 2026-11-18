"""Revalide le dictionnaire J1 avec le DDL officiel de l'Annexe G, sans écrire dans J1."""
import hashlib
import json
import re
from pathlib import Path
from urllib.request import urlopen
from pypdf import PdfReader

root=Path(__file__).resolve().parents[1]
url='https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPCX-BB_v1.7.0.pdf'
path=root/'preuves/consignes/TPCX-BB_v1.7.0.pdf'
if not path.exists():
    path.write_bytes(urlopen(url,timeout=30).read())
content=path.read_bytes()
reader=PdfReader(path)
assert len(reader.pages)==139
schema=json.loads((root/'configuration/parametres/schemas.json').read_text())
pages=[]
for i in range(119,137):
    text=reader.pages[i].extract_text()
    text=re.sub(r'^.*?Standard Specification Version 1\.7\.0\s+Page \d+ of\s+139\s*','',text,count=1,flags=re.S)
    pages.append(text)
text='\n'.join(pages)
for tag,name in [('storeSales','store_sales'),('item','item')]:
    pattern=r'CREATE EXTERNAL TABLE\s+\$\{hiveconf:'+tag+r'TableName\}\s*\$\{hiveconf:temporaryTableSuffix\}(.*?)ROW FORMAT'
    ddl=re.search(pattern,text,re.S)[1]
    actual=re.findall(r'\b(\w+)\s+(bigint|int|string|decimal\(\s*\d+\s*,\s*\d+\s*\))',ddl)
    actual=[[n,t.replace(' ','')] for n,t in actual]
    assert actual==schema[name]['columns'],(name,actual)
    print(name,'Annexe G : schéma confirmé',len(actual))
(root/'preuves/controles/schema_reference.json').write_text(json.dumps(dict(url=url,sha256=hashlib.sha256(content).hexdigest(),pages=139,verified_tables=['store_sales','item'],result='OK'),indent=2),encoding='utf-8')
