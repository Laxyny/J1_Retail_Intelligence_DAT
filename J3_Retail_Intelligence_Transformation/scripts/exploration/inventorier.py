"""Inventaire exhaustif indépendant de Spark, sans modification des sources."""
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = json.loads((ROOT / 'configuration/parametres/schemas.json').read_text())


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    args = parser.parse_args()
    results, product_totals = {}, {}
    for lot, table in [('data', 'store_sales'), ('data', 'item'), ('data_refresh', 'item')]:
        path = args.sources / lot / table / (table + '.dat')
        columns = SCHEMAS[table]['columns']
        widths, missing, duplicates, keys = Counter(), Counter(), Counter(), Counter()
        rows_seen, high_bytes, crlf = set(), 0, 0
        repeated = 0
        totals = {'quantity': 0, 'net_paid': Decimal(0)}
        digest = hashlib.sha256()
        for line in path.open('rb'):
            digest.update(line)
            high_bytes += sum(b >= 128 for b in line)
            crlf += line.endswith(b'\r\n')
            fields = line.decode('utf-8', errors='strict').rstrip('\r\n').split('|')
            widths[len(fields)] += 1
            assert len(fields) == len(columns), (path, widths)
            row_hash = hashlib.sha256(line.rstrip(b'\r\n')).digest()
            repeated += row_hash in rows_seen
            rows_seen.add(row_hash)
            for (name, _), value in zip(columns, fields):
                missing[name] += value == ''
            keys[fields[2] if table == 'store_sales' else fields[0]] += 1
            if table == 'store_sales':
                qty, paid = int(fields[10]), Decimal(fields[20])
                totals['quantity'] += qty
                totals['net_paid'] += paid
                result = product_totals.setdefault(fields[2], {'quantity': 0, 'net_paid': Decimal(0), 'rows': 0})
                result['quantity'] += qty
                result['net_paid'] += paid
                result['rows'] += 1
        key = f'{lot}/{table}'
        results[key] = {'path': str(path), 'bytes': path.stat().st_size,
                        'sha256': digest.hexdigest(), 'rows': sum(widths.values()),
                        'field_counts': dict(widths), 'missing': dict(missing),
                        'exact_repeated_rows': repeated, 'distinct_keys': len(keys),
                        'key_repetitions': sum(n-1 for n in keys.values()),
                        'key_min': min(map(int, keys)), 'key_max': max(map(int, keys)),
                        'utf8_strict': True, 'non_ascii_bytes': high_bytes, 'crlf_rows': crlf,
                        'totals': totals}
        print(key, results[key]['rows'], results[key]['bytes'], 'doublons exacts', repeated, flush=True)
    output = {'sources': results, 'store_sales_by_product': product_totals}
    (ROOT / 'preuves/controles/inventaire_python.json').write_text(
        json.dumps(output, indent=2, ensure_ascii=False, default=str), encoding='utf-8')


if __name__ == '__main__':
    main()
