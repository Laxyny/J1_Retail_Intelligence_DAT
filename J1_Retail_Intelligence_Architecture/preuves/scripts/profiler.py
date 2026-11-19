"""Inventaire exhaustif des fichiers et profil par colonne, sans modifier la source."""
import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from time import perf_counter

PROJECT = Path(__file__).resolve().parents[2]
OUT = PROJECT / 'preuves' / 'resultats'
SAMPLE = 20_000
LOTS = ('data', 'data_refresh')

def source_path(explicit=None):
    if explicit:
        return explicit.resolve(strict=True)
    candidates = [p.parent for p in PROJECT.parent.glob('*/**/data')
                  if p.is_dir() and (p.parent / 'data_refresh').is_dir()
                  and p.parent != PROJECT]
    if len(candidates) != 1:
        raise SystemExit(f'Racines candidates : {candidates}. Préciser --source.')
    return candidates[0]

def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--source', type=Path, help='Dossier parent de data et data_refresh')
    return cli

def csv_out(name, rows):
    if not rows:
        return
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(rows)

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def payload(line):
    return line[:-2] if line.endswith(b'\r\n') else line.removesuffix(b'\n')

def rule(typ):
    if typ == 'string':
        return lambda value: True
    if typ == 'bigint':
        return lambda value: value.removeprefix(b'-').isdigit() and -(2**63) <= int(value) < 2**63
    if typ == 'int':
        return lambda value: value.removeprefix(b'-').isdigit() and -(2**31) <= int(value) < 2**31
    precision, scale = map(int, re.findall(r'\d+', typ))
    pattern = re.compile(rb'-?\d{1,' + str(precision-scale).encode() + rb'}(?:\.\d{1,' + str(scale).encode() + rb'})?')
    return pattern.fullmatch

def mask(value):
    if not value:
        return '∅'
    if value.removeprefix(b'-').isdigit():
        return f'<entier {len(value)} oct.>'
    if re.fullmatch(rb'\d{4}-\d{2}-\d{2}', value):
        return '<AAAA-MM-JJ>'
    if re.fullmatch(rb'-?\d+\.\d+', value):
        return '<décimal>'
    return f'<texte {len(value)} oct.>'

def profile(path, source, ddl):
    widths, ends, newline, types = Counter(), Counter(), Counter(), []
    blanks = non_ascii = invalid_utf8 = 0
    seen, previews, audit_meta = set(), [], {}
    repeated = sampled = 0
    cols = ddl['columns'] if ddl else []
    missing, markers, failures = ([0] * len(cols) for _ in range(3))
    validators = [rule(t) for _, t in cols]
    sample_min, sample_max = [None]*len(cols), [None]*len(cols)
    dimensions_wrong = Counter()
    with path.open('rb') as stream:
        for idx, line in enumerate(stream, 1):
            newline['CRLF' if line.endswith(b'\r\n') else 'LF' if line.endswith(b'\n') else 'sans LF final'] += 1
            raw = payload(line)
            if not raw.isascii():
                non_ascii += 1
                try:
                    raw.decode('utf-8')
                except UnicodeDecodeError:
                    invalid_utf8 += 1
            if not raw:
                blanks += 1
            if ddl:
                fields = raw.split(b'|')
                ends[raw.endswith(b'|')] += 1
            else:
                fields = next(csv.reader([raw.decode('utf-8-sig', errors='replace')], strict=True)) if raw else []
                if idx == 2:
                    audit_meta['header'] = fields
                if idx == 3:
                    audit_meta['summary'] = dict(zip(audit_meta['header'], fields))
                if idx > 3:
                    dimensions_wrong[len(fields)] += 1
            widths[len(fields)] += 1
            if ddl and len(fields) == len(cols):
                for pos, value in enumerate(fields):
                    if value == b'':
                        missing[pos] += 1
                    elif value in (b'\\N', b'NULL'):
                        markers[pos] += 1
                if sampled < SAMPLE:
                    for pos, (value, validator) in enumerate(zip(fields, validators)):
                        if value in (b'', b'\\N', b'NULL'):
                            continue
                        if not validator(value):
                            failures[pos] += 1
                            continue
                        if cols[pos][1] in ('int','bigint'):
                            num = int(value)
                            sample_min[pos] = num if sample_min[pos] is None else min(sample_min[pos], num)
                            sample_max[pos] = num if sample_max[pos] is None else max(sample_max[pos], num)
                    sampled += 1
            if idx <= SAMPLE:
                if raw in seen:
                    repeated += 1
                seen.add(raw)
            if idx <= 3:
                previews.append({'ligne': idx, 'champs': len(fields),
                                 'structure': ' | '.join(map(mask, fields)) if ddl else f'<audit : {len(fields)} champs>'})
    row_total = sum(widths.values())
    good = widths[len(cols)] if ddl else None
    relative = path.relative_to(source).as_posix()
    rec = dict(lot=path.parents[1].name, fichier=relative, table=path.stem, octets=path.stat().st_size,
               extension=path.suffix, format='texte tabulé par pipe, sans en-tête' if ddl else 'rapport texte composite à sections',
               separateur='|' if ddl else ', sur les sections tabulaires',
               encodage='ASCII (compatible UTF-8)' if not non_ascii else
                        'UTF-8 valide' if not invalid_utf8 else 'UTF-8 invalide sur certaines lignes',
               lignes=row_total, largeurs=dict(sorted(widths.items())), attendus=len(cols) if ddl else None,
               largeur_hors_ddl=row_total-good if ddl else None, lignes_vides=blanks,
               fins_ligne=dict(newline), fin_pipe=ends[True], lignes_non_ascii=non_ascii,
               erreurs_utf8=invalid_utf8, vides_bruts=sum(missing), marqueurs_litteraux=sum(markers),
               echantillon_types=sampled, incompatibilites_types=sum(failures),
               echantillon_doublons=min(SAMPLE,row_total), lignes_repetitions_exactes=repeated,
               homologue=(source / ('data_refresh' if path.parents[1].name == 'data' else 'data') /
                          path.parent.name / path.name).is_file(),
               sha256=digest(path))
    for i,(name,typ) in enumerate(cols):
        types.append(dict(lot=rec['lot'], table=path.stem, position=i+1, colonne=name,
                          type_ddl=typ, pages_ddl=ddl['pages'], lignes_conformes=good,
                          vides=missing[i], marqueurs_litteraux=markers[i],
                          echantillon_types=sampled, echecs_echantillon=failures[i],
                          min_entier_echantillon=sample_min[i], max_entier_echantillon=sample_max[i]))
    if audit_meta:
        audit_meta['sections_apres_resume'] = dict(sorted(dimensions_wrong.items()))
    return rec, types, previews, audit_meta

