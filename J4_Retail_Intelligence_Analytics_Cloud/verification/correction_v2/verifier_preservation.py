"""Compare les preuves avant/après V2 et les fichiers UC-07 à la sauvegarde initiale."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def main():
    before=load('preuves/environnement/protection_v2_avant.json')
    after=load('preuves/environnement/protection_apres.json')
    assert before==after
    assert (ROOT/'preuves/environnement/hdfs_v2_avant.txt').read_bytes()==(ROOT/'preuves/environnement/hdfs_apres.txt').read_bytes()
    backup=Path(load('verification/correction_v2/sauvegarde.json')['path'])
    changes=[]
    for p in (backup/'cloud').rglob('*'):
        if p.is_file() and p.read_bytes()!=(ROOT/p.relative_to(backup)).read_bytes():
            changes.append(p.relative_to(backup).as_posix())
    assert changes==['cloud/simulation/scenario_non_execute.md'],changes
    old=(backup/changes[0]).read_text(encoding='utf-8')
    new=(ROOT/changes[0]).read_text(encoding='utf-8')
    assert new==old.replace('ne contient que trois agrégats','ne contient que des agrégats')
    initial=load('verification/correction_v2/sauvegarde.json')['files']
    changed=[name for name,digest in initial.items() if (ROOT/name).is_file() and not name.startswith(('A_REMETTRE_J4','verification/pdf/')) and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
    result={'all_passed':True,'previous_files_unchanged':len(before),'hdfs_listing_unchanged':True,
            'cloud_only_reference_changed':changes,'cloud_architecture_security_and_diagrams_unchanged':True,
            'backup_path':str(backup),'changed_content_files':changed,
            'limits':'Les métadonnées internes HDFS évoluent au démarrage ; listings de fichiers et empreintes locales sont comparés.'}
    (ROOT/'verification/correction_v2/preservation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(len(before),'fichiers antérieurs identiques ; HDFS inchangé ; UC-07 conservé sauf une référence devenue périmée.')

if __name__=='__main__':
    main()
