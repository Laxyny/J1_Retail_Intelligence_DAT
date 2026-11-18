"""Pipeline UC-06 complet, sorties HDFS dédiées, arrêt sur contrôle bloquant."""
import json
import sys
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from uc06 import ROOT, F, T, session, read_source, normalize_item, parquet_checked, save


def main():
    config = json.loads((ROOT/'configuration/parametres/execution.json').read_text())
    independent = json.loads((ROOT/'preuves/controles/inventaire_python.json').read_text())
    spark = session('UC06-Silver-Gold')
    fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(spark._jsc.hadoopConfiguration())
    for dest in [config['silver'],config['gold']]:
        assert not fs.exists(spark._jvm.org.apache.hadoop.fs.Path(dest)), 'Lot déjà présent : créer un nouveau lot, jamais écraser'
    frames, casts, controls, outputs, rejects, changed = {}, {}, [], {}, {}, {}

    def check(rule, target, value, expected=None, status=None, method='', justification='', limit='Exhaustif sur les fichiers initiaux retenus'):
        state = status or ('OK' if value == expected else 'ECHEC')
        controls.append(dict(id=f'Q{len(controls)+1:03}',rule=rule,target=target,result=value,
                             expected=expected,status=state,method=method,justification=justification,limits=limit))
        if state == 'ECHEC':
            save('preuves/controles/qualite_echec.json',controls)
            raise AssertionError((rule,target,value,expected))

    for table in ['store_sales','item']:
        df, failures = read_source(spark,table,config['sources'][table]['hdfs'])
        df = df.cache()
        casts[table] = failures
        n = df.count()
        check('Volume Raw/Python',table,n,independent['sources']['data/'+table]['rows'],method='count vs lecture Python indépendante')
        check('Conversions sans perte',table,sum(failures.values()),0,method='try_cast sur chaque valeur non nulle')
        profile = json.loads((ROOT/f'preuves/controles/J3-P04-{table}.json').read_text())
        for col, nulls in profile['nulls'].items():
            check('Complétude '+col,table,nulls,status='OBSERVE' if nulls else 'OK',method='SUM(isNull)',
                  justification='NULL conservé ; champs facultatifs ou fin de validité ouverte' if nulls else 'Champ renseigné')
        check('Doublons exacts',table,profile['exact_repeated_rows'],0,method='count - distinct toutes colonnes natives')
        if table == 'store_sales':
            invalid = F.col('ss_item_sk').isNull() | (F.col('ss_item_sk')<0) | F.col('ss_ticket_number').isNull() | (F.col('ss_ticket_number')<0) | F.col('ss_quantity').isNull() | F.col('ss_net_paid').isNull()
            changed[table] = 0
            clean = df
        else:
            invalid = F.col('i_item_sk').isNull() | (F.col('i_item_sk')<0)
            text = [f.name for f in df.schema if isinstance(f.dataType,T.StringType)]
            condition = F.lit(False)
            for col in text:
                condition = condition | (~F.col(col).eqNullSafe(F.trim(col)))
            changed[table] = df.filter(condition).count()
            clean = normalize_item(df)
            for col in ['i_rec_start_date','i_rec_end_date']:
                check('Date ISO valide '+col,table,profile['date_errors'][col],0,method='try_cast date non vide')
            check('Ordre dates produit',table,clean.filter(F.col('i_rec_end_date')<F.col('i_rec_start_date')).count(),0,method='fin < début ; nulls ouverts exclus')
        rejected = df.filter(invalid)
        rejects[table] = rejected.count()
        if rejects[table]:
            parquet_checked(spark,rejected.withColumn('_reject_reason',F.lit('Identifiant ou mesure nécessaire invalide')),
                f"hdfs://hdfs:9000/retail-lake/quality/j3/{config['run_id']}/{table}_rejects")
        clean = clean.filter(~invalid)
        for name, value in {'_source_uri':config['sources'][table]['hdfs'],
                            '_source_sha256':config['sources'][table]['sha256'],
                            '_source_batch':'initial','_run_id':config['run_id']}.items():
            clean = clean.withColumn(name,F.lit(value))
        frames[table], outputs['silver_'+table] = parquet_checked(spark,clean,config['silver']+'/'+table)
        check('Conservation Raw=Silver+rejets',table,n,frames[table].count()+rejects[table],method='count')
        check('Provenance Silver',table,frames[table].filter(F.col('_source_sha256')!=config['sources'][table]['sha256']).count(),0,method='comparaison empreinte attendue')
        print('SILVER',table,outputs['silver_'+table],flush=True)
        df.unpersist()

    sales, items = frames['store_sales'], frames['item']
    before, dim = sales.count(), items.count()
    check('Unicité clé dimension', 'item', dim-items.select('i_item_sk').distinct().count(),0,method='count - count distinct i_item_sk')
    check('Clé jointure types','store_sales/item',sales.schema['ss_item_sk'].dataType.simpleString(),items.schema['i_item_sk'].dataType.simpleString(),method='schémas explicites')
    unmatched = sales.join(items,sales.ss_item_sk==items.i_item_sk,'left_anti').count()
    check('Intégrité référentielle','store_sales/item',unmatched,0,method='left_anti')
    enriched = sales.join(items.select('i_item_sk','i_product_name','i_category','i_brand'),sales.ss_item_sk==items.i_item_sk,'left').cache()
    after = enriched.count()
    check('Cardinalité jointure gauche','store_sales/item',after,before,method='count avant/après')
    totals = sales.agg(F.sum('ss_quantity').alias('quantity'),F.sum('ss_net_paid').alias('net_paid'),F.count('*').alias('rows')).first().asDict()
    gold = enriched.groupBy('ss_item_sk','i_product_name','i_category','i_brand').agg(
        F.sum('ss_quantity').alias('quantity_sold'),F.sum('ss_net_paid').alias('net_paid'),F.count('*').alias('sales_line_count'))
    gold = gold.withColumn('_run_id',F.lit(config['run_id'])).withColumn('_source_sales_sha256',F.lit(config['sources']['store_sales']['sha256'])).withColumn('_source_item_sha256',F.lit(config['sources']['item']['sha256']))
    gold, outputs['gold_ventes_par_produit'] = parquet_checked(spark,gold,config['gold']+'/ventes_par_produit')
    gold_totals = gold.agg(F.sum('quantity_sold').alias('quantity'),F.sum('net_paid').alias('net_paid'),F.sum('sales_line_count').alias('rows')).first().asDict()
    for metric in totals:
        check('Réconciliation Silver/Gold '+metric,'gold',gold_totals[metric],totals[metric],method='SUM et COUNT aux deux grains')
    check('Gold clé produit unique','gold',gold.count()-gold.select('ss_item_sk').distinct().count(),0,method='count-distinct')
    py = independent['sources']['data/store_sales']['totals']
    check('Somme quantité indépendante','gold',gold_totals['quantity'],py['quantity'],method='SUM Spark vs entiers Python')
    check('Somme monétaire indépendante','gold',gold_totals['net_paid'],Decimal(py['net_paid']),method='SUM Spark Decimal vs decimal.Decimal Python')
    by_product = independent['store_sales_by_product']
    differences = 0
    for r in gold.select('ss_item_sk','quantity_sold','net_paid','sales_line_count').collect():
        p = by_product[str(r.ss_item_sk)]
        differences += (r.quantity_sold!=p['quantity'] or r.net_paid!=Decimal(p['net_paid']) or r.sales_line_count!=p['rows'])
    check('Réconciliation de chaque produit','gold',differences,0,method='Toutes les lignes Gold vs groupement Python indépendant')
    for rule, value in json.loads((ROOT/'preuves/controles/J3-P04-store_sales.json').read_text())['coherence'].items():
        check(rule,'store_sales',value,0,method='égalité décimale exhaustive')
    check('Couple ticket-produit non unique','store_sales',4136,status='ANOMALIE_DOCUMENTEE',method='count - distinct couple, notebook',justification='Pas une clé de ligne ; aucune suppression')
    check('Profits négatifs conservés','store_sales',sales.filter(F.col('ss_net_profit')<0).count(),495971,method='count ss_net_profit<0',justification='Signe conservé, ne constitue pas un rejet')
    top = [r.asDict() for r in gold.orderBy(F.desc('net_paid'),'ss_item_sk').limit(10).collect()]
    summary = dict(run_id=config['run_id'],spark=spark.version,outputs=outputs,casts=casts,
                   rejects=rejects,text_changed=changed,totals=gold_totals,
                   join=dict(before=before,after=after,unmatched=unmatched),top10=top,
                   checks=controls)
    save('preuves/controles/J3-P06-transformation.json',summary)
    save('preuves/parquet/J3-P08-parquet.json',outputs)
    print('GOLD',gold_totals,'produits',gold.count(),flush=True)
    gold.orderBy(F.desc('net_paid'),'ss_item_sk').show(10,truncate=36)
    save('preuves/controles/J3-P09-qualite.json',controls)
    print('CONTROLES',len(controls),'ECHECS',sum(c['status']=='ECHEC' for c in controls),flush=True)
    enriched.unpersist()
    spark.stop()


if __name__ == '__main__':
    main()