def main():
    args = parser().parse_args()
    source = source_path(args.source)
    started = perf_counter()
    stamp = datetime.now().astimezone().isoformat(timespec='seconds')
    schema = json.loads((OUT / 'schema_tpc.json').read_text(encoding='utf-8'))
    assert payload(b'a|\r\n').split(b'|') == [b'a',b''] and rule('decimal(7,2)')(b'-123.45')
    records, columns, previews, audits = [], [], {}, {}
    for lot in LOTS:
        for path in sorted((source / lot).rglob('*')):
            if not path.is_file():
                continue
            if path.suffix != '.csv' and (path.suffix != '.dat' or path.stem not in schema):
                raise ValueError(f'Format sans profil configuré : {path}')
            rec, types, preview, audit = profile(path, source, schema.get(path.stem))
            records.append(rec)
            columns.extend(types)
            previews[rec['fichier']] = preview
            if audit:
                audits[rec['fichier']] = audit
            print(f"{rec['fichier']:52} {rec['lignes']:>11} lignes  {rec['largeurs']}", flush=True)
    csv_out('01_inventaire.csv', records)
    csv_out('02_colonnes.csv', columns)
    meta = {'debut': stamp, 'fin': datetime.now().astimezone().isoformat(timespec='seconds'),
            'secondes': round(perf_counter()-started, 1), 'statut': 'succès',
            'commande': [sys.executable, *sys.argv], 'source': str(source)}
    doc_files = sorted(source.parents[1].glob('*.pdf'))
    profiles = {'execution': meta, 'fichiers': records, 'audits': audits,
                'documents_pedagogiques': [{'nom': p.name,'octets': p.stat().st_size,'sha256':digest(p)} for p in doc_files],
                'apercus_masques_3_premieres_lignes': previews}
    (OUT / '01_profil.json').write_text(json.dumps(profiles, ensure_ascii=False, indent=2), encoding='utf-8')
    for lot in LOTS:
        rows = [r for r in records if r['lot'] == lot]
        print(lot, len(rows), 'fichiers ;', sum(r['octets'] for r in rows), 'octets ;',
              sum(r['lignes'] for r in rows), 'lignes physiques')
    print(f"Succès en {meta['secondes']} s")

if __name__ == '__main__':
    main()
