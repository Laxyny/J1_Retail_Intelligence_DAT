"""Recalcule les KPI du DAT en lecture seule sur les deux lots inventoriés."""
import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
from statistics import median
from time import perf_counter

from profiler import LOTS, OUT, csv_out, digest, parser, payload, rule, source_path

SALES = ('quantity','net_paid','ext_list_price','ext_sales_price','ext_wholesale_cost',
         'net_paid_inc_tax','net_profit','ext_tax','coupon_amt','ext_discount_amt')
RETURNS = ('return_quantity','return_amt','return_tax','return_amt_inc_tax','net_loss',
           'return_ship_cost','fee','refunded_cash','reversed_charge')
SNAPSHOT = '2005-12-12'
BASE, REFRESH = LOTS

def amount(cents):
    return Decimal(cents).scaleb(-2)

def cents(value):
    whole, dot, fraction = value.removeprefix(b'-').partition(b'.')
    number = int(whole) * 100 + (int(fraction.ljust(2,b'0')) if dot else 0)
    return -number if value.startswith(b'-') else number

class Field:
    def __init__(self, typ):
        self.typ = typ
        self.valid = rule(typ)
        self.n = self.blank = self.invalid = self.negative = self.zero = self.total = 0
        self.low = self.high = None

    def read(self, v):
        if not v:
            self.blank += 1
            return None
        if not self.valid(v):
            self.invalid += 1
            return None
        parsed = cents(v) if self.typ.startswith('decimal') else int(v)
        self.n += 1
        self.negative += parsed < 0
        self.zero += parsed == 0
        self.total += parsed
        self.low = parsed if self.low is None else min(self.low, parsed)
        self.high = parsed if self.high is None else max(self.high, parsed)
        return parsed

    def summary(self):
        convert = amount if self.typ.startswith('decimal') else lambda v: v
        return dict(type_ddl=self.typ, valides=self.n, vides=self.blank, invalides=self.invalid,
                    negatifs=self.negative, zeros=self.zero, minimum=convert(self.low) if self.n else None,
                    maximum=convert(self.high) if self.n else None, somme=convert(self.total))

