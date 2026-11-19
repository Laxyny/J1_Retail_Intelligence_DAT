"""Reconstruit le dictionnaire ordinal .dat à partir du DDL Hive, annexe G."""
import argparse
import hashlib
import json
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = 'https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPCX-BB_v1.7.0.pdf'
TABLES = dict(zip(
    'customer customerAddress customerDemographics date householdDemographics income item '
    'promotion reason shipMode store time warehouse webSite webPage inventory storeSales '
    'storeReturns webSales webReturns marketPrices clickstreams reviews'.split(),
    'customer customer_address customer_demographics date_dim household_demographics income_band item '
    'promotion reason ship_mode store time_dim warehouse web_site web_page inventory store_sales '
    'store_returns web_sales web_returns item_marketprices web_clickstreams product_reviews'.split(),
    strict=True,
))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path, help='Copie locale du PDF officiel, sinon lecture depuis le TPC')
    args = parser.parse_args()
    if args.pdf:
        content = args.pdf.read_bytes()
    else:
        with urlopen(REFERENCE, timeout=30) as response:
            content = response.read()
    reader = PdfReader(BytesIO(content))
    assert len(reader.pages) == 139 and '1.7.0' in reader.pages[0].extract_text()
    pages = []
    for n in range(119, 137):
        page = reader.pages[n].extract_text()
        page = re.sub(r'^.*?Standard Specification Version 1\.7\.0\s+Page \d+ of\s+139\s*',
                      '', page, count=1, flags=re.S)
        pages.append(f'\n@@{n + 1}@@\n{page}')
    text = ''.join(pages)
    schema = {}
    pattern = (r'CREATE EXTERNAL TABLE\s+\$\{hiveconf:(\w+)TableName\}'
               r'\$\{hiveconf:temporaryTableSuffix\}(.*?)ROW FORMAT')
    for match in re.finditer(pattern, text, re.S):
        name, ddl = match.groups()
        start = re.findall(r'@@(\d+)@@', text[:match.start()])[-1]
        end = re.findall(r'@@(\d+)@@', text[:match.end()])[-1]
        ddl = re.sub(r'@@\d+@@', '', ddl).strip()
        assert ddl.startswith('(') and ddl.endswith(')'), (name, ddl[:80])
        ddl = re.sub(r'--[^\n]*', '', ddl[1:-1])
        parts = re.split(r',(?![^()]*\))', ddl)
        columns = []
        for part in parts:
            field = re.fullmatch(r'\s*(\w+)\s+(bigint|int|string|decimal\(\s*\d+\s*,\s*\d+\s*\))\s*', part)
            assert field, (name, part)
            columns.append([field[1], field[2].replace(' ', '')])
        schema[TABLES[name]] = {'pages': start if start == end else f'{start}-{end}', 'columns': columns}
    assert set(schema) == set(TABLES.values()) and len(schema['store_sales']['columns']) == 23
    output = ROOT / 'preuves' / 'resultats' / 'schema_tpc.json'
    output.write_text(json.dumps(schema, indent=2), encoding='utf-8')
    trace = {
        'date':datetime.now().astimezone().isoformat(timespec='seconds'),
        'statut':'succès','reference':REFERENCE,'sha256_pdf':hashlib.sha256(content).hexdigest(),
        'octets_pdf':len(content),'pages_ddl':'120–137','tables':len(schema),
        'commande_equivalente':'python -B preuves/scripts/schema_tpc.py',
    }
    (output.parent/'00_schema_execution.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{len(schema)} tables extraites de l’annexe G : {output.name}')

if __name__ == '__main__':
    main()
