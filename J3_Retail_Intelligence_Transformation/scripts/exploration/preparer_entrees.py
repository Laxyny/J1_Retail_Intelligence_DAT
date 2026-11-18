"""Copie immuable de deux sources vers un nouveau lot Raw J3 ; jamais de -f."""
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from uc06 import ROOT, save

run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
base = '/retail-lake/raw/j3/'+run_id
inventory = json.loads((ROOT/'preuves/controles/inventaire_python.json').read_text())['sources']
config = {'run_id': run_id, 'fs': 'hdfs://hdfs:9000', 'sources': {},
          'silver': f'hdfs://hdfs:9000/retail-lake/silver/j3/{run_id}',
          'gold': f'hdfs://hdfs:9000/retail-lake/gold/j3/{run_id}'}
for table in ['store_sales', 'item']:
    local = '/sources/data/'+table+'/'+table+'.dat'
    destination = base+'/'+table+'.dat'
    subprocess.run(['hdfs','dfs','-fs',config['fs'],'-mkdir','-p',base],check=True)
    subprocess.run(['hdfs','dfs','-fs',config['fs'],'-put',local,destination],check=True)
    content = subprocess.check_output(['hdfs','dfs','-fs',config['fs'],'-cat',destination])
    expected = inventory['data/'+table]['sha256']
    assert hashlib.sha256(content).hexdigest() == expected
    config['sources'][table] = {'local': local, 'hdfs': config['fs']+destination,
                                'sha256': expected, 'batch': 'initial'}
    print(table, len(content), expected, flush=True)
save('configuration/parametres/execution.json',config)
save('preuves/controles/J3-P03-entrees-hdfs.json',config)
print(run_id)