def main():
    args = parser().parse_args()
    root = source_path(args.source)
    start = datetime.now().astimezone().isoformat(timespec='seconds')
    timer = perf_counter()
    schema = json.loads((OUT/'schema_tpc.json').read_text(encoding='utf-8'))
    profile = json.loads((OUT/'01_profil.json').read_text(encoding='utf-8'))
    expected = {r['fichier']: r for r in profile['fichiers']}
    positions = {t: {name: i for i,(name,_) in enumerate(s['columns'])} for t,s in schema.items()}
    dat_read = {}
    checks, metrics, fields = [], [], []
    assert cents(b'-1.02') == -102 and cents(b'2.3') == 230 and cents(b'0') == 0

    def rows(lot, table):
        relative = f'{lot}/{table}/{table}.dat'
        path = root/relative
        record = expected[relative]
        count = 0
        width = len(positions[table])
        with path.open('rb') as stream:
            for line in stream:
                count += 1
                value = payload(line).split(b'|')
                if len(value) != width:
                    raise ValueError(f'{relative}, ligne {count} : largeur {len(value)}, attendu {width}')
                yield value
        assert count == record['lignes'] and path.stat().st_size == record['octets'], relative
        dat_read[relative] = count
        print(f'{lot}/{table} : {count} lignes contrôlées',flush=True)

    def view(lot, table, names):
        indexes = tuple(positions[table][name] for name in names)
        for r in rows(lot,table):
            yield tuple(r[i] for i in indexes)

    def field(table, name):
        return Field(schema[table]['columns'][positions[table][name]][1])

    def save_fields(lot, table, observed):
        for name, stats in observed.items():
            fields.append(dict(lot=lot,table=table,champ=name,**stats.summary()))

    def control(lot, domain, values):
        checks.extend(dict(lot=lot,domaine=domain,controle=code,valeur=x) for code,x in values.items())

    def kpi(k, lot, scope, unit, num, den=None, *, factor=1, note=''):
        value = num if den is None else (Decimal(num) / den * factor if den else None)
        metrics.append(dict(kpi=k,lot=lot,perimetre=scope,unite=unit,numerateur=num,denominateur=den,
                            valeur=value,note=note))

    calendar = {key:date.fromisoformat(d.decode('ascii')) for key,d in
                view(BASE,'date_dim',('d_date_sk','d_date'))}
    item_ref = {}
    customer_ref = set()
    warehouse_ref = {r[0] for r in rows(BASE,'warehouse')}
    for lot in LOTS:
        for r in view(lot,'item',('i_item_sk','i_rec_start_date','i_rec_end_date','i_current_price')):
            sk, first, last, price = r
            assert sk not in item_ref
            price_valid = rule('decimal(7,2)')(price) if price else False
            item_ref[sk] = (first,last,cents(price) if price_valid else None)
        customer_ref.update(r[0] for r in rows(lot,'customer'))
    snapshot = date.fromisoformat(SNAPSHOT)
    expected_stock = len(warehouse_ref)*len(item_ref)
    money_unit = 'UM du kit'
    sale_days = {}

    for lot in LOTS:
        for table,prefix,channel in [('store_sales','ss','Magasin'),('web_sales','ws','Web')]:
            web = prefix=='ws'
            measures = tuple(f'{prefix}_{n}' for n in SALES)
            tx_key = 'ws_order_number' if web else 'ss_ticket_number'
            cust_key = 'ws_bill_customer_sk' if web else 'ss_customer_sk'
            date_key = f'{prefix}_sold_date_sk'
            selected = (*measures,tx_key,cust_key,date_key) + (('ws_ship_date_sk',) if web else ())
            track = {name:field(table,name) for name in measures}
            tx = {}
            clients, days = set(),set()
            months, day_net = Counter(),Counter()
            anomalies = Counter({k:0 for k in (
                'net_vs_vente_moins_coupon','ecart_max_net_centimes','taxe_vs_ttc_moins_net',
                'remise_vs_catalogue_moins_vente','resultat_vs_net_moins_cout','net_superieur_catalogue',
                'coupons_superieurs_montant_vente','lignes_incompletes_finance','date_vente_non_resolue',
                'transactions_date_incoherente','en_tete_invalide','client_vide','client_non_resolu')})
            if web:
                anomalies.update({k:0 for k in ('date_expedition_vide','date_expedition_non_resolue',
                                                'expedition_avant_vente','ventes_sans_delai_valide')})
            lead = Counter()
            orders_ship_date = {}
            multiple_ship = set()
            for r in view(lot,table,selected):
                pay = tuple(s.read(raw) for s,raw in zip(track.values(),r))
                q,net,listing,selling,cost,ttc,profit,tax,coupon,discount = pay
                key,client,day_key = r[len(SALES):len(SALES)+3]
                sold = calendar.get(day_key)
                if sold:
                    days.add(sold)
                    if net is not None:
                        months[sold.isoformat()[:7]] += net
                        day_net[sold] += net
                else:
                    anomalies['date_vente_non_resolue'] += 1
                if client in customer_ref:
                    clients.add(client)
                else:
                    anomalies['client_non_resolu' if client else 'client_vide'] += 1
                if key.isdigit():
                    order = tx.setdefault(key,[day_key,0,0,True,False])
                    if order[0] != day_key:
                        order[4] = True
                    order[3] &= net is not None and q is not None and q > 0 and sold is not None
                    order[1] += net or 0
                    order[2] += q or 0
                else:
                    anomalies['en_tete_invalide'] += 1
                if all(v is not None for v in pay):
                    delta = abs(net - (selling-coupon))
                    anomalies['net_vs_vente_moins_coupon'] += delta > 0
                    anomalies['ecart_max_net_centimes'] = max(anomalies['ecart_max_net_centimes'],delta)
                    anomalies['taxe_vs_ttc_moins_net'] += ttc-net != tax
                    anomalies['remise_vs_catalogue_moins_vente'] += discount != listing-selling
                    anomalies['resultat_vs_net_moins_cout'] += profit != net-cost
                    anomalies['net_superieur_catalogue'] += net > listing
                    anomalies['coupons_superieurs_montant_vente'] += coupon > selling
                else:
                    anomalies['lignes_incompletes_finance'] += 1
                if web:
                    ship_key = r[-1]
                    ship = calendar.get(ship_key)
                    anomalies['date_expedition_vide'] += not ship_key
                    anomalies['date_expedition_non_resolue'] += bool(ship_key) and not ship
                    if sold and ship:
                        delay = (ship-sold).days
                        anomalies['expedition_avant_vente'] += delay < 0
                        if delay >= 0:
                            lead[delay] += 1
                        if key.isdigit() and orders_ship_date.setdefault(key,ship_key) != ship_key:
                            multiple_ship.add(key)
                    else:
                        anomalies['ventes_sans_delai_valide'] += 1
            save_fields(lot,table,track)
            anomalies['transactions_date_incoherente'] = sum(row[4] for row in tx.values())
            ok = [row for row in tx.values() if row[3] and not row[4]]
            anomalies['transactions_incompletes_exclues'] = len(tx)-len(ok)
            block = {name.removeprefix(prefix+'_'):s for name,s in track.items()}
            paid = amount(block['net_paid'].total)
            qty = block['quantity'].total
            profit = amount(block['net_profit'].total)
            listing = amount(block['ext_list_price'].total)
            kpi('K01',lot,channel,money_unit,paid)
            kpi('K02',lot,channel,'unités',qty)
            kpi('K03',lot,channel,'transactions',len(tx))
            kpi('K04',lot,channel,'UM par transaction',amount(sum(r[1] for r in ok)),len(ok))
            if lot==BASE:
                nov,october=months['2005-11'],months['2005-10']
                assert sum(d.month==10 and d.year==2005 for d in days)==31
                assert sum(d.month==11 and d.year==2005 for d in days)==30
                kpi('K05',lot,channel+' · nov. / oct. 2005','%',amount(nov-october),amount(october),factor=100)
            kpi('K08',lot,channel,'%',listing-paid,listing,factor=100)
            kpi('K09',lot,channel,'clients identifiés',len(clients),note='facturation' if web else 'client de vente')
            kpi('K13',lot,channel,money_unit,profit)
            kpi('K14',lot,channel,'%',profit,paid,factor=100)
            for kid,name in [('K17','ext_tax'),('K18','coupon_amt'),('K19','ext_discount_amt')]:
                kpi(kid,lot,channel,money_unit,amount(block[name].total))
            kpi('K20',lot,channel,'UM par unité',paid,qty)
            kpi('K21',lot,channel,'unités par transaction',sum(r[2] for r in ok),len(ok))
            if web:
                anomalies.update(lignes_delai_valide=sum(lead.values()),delai_min_jours=min(lead,default=None),
                                 delai_max_jours=max(lead,default=None),commandes_dates_expedition_multiples=len(multiple_ship))
                kpi('K25',lot,'Web · ligne expédiée','jours calendaires',sum(k*v for k,v in lead.items()),sum(lead.values()))
            sale_days[lot,channel] = day_net
            control(lot,table,anomalies)

        common = set(sale_days[lot,'Magasin']) & set(sale_days[lot,'Web'])
        values = {channel:amount(sum(sale_days[lot,channel][d] for d in common)) for channel in ('Magasin','Web')}
        control(lot,'ventes_canaux',dict(jours_communs=len(common),
                                        jours_exclus_magasin=len(sale_days[lot,'Magasin'])-len(common),
                                        jours_exclus_web=len(sale_days[lot,'Web'])-len(common)))
        for channel,value in values.items():
            kpi('K27',lot,channel+' · dates communes','%',value,sum(values.values()),factor=100)

        for table,prefix,channel,credit in [
            ('store_returns','sr','Magasin','store_credit'),
            ('web_returns','wr','Web','account_credit')]:
            names=tuple(f'{prefix}_{n}' for n in (*RETURNS,credit))
            track={n:field(table,n) for n in names}
            bad_ttc=bad_loss=bad_date=bad_observed_loss=bad_refunds=0
            for values in view(lot,table,(*names,f'{prefix}_returned_date_sk')):
                q,ht,tax,ttc,loss,ship,fee,cash,charge,credited=(
                    s.read(raw) for s,raw in zip(track.values(),values))
                if None not in (ttc,ht,tax):
                    bad_ttc += ttc != ht+tax
                if None not in (loss,ht,ship,tax,credited,cash,charge,fee):
                    bad_loss += loss != ht+ship+tax-credited-cash-charge+fee
                    bad_observed_loss += loss != ship + 2*tax
                    bad_refunds += ht != credited+cash+charge
                bad_date += values[-1] not in calendar
            save_fields(lot,table,track)
            for kid,n in [('K06','return_quantity'),('K15','return_amt'),('K16','net_loss')]:
                stat=track[f'{prefix}_{n}']
                kpi(kid,lot,channel,'unités' if kid=='K06' else money_unit,
                    stat.total if kid=='K06' else amount(stat.total))
            control(lot,table,dict(ttc_vs_ht_plus_taxe=bad_ttc,perte_vs_formule_tpc=bad_loss,
                                   perte_vs_port_plus_deux_taxes=bad_observed_loss,
                                   remboursement_vs_montant_ht=bad_refunds,
                                   date_retour_non_resolue=bad_date))

    stocks = {lot:defaultdict(Counter) for lot in LOTS}
    snapshot_keys = {lot:set() for lot in LOTS}
    for lot in LOTS:
        overview = Counter()
        qty_summary=field('inventory','inv_quantity_on_hand')
        for d,i,w,raw in rows(lot,'inventory'):
            stat=stocks[lot][d]
            stat['observes'] += 1
            qty=qty_summary.read(raw)
            if qty is None:
                continue
            if qty < 0:
                continue
            stat['connus'] += 1
            stat['zero'] += qty==0
            stat['quantite'] += qty
            if calendar[d]==snapshot:
                snapshot_keys[lot].add((i,w))
        for key,stat in stocks[lot].items():
            day=calendar[key].isoformat()
            control(lot,'stock '+day,{'triplets_observes':stat['observes'],
                                       'quantites_connues':stat['connus'],'zeros':stat['zero'],
                                       'quantite_observee':stat['quantite']})
            if day==SNAPSHOT:
                overview.update(stat)
        save_fields(lot,'inventory',{'inv_quantity_on_hand':qty_summary})
        kpi('K07',lot,SNAPSHOT+' · couverture du lot','unités',overview['quantite'],
            note=f"{overview['connus']} quantités connues sur {overview['observes']} triplets")
        kpi('K22',lot,SNAPSHOT+' · couverture du lot','%',overview['zero'],overview['connus'],factor=100)
    snap_key=next(k for k,d in calendar.items() if d==snapshot)
    assert not snapshot_keys[BASE] & snapshot_keys[REFRESH], 'triplet stock commun'
    combined=stocks[BASE][snap_key]+stocks[REFRESH][snap_key]
    control('data + data_refresh','stock '+SNAPSHOT,dict(triplets_observes=combined['observes'],
            quantites_connues=combined['connus'],triplets_attendus_panier_reference=expected_stock))
    kpi('K07','data + data_refresh',SNAPSHOT+' · simulation de réunion','unités',combined['quantite'],
        note=f"{combined['connus']} quantités connues sur {combined['observes']} triplets observés")
    kpi('K22','data + data_refresh',SNAPSHOT+' · simulation de réunion','%',combined['zero'],combined['connus'],factor=100,
        note='Couverture du stock à publier avec le taux, politique de refresh à valider')

    targets = {'date':set(calendar),'item':set(item_ref),'customer':customer_ref}
    targets['page'] = {r[0] for r in rows(BASE,'web_page')}
    for lot in LOTS:
        track=field('product_reviews','pr_review_rating')
        reviews=set()
        cnt=Counter()
        for r in rows(lot,'product_reviews'):
            cnt['cle_invalide'] += not r[0].isdigit()
            if r[0].isdigit():
                cnt['cle_repetee'] += r[0] in reviews
                reviews.add(r[0])
            stars=track.read(r[3])
            cnt['note_hors_1_5'] += stars is not None and not 1<=stars<=5
            cnt['produit_non_resolu'] += r[4] not in targets['item']
        save_fields(lot,'product_reviews',{'pr_review_rating':track})
        control(lot,'product_reviews',cnt)
        assert cnt['note_hors_1_5']==0 and cnt['cle_invalide']==cnt['cle_repetee']==0
        kpi('K10',lot,'Avis du lot','note sur 5',track.total,track.n)
        kpi('K23',lot,'Avis du lot','avis',len(reviews))
        cnt=Counter()
        for d,t,s,i,p,c in rows(lot,'web_clickstreams'):
            cnt['lignes'] += 1
            cnt['client_resolu'] += c in targets['customer']
            cnt['client_renseigne_non_resolu'] += bool(c) and c not in targets['customer']
            cnt['client_vide'] += not c
            cnt['date_non_resolue'] += d not in targets['date']
            cnt['page_vide'] += not p
            cnt['page_renseignee_non_resolue'] += bool(p) and p not in targets['page']
        kpi('K11',lot,'Navigation du lot','%',cnt['client_resolu'],cnt['lignes'],factor=100)
        kpi('K24',lot,'Navigation du lot','lignes événement',cnt['lignes'])
        control(lot,'web_clickstreams',cnt)

    for lot in LOTS:
        quote=field('item_marketprices','imp_competitor_price')
        active=defaultdict(list)
        inclusive=0
        diagnostics=Counter()
        for _,sku,competitor,raw,first,last in rows(lot,'item_marketprices'):
            price=quote.read(raw)
            a,b=calendar.get(first),calendar.get(last)
            if not a or not b:
                diagnostics['plage_non_resolue'] += 1
                continue
            diagnostics['plage_inversee'] += b<a
            if price is not None and price>0 and sku in item_ref and competitor:
                inclusive += a<=snapshot<=b
                if a<=snapshot<b:
                    active[sku,competitor].append(price)
        by_product=defaultdict(list)
        for (sku,_),group in active.items():
            if len(group)>1:
                diagnostics['groupes_concurrent_multiples_au_snapshot'] += 1
                continue
            first,last,price=item_ref[sku]
            if price is not None and price>0 and first and first<=SNAPSHOT.encode() and (not last or SNAPSHOT.encode()<last):
                by_product[sku].append(group[0])
        diagnostics.update(offres_actives_fin_exclue=sum(map(len,active.values())),
                           offres_actives_fin_incluse=inclusive,
                           produits_comparables=len(by_product))
        nullable_gaps = [Decimal(item_ref[sku][2])-Decimal(str(median(prices))) for sku,prices in by_product.items()]
        control(lot,'prix marché '+SNAPSHOT,diagnostics)
        save_fields(lot,'item_marketprices',{'imp_competitor_price':quote})
        if nullable_gaps:
            kpi('K26',lot,SNAPSHOT+' · diagnostic exploratoire','UM par produit',
                amount(sum(nullable_gaps)),len(nullable_gaps),
                note='Prix courant item moins médiane concurrente. Fin exclue, doublons concurrent exclus. Convention et équivalence à valider.')

    for relative in sorted(dat_read):
        assert digest(root/relative)==expected[relative]['sha256'], relative
    for name,data in [('11_kpi_valeurs.csv',metrics),('12_kpi_champs.csv',fields),('13_kpi_controles.csv',checks)]:
        csv_out(name,data)
    meta=dict(debut=start,fin=datetime.now().astimezone().isoformat(timespec='seconds'),
              secondes=round(perf_counter()-timer,2),statut='succès',commande=[sys.executable,*sys.argv],
              source=str(root),fichiers_sha256=len(dat_read),valeurs=len(metrics),champs=len(fields),controles=len(checks),
              regle='Calculs par lot. Réunion stock du 12/12/2005 : diagnostic de couverture.')
    (OUT/'11_kpi_execution.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False),flush=True)

if __name__=='__main__':
    main()
