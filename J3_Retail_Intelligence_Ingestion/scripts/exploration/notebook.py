"""Construit puis exécute réellement le notebook d'exploration avec nbclient."""
from pathlib import Path
import nbformat as nb
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[2]
cells = [nb.v4.new_markdown_cell('''# UC-06 - Exploration des sources TPCx-BB
Kevin GREGOIRE - IPSSI - Jour 3

Objectif : vérifier les deux fichiers initiaux complets avant nettoyage. Les chemins HDFS et empreintes sont externalisés. Le refresh produit est inventorié séparément et n'est pas intégré. Contrôles exhaustifs ; seuls les affichages show sont des échantillons.'''),
nb.v4.new_code_cell('''import sys, json
from pathlib import Path
sys.path.insert(0, '/work/scripts')
from uc06 import session, read_source, profile, save, ROOT, F
config = json.loads((ROOT/'configuration/parametres/execution.json').read_text())
spark = session('UC06-exploration')
print('Spark', spark.version, 'Python', sys.version.split()[0])
print('Mode', spark.sparkContext.master, 'Lot', config['run_id'])'''),
nb.v4.new_markdown_cell('La session utilise deux threads locaux dans Docker ; les fichiers sont lus dans HDFS. Ce mode ne constitue pas un cluster Spark distribué.')]
for table in ['store_sales','item']:
    preview = ['ss_ticket_number','ss_item_sk','ss_quantity','ss_sales_price','ss_net_paid','ss_net_profit'] if table == 'store_sales' else ['i_item_sk','i_product_name','i_category','i_rec_start_date','i_rec_end_date']
    cells.extend([nb.v4.new_markdown_cell(f'## Source : {table}\nLecture sans en-tête, séparateur |, schéma ordinal Annexe G. Les conversions sont contrôlées sur toutes les valeurs non nulles.'),
        nb.v4.new_code_cell(f'''{table}, failures_{table} = read_source(spark, '{table}', config['sources']['{table}']['hdfs'])
{table} = {table}.cache()
{table}.printSchema()
{table}.select({preview!r}).show(5, truncate=22)
p_{table} = profile({table}, '{table}')
print(json.dumps({{k:v for k,v in p_{table}.items() if k != 'schema'}}, indent=2, default=str, ensure_ascii=False))
assert not any(failures_{table}.values())
save('preuves/controles/J3-P04-{table}.json', p_{table})'''),
        nb.v4.new_markdown_cell('''Les résultats ci-dessus portent sur tout le fichier. Les clés à zéro sont présentes dans le kit et ne sont pas invalidées. Les valeurs nulles ne sont pas remplacées par zéro. Les colonnes *_sk de vente sont des références numériques, pas des dates calendaires.''')])
cells.extend([nb.v4.new_markdown_cell('## Relation produit et décisions préparatoires\nVérifier l’unicité du référentiel, les références sans correspondance et le maintien du grain vente.'),
nb.v4.new_code_cell('''key_errors = item.filter(F.col('i_item_sk').isNull() | (F.col('i_item_sk') < 0)).count()
duplicate_keys = item.count() - item.select('i_item_sk').distinct().count()
unmatched = store_sales.join(item, store_sales.ss_item_sk == item.i_item_sk, 'left_anti').count()
joined = store_sales.join(item.select('i_item_sk','i_product_name'), store_sales.ss_item_sk == item.i_item_sk, 'left')
relation = dict(key_errors=key_errors, duplicate_keys=duplicate_keys, unmatched=unmatched,
                before=store_sales.count(), after=joined.count())
assert key_errors == duplicate_keys == unmatched == 0
assert relation['before'] == relation['after']
print(relation)
save('preuves/controles/J3-P05-jointure-exploration.json', relation)'''),
nb.v4.new_markdown_cell('''La jointure initiale est vérifiée par la clé de substitution produit, avec un seul produit pour chaque clé. Le couple ticket-produit n'est pas une clé unique de ligne. Aucun dédoublonnage des ventes n'est justifié. Les résultats signés restent conservés. Les dates de fin produit nulles restent nulles ; leur absence n'est pas une erreur de conversion.'''),
nb.v4.new_code_cell('''print('Bilan :', p_store_sales['rows'], 'ventes ;', p_item['rows'], 'produits')
print('Nulls ventes :', {k:v for k,v in p_store_sales['nulls'].items() if v})
print('Valeurs signées :', p_store_sales['signed_values'])
print('Répétitions ticket-produit :', p_store_sales['ticket_item_repetitions'])
store_sales.unpersist(); item.unpersist(); spark.stop()'''),
nb.v4.new_markdown_cell('''## Conclusion
L'exploration permet de définir les règles avant application : typer les montants en décimaux, convertir les dates produit, retirer seulement les espaces périphériques et conserver les nulls facultatifs. Ne pas exclure les profits négatifs ni les répétitions ticket-produit. Les traitements Silver et Gold sont distincts de ce notebook. Les chiffres de contrôle sont sauvegardés dans preuves/controles ; le rapport documente leurs limites.''')])
notebook = nb.v4.new_notebook(cells=cells, metadata={'kernelspec':{'name':'python3','display_name':'Python 3 UC06','language':'python'}})
path = root/'notebooks/UC06_exploration.ipynb'
nb.validate(notebook)
nb.write(notebook,path)
try:
    NotebookClient(notebook,timeout=600,kernel_name='python3',resources={'metadata':{'path':str(root)}}).execute()
finally:
    nb.write(notebook,path)
nb.validate(notebook)
print('Notebook exécuté :',path)
