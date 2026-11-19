# %% [markdown]
# # Retail Intelligence Platform - Jour 4, UC-08
# IPSSI - 19 novembre 2026. Parcours B local/open source. Données synthétiques TPCx-BB.
# Ce notebook relit exclusivement le lot J3 final. Aucun nettoyage ni réécriture des zones HDFS.
# Objectifs V2 : quatre KPI métier, volume technique, statistiques, produits, magasins et catégories.
# UM signifie unité monétaire ; la devise n'est pas établie.
# Les résultats monétaires sont calculés en Decimal ; seules les coordonnées graphiques passent en flottants.
# %%
import os
import sys
import json
import csv
import platform
import importlib.metadata as metadata
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from IPython.display import Image, display
from pyspark.sql import SparkSession, functions as F

ROOT = Path(os.environ.get('J4_ROOT', str(Path(__file__).resolve().parents[2]) if '__file__' in globals() else '../..')).resolve()
MODE = os.environ.get('J4_MODE', 'hdfs')
BATCH = '20261118T113628Z-243a5fb5-r3'
assert MODE in ('hdfs', 'local'), MODE
for folder in ['analytics/outputs','analytics/visualisations','preuves/analyses','preuves/environnement']:
    (ROOT/folder).mkdir(parents=True, exist_ok=True)

def save(relative, data):
    (ROOT/relative).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

def export(relative, rows):
    rows = [r.asDict() if hasattr(r, 'asDict') else r for r in rows]
    assert rows, relative
    with (ROOT/relative).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

environment = {'date_utc':datetime.now(timezone.utc).isoformat(), 'python':sys.version,
               'executable':sys.executable, 'system':platform.platform(), 'mode':MODE,
               'versions':{p:metadata.version(p) for p in ['pyspark','pandas','matplotlib','numpy','notebook','jupyterlab','nbformat','nbclient','nbconvert','ipykernel']}}
print(json.dumps(environment, ensure_ascii=False, indent=2))
# %% [markdown]
# Le noyau réutilise le venv du conteneur Spark J3. Pandas, Matplotlib et Jupyter ont été ajoutés dans ce venv,
# sans changer Python, Java ni Spark. Les versions affichées ci-dessus sont celles de cette exécution.
# Les chemins d'entrée sont paramétrables par J4_MODE, J4_SALES, J4_ITEM et J4_GOLD.
# %%
os.environ['PYSPARK_PYTHON'] = sys.executable
spark = (SparkSession.builder.master('local[2]').appName('Retail-J4-UC08')
         .config('spark.driver.memory','1536m').config('spark.sql.shuffle.partitions','4')
         .config('spark.ui.enabled','false').config('spark.sql.ansi.enabled','true')
         .config('spark.sql.session.timeZone','UTC')
         .config('spark.hadoop.fs.defaultFS','hdfs://hdfs:9000' if MODE=='hdfs' else 'file:///')
         .config('spark.hadoop.dfs.client.use.datanode.hostname','true').getOrCreate())
spark.sparkContext.setLogLevel('WARN')
environment.update(spark=spark.version, java=spark.sparkContext._jvm.java.lang.System.getProperty('java.version'),
                   hadoop_client=spark.sparkContext._jvm.org.apache.hadoop.util.VersionInfo.getVersion())
save('preuves/environnement/environnement.json', environment)
print('Session Spark active :', spark.version, '| Java', environment['java'])
# %% [markdown]
# La session est locale dans Docker mais le mode hdfs utilise le protocole RPC du NameNode existant.
# Un mode local explicite est également prévu pour les exports Parquet vérifiés du Jour 3.
# %%
base = 'hdfs://hdfs:9000/retail-lake'
local = Path(os.environ.get('J4_J3_EXPORT','/work/donnees_produites/export'))
paths = {
    'store_sales':os.environ.get('J4_SALES', f'{base}/silver/j3/{BATCH}/store_sales' if MODE=='hdfs' else (local/'silver/store_sales').as_uri()),
    'item':os.environ.get('J4_ITEM', f'{base}/silver/j3/{BATCH}/item' if MODE=='hdfs' else (local/'silver/item').as_uri()),
    'ventes_par_produit':os.environ.get('J4_GOLD', f'{base}/gold/j3/{BATCH}/ventes_par_produit' if MODE=='hdfs' else (local/'gold/ventes_par_produit').as_uri())}
