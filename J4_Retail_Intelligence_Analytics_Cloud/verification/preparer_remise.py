"""Vérifie une remise candidate V2 puis remplace la publication en conservant l'ancienne."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from verifier_remise import verify

ROOT=Path(__file__).resolve().parents[1]

def main():
    validation=json.loads((ROOT/'verification/controle_final.json').read_text(encoding='utf-8'))
    assert validation['all_passed'] and validation['livrables_verifies']==11 and validation['version']=='J4 V2'
    preservation=json.loads((ROOT/'verification/correction_v2/preservation.json').read_text(encoding='utf-8'))
    assert preservation['all_passed']
    assert '25 pages' in (ROOT/'verification/revue_visuelle.md').read_text(encoding='utf-8')
    candidate=ROOT/'verification/correction_v2/candidate'
    assert not candidate.exists(), 'Conserver la candidate existante pour diagnostic'
    candidate.mkdir()
    target=candidate/'A_REMETTRE_J4';archive=candidate/'A_REMETTRE_J4.zip'
    target.mkdir()
    for name in ['README.md','configuration','analytics','documentation','cloud','preuves','rapport']:
        p=ROOT/name
        if p.is_dir():
            shutil.copytree(p,target/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        else:
            shutil.copy2(p,target/name)
    (target/'verification').mkdir()
    for name in ['suivi_exigences.md','controle_final.json','revue_visuelle.md','verifier_livrables.py','verifier_remise.py','preparer_remise.py','TP4_texte_extrait.txt']:
        shutil.copy2(ROOT/'verification'/name,target/'verification'/name)
    correction=target/'verification/correction_v2'
    correction.mkdir()
    for name in ['journal_changements.md','sauvegarde.json','preservation.json','validation_calculs.json','verifier_preservation.py']:
        shutil.copy2(ROOT/'verification/correction_v2'/name,correction/name)
    files={p.relative_to(target).as_posix():{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(target.rglob('*')) if p.is_file()}
    assert not any(Path(n).suffix.lower() in ['.dat','.parquet'] for n in files)
    manifest={'version':'J4 V2','batch_j3':'20261118T113628Z-243a5fb5-r3','files':files}
    (target/'MANIFESTE_REMISE.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    verify(target)
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(target.rglob('*')):
            if p.is_file():
                z.write(p,Path(target.name)/p.relative_to(target))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        expected={(Path(target.name)/p.relative_to(target)).as_posix():p for p in target.rglob('*') if p.is_file()}
        assert set(z.namelist())==set(expected)
        for name,p in expected.items():
            assert hashlib.sha256(z.read(name)).digest()==hashlib.sha256(p.read_bytes()).digest(),name
    result={'version':'J4 V2','statut':'OK','files':len(files)+1,'archive_bytes':archive.stat().st_size,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'crc_checked':True,'sha256_all_entries':True,'all_names_checked':True,'no_raw_or_parquet':True}
    backup=Path(preservation['backup_path']).resolve()/'publication_remplacee'
    public_target=ROOT/'A_REMETTRE_J4';public_archive=ROOT/'A_REMETTRE_J4.zip'
    # Tous les déplacements restent dans le projet autorisé ; aucune destination existante n'est écrasée.
    assert ROOT.name=='J4_Retail_Intelligence_Analytics_Cloud'
    assert backup.is_relative_to((ROOT.parent/'Sauvegardes_J4').resolve())
    assert target.resolve().is_relative_to(ROOT) and archive.resolve().is_relative_to(ROOT)
    assert not backup.exists()
    backup.mkdir()
    if public_target.exists():
        public_target.rename(backup/public_target.name)
    if public_archive.exists():
        public_archive.rename(backup/public_archive.name)
    target.rename(public_target)
    archive.rename(public_archive)
    verify(public_target)
    assert hashlib.sha256(public_archive.read_bytes()).hexdigest()==result['archive_sha256']
    result['old_publication_saved_to']=str(backup)
    result['published_folder']=str(public_target)
    result['published_zip']=str(public_archive)
    (ROOT/'verification/integrite_archive.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
