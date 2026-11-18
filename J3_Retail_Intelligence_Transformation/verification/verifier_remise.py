"""Contrôle autonome du dossier reçu à partir de MANIFESTE_REMISE.json."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'MANIFESTE_REMISE.json').read_text(encoding='utf-8'))
for relative,expected in manifest['files'].items():
    path=(root/relative).resolve()
    assert path.is_relative_to(root.resolve()),relative
    assert path.is_file() and path.stat().st_size==expected['bytes'],relative
    with path.open('rb') as stream:
        assert hashlib.file_digest(stream,'sha256').hexdigest()==expected['sha256'],relative
export=json.loads((root/'donnees_produites/verification_export/manifeste_export.json').read_text(encoding='utf-8'))
assert export['lot']==manifest['lot'] and export['status']=='OK'
for data in export['datasets'].values():
    for info in data['files'].values():
        assert manifest['files'][info['local_relative']]['sha256']==info['sha256_windows']==info['sha256_hdfs']
print('DOSSIER INTEGRE :',len(manifest['files']),'fichiers ; 3 jeux ; 9 SHA-256 HDFS/Windows concordants')