frames = {name:spark.read.parquet(path).cache() for name,path in paths.items()}
sales, items, gold = (frames[n] for n in ['store_sales','item','ventes_par_produit'])
counts = {name:df.count() for name,df in frames.items()}
inventory = {name:{'path':paths[name], 'rows':counts[name], 'schema':df.schema.jsonValue(),
                   'files':sorted(df.inputFiles()), 'batch':BATCH} for name,df in frames.items()}
for name,df in frames.items():
    print(name, counts[name], 'lignes', paths[name])
    df.printSchema()
save('preuves/analyses/inventaire.json', inventory)
assert counts == {'store_sales':667579,'item':17820,'ventes_par_produit':17820}
assert dict(sales.dtypes)['ss_net_paid']=='decimal(7,2)'
assert dict(gold.dtypes)['net_paid']=='decimal(17,2)'
# %% [markdown]
# Silver store_sales conserve une ligne de vente ; item conserve une ligne par clé produit.
# Gold est déjà agrégé par produit : sales_line_count permet de retrouver le nombre de faits,
# tandis que compter ses lignes mesure le nombre de produits. Aucun calendrier supplémentaire n'est joint.
# %%
totals = sales.agg(F.count('*').alias('sales_lines'),F.sum('ss_quantity').alias('units'),F.sum('ss_net_paid').alias('net_paid')).first().asDict()
gold_totals = gold.agg(F.sum('sales_line_count').alias('sales_lines'),F.sum('quantity_sold').alias('units'),F.sum('net_paid').alias('net_paid')).first().asDict()
# %% [markdown]
# ## Qualification des transactions magasin
# UC-01 définit un en-tête distinct par canal. Le contrôle ci-dessous vérifie sur toutes les lignes que
# ticket détermine un magasin, une date et un client, et qu'aucun champ nécessaire ne manque.
# Les répétitions de lignes d'un même ticket sont conservées ; aucun dédoublonnage ticket-produit.
# %%
header_columns=['ss_ticket_number','ss_store_sk','ss_sold_date_sk','ss_customer_sk','ss_net_paid']
header_nulls=sales.agg(*[F.sum(F.col(c).isNull().cast('long')).alias(c) for c in header_columns]).first().asDict()
transactions=sales.groupBy('ss_ticket_number').agg(
    F.countDistinct('ss_store_sk').alias('stores'),F.countDistinct('ss_sold_date_sk').alias('dates'),
    F.countDistinct('ss_customer_sk').alias('customers'),F.count('*').alias('line_count'),
    F.sum('ss_net_paid').alias('transaction_net_paid'),F.sum('ss_quantity').alias('transaction_units')).cache()
qualification={
    'nulls':header_nulls,'distinct_tickets':sales.select('ss_ticket_number').distinct().count(),
    'negative_ticket_ids':sales.filter('ss_ticket_number < 0').count(),
    'tickets_multiple_stores':transactions.filter('stores != 1').count(),
    'tickets_multiple_dates':transactions.filter('dates != 1').count(),
    'tickets_multiple_customers':transactions.filter('customers != 1').count(),
    'distinct_ticket_store_date_customer':sales.select(*header_columns[:4]).distinct().count(),
    'nonpositive_quantity_lines':sales.filter('ss_quantity <= 0 OR ss_quantity IS NULL').count(),
    'nonpositive_date_keys':sales.filter('ss_sold_date_sk <= 0').count(),
    'net_plus_tax_mismatch':sales.filter(~F.col('ss_net_paid_inc_tax').eqNullSafe(F.col('ss_net_paid')+F.col('ss_ext_tax'))).count(),
    'net_after_coupon_mismatch':sales.filter(~F.col('ss_net_paid').eqNullSafe(F.col('ss_ext_sales_price')-F.col('ss_coupon_amt'))).count(),
    'source_hashes':sorted(r[0] for r in sales.select('_source_sha256').distinct().collect()),
    'silver_run_ids':sorted(r[0] for r in sales.select('_run_id').distinct().collect()),
    'reference_source_j1_sha256':'7e0a7f16b47483741754bb641c92601dd7384dacc8331d0bcfb8abac82ed3d2e'}
