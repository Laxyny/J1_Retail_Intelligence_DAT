"""Vérification Windows : immutabilité et présence des onze livrables."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
project=root.parent
baseline=json.loads((root/'preuves/controles/empreintes_avant.json').read_text())
changed=[]
metadata_changed=[]
protected=0
for name,expected in baseline.items():
    path=project/name
    is_git_metadata='.git' in Path(name).parts
    protected+=not is_git_metadata
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        (metadata_changed if is_git_metadata else changed).append(name)
assert not changed,changed
required=['configuration/environnement.md','documentation/inventaire_sources.md',
          'notebooks/UC06_exploration.ipynb','documentation/regles_nettoyage.md',
          'scripts/transformation/transformer.py','donnees_produites/manifest.json',
          'preuves/controles/J3-P06-transformation.json','preuves/parquet/J3-P08-parquet.json',
          'documentation/rapport_qualite.md','README.md','preuves/index.md',
          'rapport/DAT_Retail_Intelligence_J3.md','rapport/DAT_Retail_Intelligence_J3.pdf',
          'verification/suivi_exigences.md','documentation/questions_recul.md']
for name in required:
    assert (root/name).is_file() and (root/name).stat().st_size>0,name
result=dict(status='OK',protected_files=protected,baseline_files=len(baseline),changed_files=changed,
            git_metadata_files=len(baseline)-protected,git_metadata_changed=metadata_changed,
            required_files=len(required),present_files=required)
(root/'preuves/controles/J3-P11-verification-fichiers.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
