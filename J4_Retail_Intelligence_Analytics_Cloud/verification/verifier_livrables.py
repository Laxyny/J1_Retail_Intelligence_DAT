"""Contrôles indépendants des résultats sauvegardés et des onze livrables du TP4."""
import base64
import csv
import hashlib
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from pathlib import Path
from PIL import Image
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]

REQUIREMENTS=[
 ('J4-01','Inventaire analytique',['documentation/inventaire_analytique.md','documentation/schemas.md','preuves/analyses/inventaire.json'],'J4-P02','Schémas, grain, volumes et provenance relus'),
 ('J4-02','Dictionnaire des KPI',['documentation/dictionnaire_kpi.md','analytics/outputs/kpi.csv','analytics/outputs/transactions.json','preuves/analyses/qualification_transactions.json'],'J4-P03 / J4-P17','K01 à K04 qualifiés ; J4-L01 secondaire conservé'),
 ('J4-03','Analyses statistiques',['documentation/statistiques.md','analytics/outputs/statistiques.csv','analytics/outputs/qualite.json'],'J4-P04','Cinq profils, couverture, sommes et médianes'),
 ('J4-04','Analyses métier',['documentation/analyses_metier.md','analytics/outputs/top10_produits.csv','analytics/outputs/ventes_par_magasin.csv','analytics/outputs/ventes_par_categorie.csv'],'J4-P05 / J4-P18','Produits et magasins conservés ; catégories ajoutées'),
 ('J4-05','Visualisations',['analytics/visualisations/top10_produits.png','analytics/visualisations/ventes_par_magasin.png','analytics/visualisations/ventes_par_categorie.png'],'J4-P06 / J4-P18','Trois PNG lisibles, données de tracé contrôlées'),
 ('J4-06','Synthèse décisionnelle',['documentation/synthese_decisionnelle.md'],'J4-P07','Deux constats avec limites et recommandations'),
 ('J4-07','Architecture Azure',['cloud/architecture/architecture_azure.md','cloud/architecture/architecture_azure.png','cloud/architecture/architecture_locale.png','cloud/architecture/comparaison_services.md'],'J4-P10','Cible et local distincts ; responsabilités et composants comparés'),
 ('J4-08','Organisation ADLS Gen2',['cloud/adls_gen2/organisation.md'],'J4-P11','Zones, chemins, HNS, conservation et traçabilité'),
 ('J4-09','Sécurité',['cloud/securite/matrice_acces.md'],'J4-P12','Cinq profils, cinq zones, RBAC/ACL et limites locales'),
 ('J4-10','Preuves Azure',['cloud/simulation/scenario_non_execute.md','cloud/simulation/couts_risques.md','preuves/architecture/azure_ineligibilite_recadree.png'],'J4-P09 / J4-P13','Simulation documentée autorisée en parcours B ; preuve de refus réelle'),
 ('J4-11','README J4',['README.md'],'J4-P14','Prérequis, paramètres, reproduction, arrêt et limites')]