qualification['valid_key']=not any(header_nulls.values()) and all(qualification[k]==0 for k in [
    'negative_ticket_ids','tickets_multiple_stores','tickets_multiple_dates','tickets_multiple_customers',
    'nonpositive_quantity_lines','nonpositive_date_keys','net_plus_tax_mismatch','net_after_coupon_mismatch'])
save('preuves/analyses/qualification_transactions.json',qualification)
assert qualification['valid_key'], 'K03/K04 non validés : voir qualification_transactions.json ; aucune donnée source modifiée'
assert qualification['source_hashes']==[qualification['reference_source_j1_sha256']], 'Périmètre différent de la source initiale J1'
assert qualification['silver_run_ids']==[BATCH]
transaction_totals=transactions.agg(F.count('*').alias('transactions'),F.sum('transaction_net_paid').alias('net_paid'),
    F.sum('line_count').alias('sales_lines'),F.sum('transaction_units').alias('units'),
    F.avg(F.col('transaction_net_paid').cast('decimal(30,12)')).alias('basket_mean'),
    F.min('line_count').alias('min_lines'),F.max('line_count').alias('max_lines'),
    F.sum((F.col('line_count')>1).cast('long')).alias('multiline_tickets')).first().asDict()
basket_exact_ratio=transaction_totals['net_paid']/Decimal(transaction_totals['transactions'])
basket_display=transaction_totals['basket_mean'].quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)
transaction_totals.update(basket_exact_ratio=basket_exact_ratio,basket_display=basket_display,
    key='canal magasin constant + ss_ticket_number',scope='initial complet, avant retours',
    repetitions_preserved=counts['store_sales']-sales.select('ss_ticket_number','ss_item_sk').distinct().count())
distribution=transactions.groupBy('line_count').agg(F.count('*').alias('tickets')).orderBy('line_count').collect()
export('analytics/outputs/repartition_lignes_par_ticket.csv',distribution)
save('analytics/outputs/transactions.json',transaction_totals)
print(json.dumps(qualification,ensure_ascii=False,indent=2))
print(json.dumps(transaction_totals,ensure_ascii=False,indent=2,default=str))
# %% [markdown]
# Les en-têtes sont qualifiés avant de calculer les KPI. Le hash de provenance Silver est confronté à
# l'inventaire initial J1. Les dates sont ici contrôlées comme clés d'en-tête ; la résolution calendaire
# du même fichier avait été validée au J1, sans nouvelle analyse temporelle ni jointure J4.
# HT reprend la définition UC-01 et les identités net + taxe = TTC, vente - coupon = net sont revérifiées.
# ## KPI métier et volume technique secondaire
# %%
kpi = [
    {'code':'K01','nom':'Net payé HT avant retours','valeur':totals['net_paid'],'unite':'unités monétaires','formule':'SUM(ss_net_paid)','origine':'UC-01'},
    {'code':'K02','nom':'Unités vendues','valeur':totals['units'],'unite':'unités','formule':'SUM(ss_quantity)','origine':'UC-01'},
    {'code':'K03','nom':'Transactions magasin distinctes','valeur':transaction_totals['transactions'],'unite':'transactions','formule':'COUNT(*) après GROUP BY ss_ticket_number qualifié','origine':'UC-01'},
    {'code':'K04','nom':'Panier moyen HT par transaction','valeur':transaction_totals['basket_mean'],'unite':'UM par transaction','formule':'AVG(SUM(ss_net_paid) par ticket qualifié)','origine':'UC-01'},
    {'code':'J4-L01','nom':'Nombre de lignes de vente','valeur':totals['sales_lines'],'unite':'lignes','formule':'COUNT(*)','origine':'Ajout J4, indicateur de volume'}]
