"""Contrôles exhaustifs des clés candidates, des relations et des fenêtres de lots."""
import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from time import perf_counter

from profiler import LOTS, OUT, csv_out, parser, payload, source_path

BASE, REFRESH = LOTS
DIMS = ('customer_address','customer_demographics','date_dim','income_band','item',
        'reason','ship_mode','store','time_dim','warehouse','household_demographics',
        'customer','promotion','web_page','web_site')
KEYS = {
    **{table: (0,) for table in DIMS + ('item_marketprices','product_reviews')},
    'store_sales': (9,2), 'web_sales': (17,3), 'store_returns': (9,2),
    'web_returns': (13,2), 'inventory': (0,1,2),
}
BUSINESS = {table: 1 for table in ('customer','customer_address','item','store','web_site','web_page','warehouse')}
FK = {
    'customer': {2:'customer_demographics',3:'household_demographics',4:'customer_address',5:'date_dim',6:'date_dim'},
    'household_demographics': {1:'income_band'},
    'promotion': {2:'date_dim',3:'date_dim',4:'item'},
    'store': {4:'date_dim'},
    'web_page': {4:'date_dim',5:'date_dim',7:'customer'},
    'web_site': {5:'date_dim',6:'date_dim'},
    'store_sales': dict(enumerate(('date_dim','time_dim','item','customer','customer_demographics',
                                  'household_demographics','customer_address','store','promotion'))),
    'web_sales': dict(enumerate(('date_dim','time_dim','date_dim','item','customer',
                                'customer_demographics','household_demographics','customer_address',
                                'customer','customer_demographics','household_demographics','customer_address',
                                'web_page','web_site','ship_mode','warehouse','promotion'))),
    'store_returns': dict(enumerate(('date_dim','time_dim','item','customer','customer_demographics',
                                    'household_demographics','customer_address','store','reason'))),
    'web_returns': dict(enumerate(('date_dim','time_dim','item','customer','customer_demographics',
                                  'household_demographics','customer_address','customer','customer_demographics',
                                  'household_demographics','customer_address','web_page','reason'))),
    'inventory': {0:'date_dim',1:'item',2:'warehouse'},
    'item_marketprices': {1:'item',4:'date_dim',5:'date_dim'},
    'web_clickstreams': {0:'date_dim',1:'time_dim',3:'item',4:'web_page',5:'customer'},
    'product_reviews': {4:'item',5:'customer'},
}
DATE_POS = {'store_sales':0,'web_sales':0,'store_returns':0,'web_returns':0,'inventory':0,
            'item_marketprices':4,'web_clickstreams':0,'product_reviews':1}
MEASURES = {
    'store_sales': (10,15,17,18,20,21,22), 'web_sales': (18,23,25,26,29,30,33),
    'store_returns': (10,11,13,19), 'web_returns': (14,15,17,23),
    'item_marketprices': (3,), 'product_reviews': (3,),
}

def key(fields, indexes):
    values = tuple(fields[i] for i in indexes)
    if any(not value for value in values):
        return None
    try:
        return tuple(map(int, values))
    except ValueError:
        return None

def rows(path, width):
    if path.exists():
        with path.open('rb') as stream:
            for line in stream:
                fields = payload(line).split(b'|')
                if len(fields) == width:
                    yield fields

def key_record(lot, table, name, valid, unique, missing, overlap):
    return dict(lot=lot, table=table, cle=name, valides=valid, distinctes=unique,
                repetitions=valid-unique, cle_vide_ou_invalide=missing, lignes_cle_dans_initial=overlap)

def measure(c, s, position, value):
    if not value:
        c[position, 'vides'] += 1
        return
    try:
        number = Decimal(value.decode('ascii'))
        if not number.is_finite():
            raise InvalidOperation()
        c[position, 'valides'] += 1
        c[position, 'negatifs'] += number < 0
        c[position, 'zero'] += number == 0
        s[position] += number
        for label, compare in [('min', min),('max', max)]:
            c[position,label] = compare(c.get((position,label),number),number)
    except (InvalidOperation, UnicodeDecodeError):
        c[position, 'invalides'] += 1

