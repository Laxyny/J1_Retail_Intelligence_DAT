"""Vérifie le manifeste d'une remise sans dépendance externe."""
import hashlib
import json
from pathlib import Path

def verify(root):
    manifest=json.loads((root/'MANIFESTE_REMISE.json').read_text(encoding='utf-8'))
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='MANIFESTE_REMISE.json'}
    assert actual==set(manifest['files']), 'Fichier ajouté ou manquant'
    for name,record in manifest['files'].items():
        p=root/name
        assert p.stat().st_size==record['bytes'],name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'],name
    print('Intégrité OK :',len(actual),'fichiers')
    return len(actual)

if __name__=='__main__':
    import sys
    verify(Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