export('analytics/outputs/kpi.csv',kpi)
save('analytics/outputs/totaux.json',totals)
print(pd.DataFrame(kpi).to_string(index=False))
# %% [markdown]
# K01 à K04 reprennent les définitions du Jour 1, limitées ici aux ventes magasin initiales.
# J4-L01 ajoute un volume de faits ; il ne mesure ni tickets ni clients. Aucun filtre, aucune imputation,
# aucune déduplication ni fusion du refresh. K04 est la moyenne des paniers regroupés, pas la moyenne par ligne.
# %%
nulls = {name:df.agg(*[F.sum(F.col(c).isNull().cast('long')).alias(c) for c in df.columns]).first().asDict() for name,df in frames.items()}
stats = []
for name,df,columns in [('store_sales',sales,['ss_quantity','ss_net_paid']),('ventes_par_produit',gold,['quantity_sold','net_paid','sales_line_count'])]:
    for column in columns:
        # Médiane exacte : moyenne décimale des une/deux valeurs centrales ordonnées par Spark.
        n = df.filter(F.col(column).isNotNull()).count()
        middle = [n//2+1] if n%2 else [n//2,n//2+1]
        ranked = df.select(F.col(column).cast('decimal(30,2)').alias('value')).filter('value is not null')
        ranked.createOrReplaceTempView('median_input')
        median = spark.sql('SELECT avg(value) FROM (SELECT value, row_number() over (order by value) rn FROM median_input) WHERE rn IN ('+','.join(map(str,middle))+')').first()[0]
        row = df.agg(F.min(column).alias('min'),F.max(column).alias('max'),F.avg(column).alias('mean'),F.sum(column).alias('sum'),F.stddev_pop(column).alias('stddev_pop')).first().asDict()
        stats.append({'jeu':name,'colonne':column,'lignes':counts[name],'non_null':n,'couverture_pct':Decimal(n)*100/Decimal(counts[name]),'median_exact':median,**row})
export('analytics/outputs/statistiques.csv',stats)
entities = {
    'produits_silver_distincts':items.select('i_item_sk').distinct().count(),
    'produits_vendus_distincts':sales.select('ss_item_sk').distinct().count(),
    'produits_gold_distincts':gold.select('ss_item_sk').distinct().count(),
    'magasins_distincts':sales.select('ss_store_sk').distinct().count(),
    'produits_sans_vente':items.join(sales.select('ss_item_sk').distinct(),items.i_item_sk==F.col('ss_item_sk'),'left_anti').count(),
    'ticket_produit_repetitions':counts['store_sales']-sales.select('ss_ticket_number','ss_item_sk').distinct().count(),
    'profils_signes':sales.agg(*[F.sum((F.col(c)<0).cast('long')).alias(c+'_negatifs') for c in ['ss_quantity','ss_net_paid','ss_net_profit']], F.sum((F.col('ss_net_paid')==0).cast('long')).alias('net_paid_zero')).first().asDict()}
save('analytics/outputs/qualite.json', {'nulls':nulls,'entites':entities})
print(pd.DataFrame(stats).to_string(index=False))
print(json.dumps(entities,ensure_ascii=False,indent=2))
# %% [markdown]
# Les moyennes et médianes de Silver décrivent les lignes ; celles de Gold décrivent les produits.
# La médiane est calculée sur les rangs centraux, sans approximation ni transfert des faits dans Pandas.
# L'écart-type de population utilise le calcul flottant Spark, les sommes monétaires restent décimales.
# Les zéros, valeurs négatives et absences sont inventoriés ; aucune absence n'est convertie en zéro.
# %%
assert totals['net_paid'] > 0
products = gold.select('ss_item_sk','i_product_name','i_category','quantity_sold','net_paid','sales_line_count').withColumn(
    'contribution_pct',(F.col('net_paid')/F.lit(totals['net_paid'])*100).cast('decimal(24,12)')).orderBy(F.desc('net_paid'),'ss_item_sk')
product_rows = products.collect()
export('analytics/outputs/contributions_produits.csv',product_rows)
top = products.limit(10).toPandas()
export('analytics/outputs/top10_produits.csv',product_rows[:10])
top_share = sum(r['net_paid'] for r in product_rows[:10])/totals['net_paid']*100
top100_share = sum(r['net_paid'] for r in product_rows[:100])/totals['net_paid']*100
concentration = {'top10_pct':top_share,'top100_pct':top100_share,'leader':product_rows[0].asDict(),
                 'somme_parts_pct':sum(r['contribution_pct'] for r in product_rows)}
save('analytics/outputs/concentration.json',concentration)
print(top.to_string(index=False))
print('Contribution top 10 (%) :',top_share,'; top 100 (%) :',top100_share)
# %% [markdown]
# Analyse 1 - Question : quels produits contribuent le plus au net payé magasin ?
# Cette analyse précise Q03 (produits par canal) et Q05 (net payé) du DAT J1, pour le canal magasin.
# Le classement porte sur net_paid, pas sur quantity_sold ni ss_net_profit. Les identifiants distinguent
# les éventuels homonymes. Une contribution élevée ne prouve pas une rentabilité élevée.
# %%
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,ax = plt.subplots(figsize=(11.5,7.2))
labels = [f"{int(r.ss_item_sk)} - {str(r.i_product_name)[:32]}" for r in top.itertuples()]
values = [float(x) for x in top['net_paid']]
ax.barh(labels[::-1],values[::-1],color='#425d72')
ax.set_xlim(left=0)
ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x/1000:,.0f}'.replace(',',' ')))
ax.set_xlabel('Net payé HT avant retours (milliers d’unités monétaires)')
ax.set_ylabel('Clé produit réelle - libellé Gold')
ax.set_title('Les dix produits contribuant le plus au net payé magasin',pad=14)
ax.grid(axis='x',alpha=.18)
fig.text(.02,.015,f'Source : Gold J3 ; TPCx-BB synthétique ; lot {BATCH}.\nSélection : 10 / 17 820 produits, ordre net payé décroissant ; aucune période calendaire filtrée.',fontsize=9)
fig.tight_layout(rect=(0,.075,1,1))
fig.savefig(ROOT/'analytics/visualisations/top10_produits.png',dpi=180)
assert list(ax.containers[0].datavalues)==values[::-1]
display(Image(filename=str(ROOT/'analytics/visualisations/top10_produits.png')))
plt.close(fig)
# %% [markdown]
# Le diagramme présente les dix plus forts montants sur l'ensemble du lot et conserve un axe à zéro.
# Le CSV adjacent contient les valeurs exactes et les parts. La faible ou forte concentration doit
# être appréciée à partir de la part top 10 affichée, et non de la seule ressemblance des dix barres.
# %%
stores = sales.groupBy('ss_store_sk').agg(F.sum('ss_net_paid').alias('net_paid'),F.sum('ss_quantity').alias('quantity_sold'),F.count('*').alias('sales_line_count')).withColumn(
    'contribution_pct',(F.col('net_paid')/F.lit(totals['net_paid'])*100).cast('decimal(24,12)')).orderBy(F.desc('net_paid'),'ss_store_sk')