def main():
    args = parser().parse_args()
    source = source_path(args.source)
    started = perf_counter()
    stamp = datetime.now().astimezone().isoformat(timespec='seconds')
    schema = json.loads((OUT / 'schema_tpc.json').read_text(encoding='utf-8'))
    key_rows, fk_rows, periods, measures, diagnostics = [], [], [], [], []
    dim = {lot:{} for lot in LOTS}
    date_names = {}
    business = {lot:{} for lot in LOTS}
    assert key([b'0',b'12'], (0,1)) == (0,12) and key([b'0',b''], (0,1)) is None

    def path(lot, table):
        return source / lot / table / f'{table}.dat'

    def names(table, positions):
        return ' + '.join(schema[table]['columns'][i][0] for i in positions)

    def records(lot, table):
        return rows(path(lot,table), len(schema[table]['columns']))

    for lot in LOTS:
        for table in DIMS:
            if not path(lot,table).exists():
                continue
            keys, business_ids = set(), set()
            valid = invalid = overlap = valid_bid = missing_bid = overlap_bid = 0
            initial = dim[BASE].get(table, set())
            initial_bid = business[BASE].get(table,set())
            for f in records(lot,table):
                k = f[0]
                if k.isdigit():
                    valid += 1
                    if lot == REFRESH:
                        overlap += k in initial
                    keys.add(k)
                    if table == 'date_dim':
                        date.fromisoformat(f[2].decode('ascii'))
                        date_names[k] = f[2].decode('ascii')
                else:
                    invalid += 1
                if table in BUSINESS:
                    bid = f[BUSINESS[table]]
                    if bid:
                        valid_bid += 1
                        business_ids.add(bid)
                        if lot == REFRESH:
                            overlap_bid += bid in initial_bid
                    else:
                        missing_bid += 1
            dim[lot][table] = keys
            business[lot][table] = business_ids
            key_rows.append(key_record(lot,table,names(table,(0,)),valid,len(keys),invalid,overlap if lot == REFRESH else None))
            if table in BUSINESS:
                key_rows.append(key_record(lot,table,names(table,(1,)),valid_bid,len(business_ids),missing_bid,
                                           overlap_bid if lot==REFRESH else None))

    def add_fk(lot, table, positions, counts, total):
        for n,(pos, target) in enumerate(positions):
            empty, invalid, initial_miss, union_miss = (c[n] for c in counts)
            fk_rows.append(dict(lot=lot, source=table, champ=names(table,(pos,)), cible=target,
                                cle_cible=names(target,(0,)), lignes=total, vides=empty, type_invalide=invalid,
                                references_valides=total-empty-invalid, hors_initial=initial_miss,
                                hors_referentiels_livres=union_miss))

    # Case dense par produit et entrepôt pour chaque jour, pour borner la mémoire des clés stock.
    item_stride = max(map(int, dim[BASE]['item'] | dim[REFRESH].get('item',set()))) + 1
    warehouse_stride = max(map(int, dim[BASE]['warehouse'])) + 1
    slots = item_stride * warehouse_stride
    if slots > 10_000_000:
        raise ValueError('Domaine stock trop dispersé pour le contrôle dense.')
    inventories = {lot:{} for lot in LOTS}
    inventory_overflow = {lot:set() for lot in LOTS}
    for lot in LOTS:
        if not path(lot,'inventory').exists():
            continue
        total = valid = repeated = overlap = missing = negative = missing_qty = invalid_qty = qty_sum = zero = 0
        observed_dates = set()
        empty, malformed, miss_initial, miss_union = [0]*3,[0]*3,[0]*3,[0]*3
        stock = inventories[lot]
        base = inventories[BASE]
        overflow = inventory_overflow[lot]
        targets = tuple((dim[BASE][t],dim[REFRESH].get(t,set())) for t in FK['inventory'].values())
        low = high = None
        for d, i, w, q in records(lot,'inventory'):
            total += 1
            valid_fields = True
            for n, (value, (left, right)) in enumerate(zip((d,i,w),targets)):
                if not value:
                    empty[n] += 1
                    valid_fields = False
                elif not value.isdigit():
                    malformed[n] += 1
                    valid_fields = False
                elif value not in left:
                    miss_initial[n] += 1
                    miss_union[n] += value not in right
            if d:
                observed_dates.add(d)
            if valid_fields:
                valid += 1
                pi, pw = int(i), int(w)
                if pi < item_stride and pw < warehouse_stride:
                    if d not in stock:
                        stock[d] = bytearray(slots)
                    bucket = stock[d]
                    pos = pi * warehouse_stride + pw
                    repeated += bucket[pos]
                    if lot == REFRESH and d in base:
                        overlap += base[d][pos]
                    bucket[pos] = 1
                else:
                    rowkey = (d, pi, pw)
                    repeated += rowkey in overflow
                    if lot == REFRESH:
                        overlap += rowkey in inventory_overflow[BASE]
                    overflow.add(rowkey)
            if not q:
                missing_qty += 1
            elif not q.removeprefix(b'-').isdigit():
                invalid_qty += 1
            else:
                quantity = int(q)
                negative += quantity < 0
                zero += quantity == 0
                qty_sum += quantity
                low = quantity if low is None or quantity < low else low
                high = quantity if high is None or quantity > high else high
        add_fk(lot,'inventory',FK['inventory'].items(),(empty,malformed,miss_initial,miss_union),total)
        key_rows.append(key_record(lot,'inventory',names('inventory',KEYS['inventory']),valid,valid-repeated, total-valid,
                                   overlap if lot==REFRESH else None))
        dts = [date_names[k] for k in observed_dates if k in date_names]
        periods.append(dict(lot=lot,table='inventory',champ='inv_date_sk',premiere=min(dts),derniere=max(dts),jours=len(dts)))
        measures.append(dict(lot=lot,table='inventory',champ='inv_quantity_on_hand',
                             valides=total-missing_qty-invalid_qty,vides=missing_qty,invalides=invalid_qty,
                             negatifs=negative,zero=zero,min=low,max=high,somme=str(qty_sum)))
        print(f'{lot}/inventory : {total} lignes / {valid-repeated} grains distincts', flush=True)

    return_keys = {}
    sale_matches = {}
    transaction_ids = {}
    link_diag = defaultdict(Counter)
    for channel in ('store','web'):
        sale = channel+'_sales'
        ret = channel+'_returns'
        for lot in LOTS:
            return_keys[lot,channel] = {k for f in records(lot,ret) if (k:=key(f,KEYS[ret])) is not None}
        sale_matches[channel] = {k:{} for k in return_keys[BASE,channel] | return_keys[REFRESH,channel]}

    scan = ('store_sales','web_sales','store_returns','web_returns','item_marketprices',
            'product_reviews','web_clickstreams', *[t for t in DIMS if t in FK])
    for table in scan:
        first_keys = set()
        for lot in LOTS:
            if not path(lot,table).exists():
                continue
            positions = FK.get(table,{})
            tasks = [(pos,dim[BASE][target],dim[REFRESH].get(target,set())) for pos,target in positions.items()]
            empty, malformed, miss_initial, miss_union = ([0]*len(tasks) for _ in range(4))
            m, sums = Counter(), defaultdict(Decimal)
            invalid = valid = overlap = total = invalid_dates = 0
            days = set()
            keys = set()
            bad_header = missing_header = 0
            mixed_dates, mixed_customers, mixed_places = set(),set(),set()
            at_date, at_cust, at_place = {},{},{}
            transactions = Counter()
            is_sale = table in ('store_sales','web_sales')
            is_return = table in ('store_returns','web_returns')
            repeated_keys = set()
            chan = table.split('_')[0]
            for f in records(lot,table):
                total += 1
                for n,(pos,left,right) in enumerate(tasks):
                    value = f[pos]
                    if not value:
                        empty[n] += 1
                    elif not value.isdigit():
                        malformed[n] += 1
                    elif value not in left:
                        miss_initial[n] += 1
                        miss_union[n] += value not in right
                if table in DATE_POS:
                    raw = f[DATE_POS[table]]
                    if raw and raw not in days:
                        days.add(raw)
                for p in MEASURES.get(table,()):
                    measure(m,sums,p,f[p])
                k = None
                if table in KEYS and table not in DIMS:
                    k = key(f,KEYS[table])
                    if k is None:
                        invalid += 1
                    else:
                        valid += 1
                        if (is_sale or is_return) and k in keys:
                            repeated_keys.add(k)
                        keys.add(k)
                        if lot == REFRESH:
                            overlap += k in first_keys
                if is_sale:
                    ix = 9 if chan == 'store' else 17
                    cust = f[3 if chan == 'store' else 4]
                    place = f[7 if chan == 'store' else 13]
                    tx = f[ix]
                    if not tx:
                        missing_header += 1
                    elif not tx.isdigit():
                        bad_header += 1
                    else:
                        transactions[tx] += 1
                        for v, cache, mixed in ((f[0],at_date,mixed_dates),(cust,at_cust,mixed_customers),
                                                (place,at_place,mixed_places)):
                            if v and cache.setdefault(tx,v) != v:
                                mixed.add(tx)
                    if k in sale_matches[chan]:
                        match = sale_matches[chan][k].setdefault(lot, [])
                        match.append((f[0],f[10 if chan=='store' else 18],cust,place))
                elif is_return:
                    obs = link_diag[lot,table]
                    if k is None:
                        obs['cle_retour_invalide'] += 1
                    else:
                        by_lot = sale_matches[chan][k]
                        matches = by_lot.get(BASE,[]) + (by_lot.get(REFRESH,[]) if lot==REFRESH else [])
                        obs['trouve_initial'] += bool(by_lot.get(BASE))
                        obs['trouve_lot_comparable'] += bool(matches)
                        obs['plusieurs_lignes_vente'] += len(matches)>1
                        obs['trouve_refresh'] += bool(by_lot.get(REFRESH))
                        if len(matches)==1:
                            sold, qty, customer, store_or_site = matches[0]
                            returned = f[0]
                            return_qty = f[10 if chan=='store' else 14]
                            return_cust = f[3]
                            obs['dates_comparables'] += sold in date_names and returned in date_names
                            obs['retour_avant_vente'] += (sold in date_names and returned in date_names
                                                          and date_names[returned] < date_names[sold])
                            if qty.isdigit() and return_qty.isdigit():
                                obs['quantites_comparables'] += 1
                                obs['quantite_retour_superieure'] += int(return_qty)>int(qty)
                            if customer and return_cust:
                                obs['clients_comparables'] += 1
                                obs['client_different'] += customer != return_cust
                            if chan == 'store' and f[7] and store_or_site:
                                obs['magasins_comparables'] += 1
                                obs['magasin_different'] += f[7] != store_or_site
                    obs['lignes_retour'] += 1
                elif table == 'product_reviews':
                    obs = link_diag[lot,table]
                    if f[3].isdigit() and not 1 <= int(f[3]) <= 5:
                        obs['notes_hors_1_5'] += 1
                elif table == 'item_marketprices':
                    obs = link_diag[lot,table]
                    if f[4] in date_names and f[5] in date_names:
                        obs['bornes_comparables'] += 1
                        obs['fin_avant_debut'] += date_names[f[5]] < date_names[f[4]]
            add_fk(lot,table,positions.items(),(empty,malformed,miss_initial,miss_union),total)
            if table in KEYS and table not in DIMS:
                key_rows.append(key_record(lot,table,names(table,KEYS[table]),valid,len(keys),invalid,
                                           overlap if lot==REFRESH else None))
                if lot==BASE and path(REFRESH,table).exists():
                    first_keys = keys
            if is_sale or is_return:
                # Les doublons exacts ne peuvent exister que parmi les clés répétées ici.
                if invalid:
                    raise ValueError(f'{lot}/{table} : clés invalides, revoir le contrôle des doublons.')
                seen = set()
                identical = 0
                for f in records(lot,table):
                    if key(f,KEYS[table]) in repeated_keys:
                        row = tuple(f)
                        identical += row in seen
                        seen.add(row)
                link_diag[lot,table]['groupes_cle_repetee'] = len(repeated_keys)
                link_diag[lot,table]['lignes_repetitions_exactes'] = identical
            if is_sale:
                transaction_ids[lot,table] = set(transactions)
                info = dict(ids_distincts=len(transactions), ids_plusieurs_lignes=sum(n>1 for n in transactions.values()),
                            lignes_sans_id=missing_header,lignes_id_invalide=bad_header,
                            ids_plusieurs_dates=len(mixed_dates),ids_plusieurs_clients_renseignes=len(mixed_customers),
                            ids_plusieurs_lieux_renseignes=len(mixed_places))
                if lot==REFRESH:
                    info['ids_aussi_dans_initial'] = len(transaction_ids[BASE,table] & set(transactions))
                link_diag[lot,table].update(info)
            if table in DATE_POS:
                if table=='product_reviews':
                    values = []
                    for d in days:
                        try:
                            values.append(date.fromisoformat(d.decode('ascii')).isoformat())
                        except ValueError:
                            invalid_dates += 1
                    link_diag[lot,table]['valeurs_date_distinctes_invalides'] = invalid_dates
                else:
                    values = [date_names[d] for d in days if d in date_names]
                periods.append(dict(lot=lot, table=table, champ=names(table,(DATE_POS[table],)),
                                    premiere=min(values,default=None),derniere=max(values,default=None),jours=len(set(values))))
            for pos in MEASURES.get(table,()):
                measures.append(dict(lot=lot,table=table,champ=names(table,(pos,)),valides=m[pos,'valides'],
                                     vides=m[pos,'vides'],invalides=m[pos,'invalides'],negatifs=m[pos,'negatifs'],
                                     zero=m[pos,'zero'],min=str(m[pos,'min']),max=str(m[pos,'max']),somme=str(sums[pos])))
            print(f'{lot}/{table} : {total} lignes contrôlées', flush=True)
    for (lot,table), counters in link_diag.items():
        diagnostics.extend(dict(lot=lot,table=table,controle=k,resultat=v) for k,v in counters.items())
    shared = transaction_ids[BASE,'store_sales'] & transaction_ids[BASE,'web_sales']
    diagnostics.append(dict(lot=BASE,table='store_sales ∩ web_sales',controle='ids_entete_communs',resultat=len(shared)))
    for filename, data in [('03_cles.csv',key_rows),('04_relations.csv',fk_rows),('05_periodes.csv',periods),
                           ('06_mesures.csv',measures),('07_diagnostics.csv',diagnostics)]:
        csv_out(filename,data)
    summary = {'debut':stamp,'fin':datetime.now().astimezone().isoformat(timespec='seconds'),
               'secondes':round(perf_counter()-started,1),'statut':'succès','commande':[sys.executable,*sys.argv],
               'source':str(source),'controles_fk':len(fk_rows),'controles_cles':len(key_rows)}
    (OUT/'03_execution.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"Succès en {summary['secondes']} s. {len(fk_rows)} relations par lot, {len(key_rows)} clés candidates.", flush=True)

if __name__ == '__main__':
    main()