def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def rows(path):
    with (ROOT/path).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def main(calculs_seuls=False):
    assert len(REQUIREMENTS)==11
    checks=[]
    def check(name,condition):
        checks.append({'controle':name,'statut':'OK' if condition else 'ECHEC'})
        assert condition,name
    products=rows('analytics/outputs/contributions_produits.csv')
    stores=rows('analytics/outputs/ventes_par_magasin.csv')
    categories=rows('analytics/outputs/ventes_par_categorie.csv')
    transactions=load('analytics/outputs/transactions.json')
    qualification=load('preuves/analyses/qualification_transactions.json')
    kpi=rows('analytics/outputs/kpi.csv')
    check('Quatre KPI métier et un indicateur secondaire', [r['code'] for r in kpi]==['K01','K02','K03','K04','J4-L01'])
    check('K01 valeur CSV',Decimal(kpi[0]['valeur'])==Decimal('1150529586.37'))
    check('K02 valeur CSV',int(kpi[1]['valeur'])==33755474)
    check('J4-L01 valeur CSV',int(kpi[4]['valeur'])==667579)
    check('K03 valeur CSV',int(kpi[2]['valeur'])==transactions['transactions']==89100)
    expected_mean=Decimal('1150529586.37')/Decimal(89100)
    check('K04 quotient indépendant Decimal',abs(Decimal(kpi[3]['valeur'])-expected_mean)<Decimal('0.000000000001'))
    check('K04 arrondi au centime',Decimal(kpi[3]['valeur']).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)==Decimal('12912.79'))
    check('Paniers totalisent K01',Decimal(transactions['net_paid'])==Decimal(kpi[0]['valeur']))
    check('Complétude en-tête',not any(qualification['nulls'].values()))
    check('Clé transaction qualifiée',qualification['valid_key'] and all(qualification[c]==0 for c in ['tickets_multiple_stores','tickets_multiple_dates','tickets_multiple_customers','negative_ticket_ids','nonpositive_quantity_lines','nonpositive_date_keys','net_plus_tax_mismatch','net_after_coupon_mismatch']))
    check('En-têtes composites et tickets distincts',qualification['distinct_ticket_store_date_customer']==qualification['distinct_tickets']==89100)
    distribution=rows('analytics/outputs/repartition_lignes_par_ticket.csv')
    check('Distribution tickets exhaustive',sum(int(r['tickets']) for r in distribution)==89100)
    check('Distribution lignes exhaustive',sum(int(r['line_count'])*int(r['tickets']) for r in distribution)==667579)
    check('Multilignes et répétitions conservés',sum(int(r['tickets']) for r in distribution if int(r['line_count'])>1)==82713 and transactions['repetitions_preserved']==4136)
    with (ROOT/'preuves/provenance/J1_kpi_valeurs.csv').open(encoding='utf-8-sig') as f:
        j1={r['kpi']:r for r in csv.DictReader(f,delimiter=';') if r['lot']=='data' and r['perimetre']=='Magasin'}
    check('K03 vs preuve J1',Decimal(kpi[2]['valeur'])==Decimal(j1['K03']['valeur']))
    check('K04 vs preuve J1 non arrondie',abs(Decimal(kpi[3]['valeur'])-Decimal(j1['K04']['valeur']))<Decimal('0.000000000001'))
    with (ROOT/'preuves/provenance/J1_inventaire.csv').open(encoding='utf-8-sig') as f:
        original=next(r for r in csv.DictReader(f,delimiter=';') if r['lot']=='data' and r['table']=='store_sales')
    check('Provenance initiale J1 vérifiée',qualification['source_hashes']==[original['sha256']] and int(original['lignes'])==667579)
    check('Clés produits sauvegardées uniques',len(products)==len({r['ss_item_sk'] for r in products})==17820)
    for scope,data in [('produits',products),('magasins',stores),('catégories',categories)]:
        for field,expected in [('net_paid',Decimal('1150529586.37')),('quantity_sold',Decimal(33755474)),('sales_line_count',Decimal(667579))]:
            check('Somme CSV indépendante '+scope+' '+field,sum(Decimal(r[field]) for r in data)==expected)
        check('Contributions recomputées '+scope,all(abs(Decimal(r['contribution_pct'])-Decimal(r['net_paid'])/Decimal('1150529586.37')*100)<Decimal('0.000000000002') for r in data))
    category_check=defaultdict(lambda:{'net_paid':Decimal(0),'quantity_sold':0,'sales_line_count':0,'product_count':0})
    for r in products:
        aggregate=category_check[r['i_category']]
        aggregate['net_paid']+=Decimal(r['net_paid'])
        aggregate['quantity_sold']+=int(r['quantity_sold'])
        aggregate['sales_line_count']+=int(r['sales_line_count'])
        aggregate['product_count']+=1
    check('Neuf catégories non manquantes',len(categories)==9 and all(r['i_category'].strip() for r in categories) and load('analytics/outputs/categories.json')['missing_products']==0)
    check('Chaque catégorie recomputée depuis les produits',all(all(Decimal(r[c])==Decimal(v) for c,v in category_check[r['i_category']].items()) for r in categories) and set(category_check)=={r['i_category'] for r in categories})
    check('Somme parts catégories',abs(sum(Decimal(r['contribution_pct']) for r in categories)-100)<Decimal('0.0000001'))
    stats=rows('analytics/outputs/statistiques.csv')
    for field in ['net_paid','quantity_sold','sales_line_count']:
        stat=next(r for r in stats if r['jeu']=='ventes_par_produit' and r['colonne']==field)
        values=sorted(Decimal(r[field]) for r in products)
        median=(values[8909]+values[8910])/2
        check('Médiane Gold recomputée '+field,Decimal(stat['median_exact'])==median)
        check('Bornes Gold recomputées '+field,Decimal(stat['min'])==values[0] and Decimal(stat['max'])==values[-1])
    top=rows('analytics/outputs/top10_produits.csv')
    check('Classement top10',top==sorted(products,key=lambda r:(-Decimal(r['net_paid']),int(r['ss_item_sk'])))[:10])
    spark_validation=load('preuves/analyses/validation.json')
    spark_checks=rows('preuves/analyses/controles.csv')
    check('Contrôles Spark V2 tous réussis',spark_validation['all_passed'] and len(spark_checks)==45 and all(r['statut']=='OK' for r in spark_checks))
    old_checks=load('verification/correction_v2/sauvegarde.json')
    backup=Path(old_checks['path'])
    if backup.is_dir():
        initial=json.loads((backup/'preuves/analyses/validation.json').read_text(encoding='utf-8'))
        check('26 contrôles initiaux réexécutés', {r['controle'] for r in initial['checks']} <= {r['controle'] for r in spark_checks})
        for name in ['top10_produits','ventes_par_magasin']:
            check('Graphique initial conservé '+name,(ROOT/f'analytics/visualisations/{name}.png').read_bytes()==(backup/f'analytics/visualisations/{name}.png').read_bytes())
    notebook=load('analytics/notebooks/TP4_Retail_Intelligence.ipynb')
    check('Format notebook 4',notebook['nbformat']==4)
    code=[c for c in notebook['cells'] if c['cell_type']=='code']
    check('Notebook exécuté dans l’ordre',all(c['execution_count']==i+1 for i,c in enumerate(code)))
    check('Aucune erreur notebook',all(o['output_type']!='error' for c in code for o in c.get('outputs',[])))
    images=[o['data']['image/png'] for c in code for o in c.get('outputs',[]) if 'data' in o and 'image/png' in o['data']]
    check('Trois images dans le notebook',len(images)==3)
    for name,embedded in zip(['top10_produits','ventes_par_magasin','ventes_par_categorie'],images):
        p=ROOT/f'analytics/visualisations/{name}.png'
        check('Pixels notebook et PNG '+name,base64.b64decode(''.join(embedded) if isinstance(embedded,list) else embedded)==p.read_bytes())
        im=Image.open(p);im.verify()
        check('PNG haute résolution '+name,Image.open(p).width>=1500)
    check('Quatorze questions',len(re.findall(r'^## \d+\.',(ROOT/'documentation/questions_recul.md').read_text(encoding='utf-8'),re.M))==14)
    security=(ROOT/'cloud/securite/matrice_acces.md').read_text(encoding='utf-8')
    check('Sécurité documentée',all(s in security for s in ['Administrateur','Service ingestion','Data Engineer','Analyste métier','Service restitution','RBAC','ACL','simple']))
    check('Simulation explicite','non exécutée' in (ROOT/'cloud/simulation/scenario_non_execute.md').read_text(encoding='utf-8'))
    if calculs_seuls:
        (ROOT/'verification/correction_v2/validation_calculs.json').write_text(json.dumps({'checks':checks,'all_passed':True,'count':len(checks)},ensure_ascii=False,indent=2),encoding='utf-8')
        print(len(checks),'contrôles de calculs, provenance et notebook V2 OK, avant régénération PDF.')
        return
    pdf=PdfReader(ROOT/'rapport/DAT_Retail_Intelligence_J4.pdf')
    check('PDF texte et pagination',len(pdf.pages)>5 and all(p.extract_text().strip() for p in pdf.pages))
    pdf_text='\n'.join(p.extract_text() for p in pdf.pages)
    check('PDF V2 et KPI concordants',all(s in pdf_text for s in ['Version améliorée V2','89 100','12 912,79','1 150 529 586,37','33 755 474','Music','Books','71,86','Contribution des catégories']))
    check('PDF anciennes exclusions K03/K04 retirées','cette analyse J4 ne reconduit pas cette qualification' not in pdf_text and 'K03 et K04 sont seulement non retenus' not in pdf_text)
    for code_,label,files,proof,description in REQUIREMENTS:
        check(code_+' fichiers complets',all((ROOT/f).is_file() and (ROOT/f).stat().st_size>50 for f in files))
    if (ROOT/'preuves/environnement/protection_apres.json').exists():
        check('617 fichiers antérieurs identiques',load('preuves/environnement/protection_avant.json')==load('preuves/environnement/protection_apres.json'))
        check('Listings HDFS inchangés',(ROOT/'preuves/environnement/hdfs_avant.txt').read_bytes()==(ROOT/'preuves/environnement/hdfs_apres.txt').read_bytes())
    result={'version':'J4 V2','spark_checks':spark_validation['count'],'checks':checks,'all_passed':True,'count':len(checks),'livrables_verifies':11,'notebook_code_cells':len(code),'notebook_png':len(images),'pdf_pages':len(pdf.pages),
            'limits':['Mode local J4 portable non exécuté','Azure documentaire uniquement','Sécurité de production non testée','Recalcul nécessite le lot J3 externe']}
    (ROOT/'verification/controle_final.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    tracker='# Suivi des exigences - TP4 §13.1\n\nLes onze intitulés ci-dessous sont ceux du TP4. J4-10 « Preuves Azure » est satisfait par la simulation admise au §9.2.\n\n'
    tracker+='| Code | Livrable / exigence | Fichiers | Preuves | Vérification réalisée | Statut / limite |\n| --- | --- | --- | --- | --- | --- |\n'
    for code_,label,files,proof,description in REQUIREMENTS:
        limit='Documentaire : aucun Azure déployé' if code_ in ['J4-07','J4-08','J4-09','J4-10'] else 'Données synthétiques, lot J3 externe pour recalcul'
        tracker+='| '+' | '.join([code_,label,' ; '.join(files),proof,description,'Vérifié ; '+limit])+' |\n'
    tracker+='\nContrôle indépendant V2 : '+str(len(checks))+' vérifications réussies, plus les '+str(spark_validation['count'])+' contrôles Spark réexécutés. La validation documentaire ne revendique aucune exécution Azure.\n'
    tracker+='Les PNG, pages PDF et HTML du notebook font également l’objet d’une inspection visuelle consignée dans verification/revue_visuelle.md.\n'
    (ROOT/'verification/suivi_exigences.md').write_text(tracker,encoding='utf-8')
    ledger='''# Registre des preuves J4

| Identifiant | Description | Fichier(s) | Exigence TP4 | Statut |
| --- | --- | --- | --- | --- |
| J4-P01 | Versions, session et environnement existant | preuves/environnement/environnement.json ; requirements.lock.txt ; java.txt ; docker.txt | §1, §12.1 | Exécuté et contrôlé |
| J4-P02 | Lecture HDFS, schémas, volumes et fichiers | preuves/analyses/inventaire.json ; documentation/schemas.md | J4-01 | Exécuté et contrôlé |
| J4-P03 | Quatre KPI métier et volume technique secondaire | analytics/outputs/kpi.csv ; preuves/analyses/controles.csv | J4-02 | Exécuté et contrôlé en V2 |
| J4-P04 | Statistiques et absences | analytics/outputs/statistiques.csv ; qualite.json | J4-03 | Exécuté et contrôlé |
| J4-P05 | Agrégats produit et magasin | analytics/outputs/contributions_produits.csv ; ventes_par_magasin.csv | J4-04 | Exécuté et contrôlé |
| J4-P06 | Trois figures issues des petits agrégats | analytics/visualisations/*.png ; CSV associés | J4-05 | Exécuté et contrôlé en V2 |
| J4-P07 | Constats, recommandations et limites | documentation/synthese_decisionnelle.md | J4-06 | Étudié et contrôlé |
| J4-P08 | Notebook intégralement exécuté et export lisible | analytics/notebooks/TP4_Retail_Intelligence.ipynb ; .html ; preuves/analyses_execution.log | §9.1.4, §12.1 | Exécuté et contrôlé |
| J4-P09 | Refus Azure authentique recadré sans identifiants | preuves/architecture/azure_ineligibilite_recadree.png ; provenance_capture.md | Parcours B, J4-10 | Contrôlé |
| J4-P10 | Architectures réelle et cible, correspondance | cloud/architecture/*.svg, *.png et fichiers MD | J4-07 | Local démontré ; cible étudiée |
| J4-P11 | Organisation logique ADLS et HNS | cloud/adls_gen2/organisation.md | J4-08 | Étudié et contrôlé |
| J4-P12 | Matrice cible et mécanismes locaux observés | cloud/securite/matrice_acces.md ; preuves/environnement/hdfs_*.txt | J4-09 | Cible étudiée ; local observé |
| J4-P13 | Scénario Azure et postes de coûts | cloud/simulation/*.md | J4-10 | Simulé documentairement, non exécuté |
| J4-P14 | Reproduction et arrêt conservant les volumes | README.md | J4-11 | Contrôlé ; autre poste non testé |
| J4-P15 | Réconciliations et validation indépendante | preuves/analyses/validation.json ; verification/controle_final.json | §12 | Exécuté et contrôlé |
| J4-P16 | Préservation antérieure et intégrité de remise | preuves/environnement/protection_*.json ; hdfs_*.txt ; MANIFESTE_REMISE.json dans la remise ; verification/integrite_archive.json hors ZIP | Contraintes de conservation / remise | Contrôlé après constitution de la remise |
| J4-P17 | Qualification des tickets et calcul des paniers | preuves/analyses/qualification_transactions.json ; analytics/outputs/transactions.json ; repartition_lignes_par_ticket.csv ; preuves/provenance/J1_*.csv | K03 / K04 | Exécuté et contrôlé en V2 |
| J4-P18 | Contribution des neuf catégories | analytics/outputs/ventes_par_categorie.csv ; categories.json ; analytics/visualisations/ventes_par_categorie.png | J4-04 / J4-05 | Exécuté et contrôlé en V2 |
| J4-P19 | Sauvegarde et journal correctif | verification/correction_v2/sauvegarde.json ; journal_changements.md ; preservation.json | Protection et traçabilité | Contrôlé en V2 |

Les schémas sont des dessins documentaires, les graphiques des résultats Matplotlib et la seule capture Azure est celle de l'utilisateur.
Les journaux ne sont pas transformés en fausses captures de terminal. Les preuves Azure simulées ne prouvent aucun accès ni déploiement.
'''
    (ROOT/'preuves/registre_preuves.md').write_text(ledger,encoding='utf-8')
    print(len(checks),'vérifications indépendantes OK ; 11/11 livrables contrôlés ;',len(pdf.pages),'pages PDF.')

if __name__=='__main__':
    import sys
    main('--calculs' in sys.argv)