store_rows = stores.collect()
export('analytics/outputs/ventes_par_magasin.csv',store_rows)
assert len(store_rows)<=100, 'Réduire le graphique avant transfert vers Pandas'
store_pdf = stores.toPandas()
store_summary = {'nombre':len(store_rows),'premier':store_rows[0].asDict(),'dernier':store_rows[-1].asDict(),
                 'ecart_net_paid':store_rows[0]['net_paid']-store_rows[-1]['net_paid'],
                 'rapport_max_min':store_rows[0]['net_paid']/store_rows[-1]['net_paid'] if store_rows[-1]['net_paid'] else None}
save('analytics/outputs/comparaison_magasins.json',store_summary)
print(store_pdf.to_string(index=False))
# %% [markdown]
# Analyse 2 - Question : comment les montants et quantités se répartissent-ils entre magasins ?
# Cette déclinaison de Q05 et du besoin du responsable magasin Q07 conserve uniquement ss_store_sk,
# faute de dimension store qualifiée dans le périmètre Silver retenu. Les montants et quantités sont
# comparés sur les mêmes faits. Les écarts ne sont pas corrigés de la taille, des jours d'ouverture ou du trafic.
# %%
fig,(ax1,ax2)=plt.subplots(2,1,figsize=(11.5,8),sharex=True)
x=store_pdf['ss_store_sk'].map(lambda n:str(int(n))).tolist()
money=[float(n) for n in store_pdf.net_paid]
units=store_pdf.quantity_sold.tolist()
ax1.bar(x,money,color='#425d72')
ax2.bar(x,units,color='#777777')
for axis in (ax1,ax2):
    axis.set_ylim(bottom=0)
    axis.grid(axis='y',alpha=.18)
    axis.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{v/1e6:.1f}'.replace('.',',')))
ax1.set_ylabel('Net payé HT\n(millions d’UM)')
ax2.set_ylabel('Quantités\n(millions d’unités)')
ax2.set_xlabel('Identifiant réel du magasin (ordre décroissant du net payé)')
ax1.set_title('Répartition des montants et quantités entre magasins',pad=13)
fig.text(.02,.012,f'Source : Silver store_sales J3 ; TPCx-BB synthétique ; lot {BATCH}.\nTous les magasins du lot ; 667 579 lignes ; aucune période calendaire filtrée. UM : unités monétaires.',fontsize=9)
fig.tight_layout(rect=(0,.075,1,1))
fig.savefig(ROOT/'analytics/visualisations/ventes_par_magasin.png',dpi=180)
assert list(ax1.containers[0].datavalues)==money
assert list(ax2.containers[0].datavalues)==units
display(Image(filename=str(ROOT/'analytics/visualisations/ventes_par_magasin.png')))
plt.close(fig)
# %% [markdown]
# Les deux panneaux permettent de distinguer valeur monétaire et volume sans les mélanger dans un axe.
# Les noms de magasins ne sont pas inventés. Les valeurs exactes figurent dans ventes_par_magasin.csv.
# Une différence observée dans le kit synthétique ne démontre pas une différence de performance commerciale.
# %% [markdown]
# ## Analyse complémentaire - Contribution des catégories
# Le Gold J3 est regroupé directement par i_category, sans nouvelle jointure ni modification des fichiers.
# Les catégories nulles ou vides seraient conservées explicitement comme groupe manquant.
# %%
category_missing=gold.filter(F.col('i_category').isNull() | (F.trim('i_category')=='')).count()
categories=gold.groupBy('i_category').agg(F.sum('net_paid').alias('net_paid'),
    F.sum('quantity_sold').alias('quantity_sold'),F.sum('sales_line_count').alias('sales_line_count'),
    F.count('*').alias('product_count')).withColumn('contribution_pct',
    (F.col('net_paid').cast('decimal(17,2)')/F.lit(totals['net_paid'])*100).cast('decimal(24,12)')).orderBy(F.desc('net_paid'),'i_category')
category_rows=categories.collect()
assert len(category_rows)<=40, 'Réduire la restitution avant conversion Pandas'
export('analytics/outputs/ventes_par_categorie.csv',category_rows)
category_pdf=categories.toPandas()
category_summary={'count':len(category_rows),'missing_products':category_missing,
    'music_books_net_paid':sum(r['net_paid'] for r in category_rows if r['i_category'] in ['Music','Books'])}
category_summary['music_books_pct']=category_summary['music_books_net_paid']/totals['net_paid']*100
save('analytics/outputs/categories.json',category_summary)
print(category_pdf.to_string(index=False))
print('Contribution Music + Books :',category_summary['music_books_pct'],'%')
# %% [markdown]
# Ces parts portent sur le net payé, tandis que quantity_sold décrit le volume. Elles n'indiquent pas la
# rentabilité. Une concentration ne justifie pas seule un changement de stock : demande, marges et disponibilité
# doivent être examinées sur des données réelles avant toute recommandation commerciale.
# %%
fig,ax=plt.subplots(figsize=(11.5,6.8))
category_labels=[str(x) if pd.notna(x) and str(x).strip() else '(catégorie manquante)' for x in category_pdf.i_category]
category_values=[float(x) for x in category_pdf.contribution_pct]
ax.barh(category_labels[::-1],category_values[::-1],color='#425d72')
ax.set_xlim(left=0)
ax.set_xlabel('Contribution au net payé HT avant retours (%)')
ax.set_ylabel('Catégorie réelle du Gold')
ax.set_title('Contribution des catégories aux ventes magasin',pad=14)
ax.grid(axis='x',alpha=.18)
for i,value in enumerate(category_values[::-1]):
    ax.text(value+.3,i,f'{value:.2f} %'.replace('.',','),va='center',fontsize=10)
ax.set_xlim(right=max(category_values)*1.16)
fig.text(.02,.012,f'Source : Gold ventes_par_produit J3 ; TPCx-BB synthétique ; lot {BATCH}.\nToutes les catégories ; aucune période calendaire filtrée. Parts calculées sur 1 150 529 586,37 UM (devise non établie).',fontsize=9)
fig.tight_layout(rect=(0,.085,1,1))
fig.savefig(ROOT/'analytics/visualisations/ventes_par_categorie.png',dpi=180)
assert list(ax.containers[0].datavalues)==category_values[::-1]
display(Image(filename=str(ROOT/'analytics/visualisations/ventes_par_categorie.png')))
plt.close(fig)
# %% [markdown]
# La lecture par catégories apporte des libellés métier compréhensibles tout en conservant les deux figures initiales.
# Les totaux et parts sont réconciliés ci-dessous ; la concentration observée reste celle d'un jeu synthétique.
# %%
checks=[]
def check(name,actual,expected):
    ok=actual==expected
    checks.append({'controle':name,'observe':str(actual),'attendu':str(expected),'statut':'OK' if ok else 'ECHEC'})
    assert ok,(name,actual,expected)

for key,expected in {'sales_lines':667579,'units':33755474,'net_paid':Decimal('1150529586.37')}.items():
    check('Silver référence J3 '+key,totals[key],expected)
    check('Gold vs Silver '+key,gold_totals[key],totals[key])
    field={'sales_lines':'sales_line_count','units':'quantity_sold','net_paid':'net_paid'}[key]
    check('Magasins vs Silver '+key,sum(r[field] for r in store_rows),totals[key])
check('Clé item unique',entities['produits_silver_distincts'],counts['item'])
check('Clé Gold unique',entities['produits_gold_distincts'],counts['ventes_par_produit'])
check('Ventes sans produit',sales.join(items,sales.ss_item_sk==items.i_item_sk,'left_anti').count(),0)
check('Lot Gold',sorted(r[0] for r in gold.select('_run_id').distinct().collect()),[BATCH])
for name,cols in [('store_sales',['ss_net_paid','ss_quantity','ss_store_sk','ss_item_sk']),('ventes_par_produit',['net_paid','quantity_sold','sales_line_count','ss_item_sk'])]:
    for col in cols:
        check(name+' nulls '+col,nulls[name][col],0)
recalculated=sales.groupBy('ss_item_sk').agg(F.sum('ss_net_paid').alias('money_check'),F.sum('ss_quantity').alias('units_check'),F.count('*').alias('rows_check'))
comparison=gold.join(recalculated,'ss_item_sk','full')
bad=comparison.filter(~F.col('net_paid').eqNullSafe(F.col('money_check')) | ~F.col('quantity_sold').eqNullSafe(F.col('units_check')) | ~F.col('sales_line_count').eqNullSafe(F.col('rows_check'))).count()
check('Chaque produit Gold vs agrégation Silver',bad,0)
check('Somme parts produits proche de 100',abs(concentration['somme_parts_pct']-Decimal(100))<Decimal('0.0000001'),True)
check('Somme parts magasins proche de 100',abs(sum(r['contribution_pct'] for r in store_rows)-Decimal(100))<Decimal('0.0000001'),True)
check('Graphique 1 et CSV top10',len(top),10)
check('Graphique 2 et CSV magasins',len(store_pdf),entities['magasins_distincts'])
check('En-tête transaction qualifié',qualification['valid_key'],True)
check('Provenance initiale J1',qualification['source_hashes'],[qualification['reference_source_j1_sha256']])
check('K03 vs référence J1',transaction_totals['transactions'],89100)
check('Tickets vs en-têtes composites',transaction_totals['transactions'],qualification['distinct_ticket_store_date_customer'])
check('Tickets multilignes vs J1',transaction_totals['multiline_tickets'],82713)
check('Répétitions ticket-produit conservées',transaction_totals['repetitions_preserved'],4136)
for field in ['net_paid','units','sales_lines']:
    check('Paniers vs Silver '+field,transaction_totals[field],totals[field])
check('K04 moyenne paniers vs quotient exact',abs(transaction_totals['basket_mean']-basket_exact_ratio)<Decimal('0.000000000001'),True)
check('K04 arrondi centime vs J1',basket_display,Decimal('12912.79'))
check('Catégories manquantes',category_missing,0)
check('Nombre de catégories',len(category_rows),9)
for field,expected in [('net_paid',totals['net_paid']),('quantity_sold',totals['units']),('sales_line_count',totals['sales_lines']),('product_count',counts['ventes_par_produit'])]:
    check('Catégories réconciliation '+field,sum(r[field] for r in category_rows),expected)
check('Somme parts catégories proche de 100',abs(sum(r['contribution_pct'] for r in category_rows)-Decimal(100))<Decimal('0.0000001'),True)
check('Graphique 3 et CSV catégories',len(category_pdf),len(category_rows))
export('preuves/analyses/controles.csv',checks)
save('preuves/analyses/validation.json',{'checks':checks,'count':len(checks),'all_passed':all(c['statut']=='OK' for c in checks),'batch':BATCH,'mode':MODE})
print(pd.DataFrame(checks).to_string(index=False))
# %% [markdown]
# Les totaux sont confrontés aux références J3, aux trois mesures Gold et à tous les magasins.
# Chaque produit Gold est aussi rapproché d'une nouvelle agrégation Silver. Les vérifications graphiques
# comparent les valeurs tracées aux petits tableaux ; la lisibilité fait l'objet d'une inspection visuelle séparée.
# %%
conclusion={'version':'J4 V2','kpi':kpi,'transactions':transaction_totals,'qualification':qualification,'categories':category_summary,'concentration':concentration,'magasins':store_summary,'statistiques':stats,'entites':entities,'controles':len(checks)}
save('analytics/outputs/synthese.json',conclusion)
print('Net payé :',totals['net_paid'],'UM ; unités :',totals['units'],'; lignes :',totals['sales_lines'])
print('Top 10 :',round(top_share,4),'% ; magasins :',entities['magasins_distincts'],'; contrôles OK :',len(checks))
print('Transactions :',transaction_totals['transactions'],'; panier moyen HT :',basket_display,'UM ; catégories :',len(category_rows))
spark.stop()
# %% [markdown]
# ## Conclusion et limites
# Les résultats sont réconciliés sur le lot J3. Les quatre KPI métier et le volume technique ont des grains distincts.
# Le classement produit, la comparaison des magasins et les catégories éclairent les questions retenues.
# Avant une décision commerciale réelle, il faudrait des données réelles, une devise confirmée,
# une période métier et les facteurs de contexte magasin. Le taux de retour K12 reste suspendu ;
# les données de retours et leur rattachement ne sont pas dans ces trois Parquet.
# Aucune analyse mensuelle ni marge n'est déduite de clés temporelles ou de coûts non qualifiés.
# Azure relève exclusivement de l'étude UC-07 ; aucun service Azure n'est déployé.
