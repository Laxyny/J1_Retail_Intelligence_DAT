"""Compose les livrables textuels depuis les résultats réellement enregistrés."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parent


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))


def write(path,text):
    (ROOT/path).parent.mkdir(parents=True,exist_ok=True)
    (ROOT/path).write_text(text.strip()+'\n',encoding='utf-8')


def table(headers,rows):
    def cell(x):
        return str(x).replace('|',' / ').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers)]+[
        '| '+' | '.join(cell(c) for c in row)+' |' for row in rows])


def number(value):
    return f'{value:,}'.replace(',',' ')


def main():
    run=read('preuves/controles/J3-P06-transformation.json')
    inv=read('preuves/controles/inventaire_python.json')['sources']
    schemas=read('configuration/parametres/schemas.json')
    config=read('configuration/parametres/execution.json')
    profiles={t:read(f'preuves/controles/J3-P04-{t}.json') for t in ['store_sales','item']}
    verified=read('preuves/controles/J3-P10-verification.json')
    assert verified['status']=='OK' and verified['failed']==0
    ident=run['run_id']
    checks=run['checks']
    statuses=Counter(c['status'] for c in checks)
    with (ROOT/'preuves/controles/registre_qualite.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(checks[0]))
        writer.writeheader();writer.writerows(checks)
    env='''# Fiche environnement

Exécution le 18 novembre 2026 (Europe/Paris). Les journaux Docker utilisent UTC, soit une heure de moins à cette date. Les identifiants de lots portent l'heure UTC.

'''+table(['Composant','Valeur observée'],[
        ['Hôte','Windows 11 Professionnel 10.0.26200 ; 16 380 056 Kio de RAM totale'],
        ['Virtualisation','WSL2, distribution docker-desktop ; moteur Linux Docker Desktop'],
        ['Docker Desktop / Engine','4.84.0 / 29.6.2'],
        ['Ressources du moteur','16 processeurs visibles ; 8 126 324 736 octets de RAM'],
        ['Conteneur Spark','retail-j3-spark ; limite 4 Gio et 4 CPU ; aucun port publié'],
        ['Système Spark','Ubuntu 24.04.4 LTS ; image existante retail-j2-hadoop:3.5.0'],
        ['Python traitement','3.12.3 ; /tmp/retail-j3-venv/bin/python'],
        ['Java traitement','Temurin OpenJDK 17.0.18, déjà installé dans l’image J2'],
        ['Spark / PySpark / Py4J','3.5.7 / 3.5.7 / 0.10.9.7'],
        ['Hadoop serveur / client Spark','3.5.0 / 3.3.4 embarqué ; accès RPC réellement testé'],
        ['Mode Spark','local[2], driver 1 536 Mio, shuffle 4 partitions, UI désactivée'],
        ['Notebook','nbclient 0.10.4, nbformat 5.10.4, ipykernel 6.31.0 ; nbconvert 7.16.6'],
        ['Jupyter interactif','Pas de serveur JupyterLab installé ; notebook exécuté par nbclient'],
        ['HDFS','hdfs://hdfs:9000, NameNode et DataNode dans retail-j2-hdfs-1 ; un DataNode vivant'],
        ['HDFS stockage','Volumes retail-j2_namenode et retail-j2_datanode conservés ; réplication J3 à 1'],
        ['NiFi','Conteneur J2 existant, resté arrêté ; aucune modification de configuration'],
        ['Windows Java / Python rapport','Java 21.0.2 non utilisé pour Spark ; Python fourni 3.12.14 pour documentation']])+'''

## Validation réelle

J3-P02 prouve la lecture HDFS de reason.dat, 35 lignes, printSchema, trim, écriture et relecture Parquet. Les traitements complets J3-P06 et la relecture autonome J3-P10 confirment ensuite le fonctionnement sur les données retenues. L'avertissement NativeCodeLoader indique l'utilisation des classes Java de remplacement ; il n'a pas empêché les écritures ni les relectures.

## Réparation minimale autorisée

Le dossier J2 est actuellement sous J1. Le conteneur existant pointait vers l'ancien chemin Projet/J2_Retail_Intelligence_Ingestion/installation/hadoop. Docker y avait créé deux dossiers vides portant les noms des XML. Après autorisation explicite de l'utilisateur, ces deux dossiers vides ont été déplacés dans configuration/restauration_montages et remplacés par des copies identiques des XML actuels. Les fichiers originaux et les volumes n'ont pas été modifiés par cette réparation. Le NameNode et le DataNode existants ont ensuite été démarrés. Le mode sûr de démarrage s'est désactivé automatiquement. Aucun formatage n'a été lancé.

Les deux fichiers reason.dat J2 sont contrôlés par SHA-256 avant et après le travail. Les autres fichiers pédagogiques, J1/J2 et sources Windows sont protégés par un manifeste de 158 fichiers de contenu, avec 173 métadonnées Git recensées séparément.

## Références techniques

Compatibilité Java 17 / Python 3.8+ vérifiée dans la documentation officielle [Spark 3.5.7](https://spark.apache.org/docs/3.5.7/) et [Installation PySpark 3.5.7](https://spark.apache.org/docs/3.5.7/api/python/getting_started/install.html). Le client Hadoop embarqué n'est pas remplacé par les bibliothèques du serveur. La compatibilité utilisée ici est démontrée par les tests HDFS ; cela ne vaut pas certification de toutes les fonctionnalités Hadoop.
'''
    write('configuration/environnement.md',env)
    inventory='''# Inventaire technique des sources

Les deux sources de traitement sont des données structurées : store_sales et item, lot initial complet. Aucun échantillonnage du traitement. Le refresh item a été examiné séparément pour lever l'incertitude sur la couverture, puis exclu du pipeline. Il contient 180 lignes, clés 17 820 à 17 999 ; toutes les ventes initiales utilisent 0 à 17 819, déjà présents dans item initial.

## Localisation vérifiée

Racine du kit sur Windows :

'''+str(PROJECT/'01. Architecture DataLake, DataWarehouse, Lakehous/retail_project/retail_project')+'''

Montage en lecture seule dans Spark : /sources. Racine des nouveaux dépôts HDFS :

'''+config['sources']['store_sales']['hdfs'].rsplit('/',1)[0]+'''

'''+table(['Source / lot','Lignes et champs','Octets','Granularité'],[
        [k,f"{number(v['rows'])} / {next(iter(v['field_counts']))}",number(v['bytes']),
         'Ligne de vente magasin' if 'store_sales' in k else 'Enregistrement produit par clé de substitution'] for k,v in inv.items()])+'''

Format vérifié sur toutes les lignes : DAT texte délimité par |, sans en-tête, fins CRLF. Le décodage UTF-8 strict réussit et aucun octet non ASCII n'est rencontré : ASCII est compatible UTF-8 ; on ne peut pas distinguer davantage les encodages compatibles sur ce contenu. Le split conserve les derniers champs vides. Chaque ligne retenue a exactement 23 ou 22 champs ; aucun séparateur terminal surnuméraire n'est retiré arbitrairement.

## Schéma ordinal fiable

Les positions ci-dessous proviennent du DDL des tables temporaires Hive de l'Annexe G de TPCx-BB 1.7.0, pages 125 et 131-132. Le dictionnaire de J1 a été recopié puis revalidé contre une nouvelle copie du PDF officiel dans preuves/consignes. La section B.1 n'a pas servi à supposer l'ordre physique. La version exacte du générateur du kit local reste inconnue ; la largeur, le typage, les relations et les égalités de montants corroborent la correspondance.

Référence : [TPCx-BB 1.7.0, juin 2025](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPCX-BB_v1.7.0.pdf). Le script verification/verifier_reference.py conserve l'empreinte du PDF et vérifie les deux listes ordinales.
'''
    for t in ['store_sales','item']:
        inventory+='\n## Dictionnaire '+t+'\n\n'+table(['Position physique','Colonne','Type Raw interprété / Silver'],[
            [i,n,'string ISO / date' if n in ['i_rec_start_date','i_rec_end_date'] else typ] for i,(n,typ) in enumerate(schemas[t]['columns'],1)])+'\n'
    inventory+='''
## Clés et anomalies

ss_item_sk et i_item_sk sont des bigint / long et représentent la clé de substitution produit. i_item_sk est unique et non nul : 17 820 clés pour 17 820 lignes ; le minimum est zéro. Les 667 579 références de vente sont rapprochées sans ambiguïté. ss_ticket_number × ss_item_sk présente 4 136 répétitions au-delà de la première occurrence ; il ne constitue pas une clé unique de ligne. Aucun doublon exact n'a été constaté, avec deux méthodes exhaustives (empreintes de lignes Python et distinct Spark). La clé i_item_id est conservée mais n'est pas utilisée pour la jointure.

Les colonnes ventes sont numériques : identifiants, quantité entière, 12 montants decimal(7,2). Aucun champ temporel calendaire n'est directement présent dans store_sales ; les clés de date et d'heure restent des références. item contient 8 colonnes numériques et 14 chaînes à la lecture, dont deux dates ISO converties en Silver.

Les listes de nulls, extrema, domaines et empreintes sont conservées dans inventaire_python.json et J3-P04-*.json. Les valeurs atypiques et champs manquants sont détaillés dans le rapport qualité. Les valeurs Unknown et N/A du référentiel restent des libellés sources, pas des nulls inventés.
'''
    write('documentation/inventaire_sources.md',inventory)
    model=f'''# Modèle Silver et Gold

## Question métier et continuité

Le DAT J1, partie 2, Q03, demande quels produits se vendent le plus par canal (K02, unités vendues). Q05 et K01 définissent le net payé des ventes avant retours. Le Jour 3 prépare cette lecture pour le canal magasin initial : quels produits cumulent les quantités et montants nets les plus importants ? Il ne reproduit pas les 27 KPI. Le stockage HDFS de J2 est réutilisé ; NiFi n'est pas requis pour ce traitement.

## Chaîne exécutée

Sources Windows en lecture seule, contrôles physiques Python, nouvelles copies Raw HDFS vérifiées par SHA-256, exploration PySpark, règles écrites, conversions et normalisation, Silver Parquet relu, jointure contrôlée, agrégation, Gold Parquet relu, réconciliation indépendante et contrôles finaux.

## Silver

store_sales : les 23 colonnes natives typées, sans déduplication, plus _source_uri, _source_sha256, _source_batch, _run_id. Grain : une ligne du fichier de ventes, qui peut partager son couple ticket-produit avec une autre ligne distincte. 667 579 lignes acceptées, zéro rejet et zéro correction de texte ; toutes les lignes sont typées et tracées.

item : 22 colonnes natives, textes trim, dates de validité converties en date, mêmes quatre colonnes de provenance. Grain : un enregistrement par i_item_sk dans ce lot. 17 820 lignes acceptées, dont 2 575 corrigées uniquement pour espaces périphériques et 15 245 sans cette correction ; zéro rejet. Les 17 820 dates de début sont harmonisées en date ; les fins nulles restent nulles.

Chaque ligne acceptée est conservée. Les rejets, s'il en existe sur un autre lot, sont écrits dans quality/j3 avec un motif. Aucun fichier de rejets vide artificiel n'est créé pour cette exécution.

## Jointure et calcul

Jointure gauche : store_sales.ss_item_sk = item.i_item_sk. Relation plusieurs-vers-un, attendue et vérifiée. Types long, dimension unique, aucune clé requise nulle. Avant : {run['join']['before']} ; après : {run['join']['after']} ; sans correspondance : {run['join']['unmatched']}. Le grain de vente est conservé avant agrégation. L'enrichissement est une étape intermédiaire, sans troisième Silver artificiel.

## Gold : ventes_par_produit

Grain final : une ligne par clé de substitution produit du lot initial, dans le canal magasin. La clé n'est pas assimilée à une gamme ni à un produit commercial durable à travers toutes ses versions. Dimensions : ss_item_sk, i_product_name, i_category, i_brand. Ces attributs sont fonctionnellement dépendants de la clé dans le référentiel vérifié.

'''+table(['Mesure','Formule','Type observé'],[
        ['quantity_sold','SUM(ss_quantity)','bigint / long'],
        ['net_paid','SUM(ss_net_paid)','decimal(17,2)'],
        ['sales_line_count','COUNT(*)','bigint / long']])+f'''

Trois colonnes de traçabilité : _run_id, _source_sales_sha256, _source_item_sha256. Aucun filtre de signe ni remplacement des nulls facultatifs. Les lignes rejetées selon R03 seraient exclues de Gold, mais leur nombre est zéro ici. Aucun calcul de prix unitaire moyen, taux de retour ou résultat net réel de l'entreprise n'est ajouté.

Sorties validées :

- {config['silver']}/store_sales
- {config['silver']}/item
- {config['gold']}/ventes_par_produit

Seul le lot {ident} est la publication complète validée. Les deux essais précédents ne contiennent que Silver ventes et ne doivent pas être lus avec un glob englobant tous les lots.

## Limites

Les montants sont exprimés en unités monétaires du kit, sans devise attestée. Le net payé est avant retours, sans déduire une seconde fois coupons ou remises déjà pris en compte. L'agrégat est descriptif sur le lot initial et ne constitue ni chiffre d'affaires réel d'une enseigne ni benchmark officiel. Aucun calendrier n'est joint ; aucune période civile nouvelle n'est déduite des clés numériques de vente. Les lots refresh ne sont pas fusionnés.
'''
    write('documentation/modele_silver_gold.md',model)
    results='# Résultats analytiques constatés\n\n'+table(['Mesure sur les ventes initiales magasin','Résultat'],[
        ['Lignes de vente',number(run['totals']['rows'])],['Unités vendues',number(run['totals']['quantity'])],
        ['Net payé, unités monétaires du kit','1 150 529 586,37'],['Clés produit représentées','17 820']])+'''

Classement décroissant du net payé ; égalités départagées par clé produit. Les noms du kit sont synthétiques ; la clé stable permet le contrôle.

'''+table(['Rang / clé produit','Quantité','Net payé (UM)','Lignes'],[
        [f"{i} / {r['ss_item_sk']}",number(r['quantity_sold']),r['net_paid'],number(r['sales_line_count'])]
        for i,r in enumerate(run['top10'],1)])+'''

Le premier produit est la clé 10 000 : 454 954 unités, 15 408 393,55 UM et 9 029 lignes. Ce classement décrit le kit initial ; il ne suffit pas à recommander un assortiment réel. Tous les totaux et chacune des 17 820 lignes produit ont été rapprochés d'un groupement Python indépendant utilisant Decimal, sans pandas. Zéro écart de quantité, de montant ou de nombre de lignes.
'''
    write('documentation/resultats.md',results)
    fmt='''# Comparaison des formats et contrôle Parquet

DAT est ici du texte délimité, comparable à un CSV sans en-tête. JSON est étudié et utilisé pour paramètres, contrôles et traces ; il n'est pas présenté comme une source native des ventes.

'''+table(['Critère','DAT / CSV','JSON','Parquet'],[
        ['Organisation','Enregistrements en lignes, séparateur |','Objets et tableaux','Colonnes binaires'],
        ['Types','Schéma externe à appliquer','Types primitifs, date et Decimal à encadrer','Types persistés dans le fichier'],
        ['Compression','Sources non comprimées','Traces lisibles non comprimées','Snappy effectivement utilisé'],
        ['Lisibilité','Lecture humaine possible','Lecture humaine possible','Lecture via Spark ou outil Parquet'],
        ['Analyse','Parsing et scans texte','Adapté aux structures imbriquées','Projection de colonnes et agrégations'],
        ['Limite','En-tête absent ; ordre à prouver','Plus verbeux ; pas de Decimal natif universel','Binaire ; gestion de table à organiser']])+'''

## Volumes réellement mesurés

'''+table(['Jeu','Texte source (octets)','Parquet (octets)','Lignes relues'],[
        ['Silver ventes',inv['data/store_sales']['bytes'],run['outputs']['silver_store_sales']['bytes'],run['outputs']['silver_store_sales']['rows_after']],
        ['Silver produits',inv['data/item']['bytes'],run['outputs']['silver_item']['bytes'],run['outputs']['silver_item']['rows_after']],
        ['Gold par produit','Pas de texte équivalent exporté',run['outputs']['gold_ventes_par_produit']['bytes'],run['outputs']['gold_ventes_par_produit']['rows_after']]])+'''

Pour Silver ventes, Parquet représente 37,48 % du volume DAT ; pour Silver produits, 52,52 %. Ces rapports comparent les sources aux sorties typées, avec provenance et normalisation ajoutées : ce n'est pas une expérience de compression à schéma strictement identique, ni un test de vitesse. La réduction Gold reflète surtout l'agrégation ; on ne l'attribue pas à la compression seule. Les volumes HDFS sont logiques, hors métadonnées du système de fichiers ; réplication 1.

## Vérifications exécutées

Pour chacune des trois sorties : écriture errorifexists, fichiers part-*.snappy.parquet et marqueur _SUCCESS présents, relecture Spark, égalité des noms et types, nombre de lignes avant/après identique. Les schémas complets avant et après sont dans J3-P08-parquet.json. Les champs de provenance déclarés non nullables par les expressions peuvent devenir nullables après lecture Parquet ; cette différence de métadonnée est documentée, pas masquée.

Deux sommes de fragments d'empreinte SHA-256 de chaque ligne sérialisée, incluant les nulls, sont calculées avant et après relecture. Elles sont égales pour les trois sorties et tiennent compte des multiplicités de lignes. Ce contrôle probabiliste n'est pas une preuve mathématique d'identité de tous les enregistrements ; il comporte un risque théorique de collision. Les sommes métier sont contrôlées séparément, dont une réconciliation indépendante pour chaque produit.

## Incident et correction

Les deux premières tentatives de contrôle par exceptAll restent en attente avec des tâches non terminées ; les lectures simples fonctionnent. Les journaux et états de threads sont conservés. Désactiver l'optimisation adaptative n'a pas résolu le problème et n'a pas été retenu. Le contrôle a été remplacé par schémas, volumes, empreintes agrégées et réconciliations métier, puis exécuté avec succès. La cause interne exacte du blocage n'est pas déterminée. Les sorties d'essai sont conservées et identifiées comme non validées ; aucune n'est écrasée.

## Garanties

Parquet stocke des fichiers typés en colonnes. Il ne fournit pas, à lui seul, de transactions multi-fichiers ACID, d'upsert métier, de contrôle de concurrence ni d'historique de table. Les lots uniques et errorifexists évitent nos écrasements, mais ne constituent pas une couche transactionnelle. Aucune installation Delta, Iceberg ou Hudi n'a été réalisée.
'''
    write('documentation/comparaison_formats.md',fmt)
    quality=f'''# Rapport qualité

Périmètre exhaustif : deux fichiers initiaux, 667 579 lignes ventes et 17 820 lignes produit, puis trois sorties relues. Les affichages de cinq ou dix lignes sont uniquement des aperçus. Le registre détaillé est disponible dans preuves/controles/registre_qualite.csv et J3-P09-qualite.json : identifiant, règle, cible, résultat numérique, attendu, statut, méthode, justification et limites.

## Bilan des contrôles

{len(checks)} contrôles enregistrés : '''+', '.join(f'{n} {s}' for s,n in statuses.items())+'''. Zéro contrôle bloquant en échec ne signifie pas absence d'anomalies. Les valeurs nulles facultatives et la non-unicité du couple ticket-produit restent explicitement signalées.

'''+table(['Dimension','Résultat exécuté','Décision'],[
        ['Complétude','Nulls par colonne contrôlés sur tout le fichier','Conservation des nulls facultatifs ; aucun zéro imputé'],
        ['Types','0 conversion impossible ; échelle décimale contrôlée','Schémas explicites ; arrêt en cas d’erreur'],
        ['Unicité produit','17 820 clés distinctes / 17 820 lignes','Dimension utilisable pour jointure'],
        ['Doublons exacts','0 ventes ; 0 produits','Aucune déduplication'],
        ['Clé ticket-produit','4 136 répétitions au-delà du premier couple','Clé candidate refusée ; lignes conservées'],
        ['Référentiel','0 vente non rapprochée ; même volume avant/après','Jointure plusieurs-vers-un vérifiée'],
        ['Cohérence monétaire','0 écart net + taxe ; 0 écart prix × quantité','Montants cohérents pour ces deux identités'],
        ['Valeurs signées','495 971 profits négatifs ; 0 quantité ou net payé négatif','Aucune exclusion au seul motif du signe'],
        ['Parquet','3 sorties lisibles ; schémas/types et volumes contrôlés','Empreintes égales ; réconciliation métier séparée'],
        ['Réconciliation','0 écart sur les 17 820 produits vs Python Decimal','Agrégats acceptés sur ce périmètre']])+'''

## Valeurs manquantes

'''+table(['Source','Champ','Nulls','Part du fichier'],[
        [t,n,v,f'{100*v/profiles[t]["rows"]:.4f} %'] for t in profiles for n,v in profiles[t]['nulls'].items() if v])+'''

Les 17 820 fins de validité produit vides sont maintenues comme valeurs ouvertes/inconnues, sans inventer une date de fin. Quatre descriptions, huit identifiants de marque et six libellés de marque manquent. Le groupement Gold garde le produit, même si sa marque manque. Un null de marque n'entraîne donc pas de perte de vente.

## Domaines et valeurs atypiques

Les quantités vont de 1 à 100, le net payé de 0,00 à 18 745,00 et le résultat de -9 866,60 à 9 134,00 UM. Ces bornes sont observées, pas imposées comme règle universelle à d'autres lots. Les clés produit vont de 0 à 17 819. Neuf catégories sont présentes ; les unités comprennent des libellés tels que Unknown et N/A et i_container vaut Unknown dans tout le référentiel. Aucune conversion d'unités n'est déduite de ces codes. Les dates ISO présentes passent le typage ; la fin étant toujours nulle, le contrôle fin >= début ne teste pas de paire fermée.

## Volumes et grain

'''+table(['Passage','Volume','Explication'],[
        ['Raw ventes → Silver ventes','667 579 → 667 579','0 rejet, aucune déduplication'],
        ['Raw produits → Silver produits','17 820 → 17 820','2 575 lignes avec trim ; 0 rejet'],
        ['Ventes → jointure','667 579 → 667 579','0 référence absente ; pas de multiplication'],
        ['Jointure → Gold','667 579 → 17 820','Changement de grain : plusieurs ventes par produit']])+'''

Gold contient 17 820 produits, mais SUM(sales_line_count) reste 667 579. Les quantités et montants sont également conservés. Comparer directement le nombre de faits et le nombre de produits sans tenir compte du grain serait incorrect.

## Anomalies et rejets

Zéro ligne mise à l'écart dans les fichiers retenus. Les anomalies non bloquantes restent dans Silver et dans le registre. La règle d'isolement est codée pour une entrée ultérieure, sans fabriquer de faux rejets sur les données actuelles. Une erreur de type ou un conflit de clé produit arrête la publication et conserve les sources.

## Limites des contrôles

L'intégrité référentielle est vérifiée uniquement pour le lien produit utilisé. Les autres dimensions, la fraîcheur métier, les périodes civiles, les prix concurrents, les retours et la sémantique du refresh ne sont pas validés par ce pipeline. L'égalité de deux formules ne prouve pas toute la validité économique du kit. Les empreintes agrégées Parquet sont probabilistes. La relecture autonome J3-P10 s'ajoute aux 73 contrôles de transformation ; son nombre n'est pas artificiellement additionné au registre.
'''
    write('documentation/rapport_qualite.md',quality)
    questions=[
        ('Pourquoi est-il nécessaire de vérifier les schémas avant de commencer les transformations ?',"Sans en-tête, une position mal affectée pourrait transformer le prix en quantité. Nous avons vérifié 23 et 22 champs, l'ordre de l'Annexe G, les types et les identités monétaires sur tout le fichier."),
        ('Quelle différence existe entre une donnée brute, une donnée Silver et une donnée Gold ?',"Raw conserve les deux DAT et leurs empreintes. Silver garde les lignes typées, les dates et textes harmonisés, avec provenance. Gold résume les ventes au grain produit et expose quantité, net payé et nombre de lignes."),
        ("Pourquoi faut-il connaître la granularité d'une table avant de réaliser une agrégation ?","Une ligne de vente n'est pas un ticket complet. Nous additionnons les quantités de chaque ligne, puis Gold contient une ligne par clé produit. COUNT(*) mesure ici les lignes de vente et non les transactions."),
        ("Quels risques présente une jointure réalisée sur une clé supposée ?","Une dimension ayant deux lignes pour la même clé multiplierait les ventes et les montants. Nous avons vérifié l'unicité de i_item_sk, la compatibilité long, les références et 667 579 lignes avant comme après jointure."),
        ('Pourquoi ne faut-il pas supprimer automatiquement les valeurs atypiques ?',"Les 495 971 profits négatifs sont des valeurs du kit dont la négativité ne démontre pas une erreur. Les supprimer changerait le périmètre. Les 4 136 répétitions ticket-produit ne sont pas non plus des doublons exacts."),
        ("Quels contrôles permettent de vérifier la cohérence d'un jeu de données transformé ?","Comparer les volumes, les types, les nulls, les clés et les références ; réconcilier les sommes avant/après jointure et agrégation ; relire les fichiers. Ici chaque produit Gold a aussi été comparé à un calcul indépendant en Decimal."),
        ('Pourquoi Parquet est-il adapté aux usages analytiques ?',"Son organisation en colonnes permet de lire les champs utiles, de conserver les types et de compresser les valeurs. Nos trois sorties Snappy se relisent dans Spark ; Silver ventes occupe 34 766 704 octets pour 92 764 700 octets de DAT source, à schéma enrichi."),
        ("Pourquoi Parquet seul ne fournit-il pas les garanties d'une table transactionnelle Lakehouse ?","Un format de fichier ne coordonne pas les transactions sur plusieurs fichiers, les versions et les écritures concurrentes. Nos lots uniques et errorifexists préviennent les écrasements accidentels, sans offrir d'upsert ni de transaction de table."),
        ('Dans quels cas une base NoSQL pourrait-elle compléter une architecture Data Lake ?',"Pour une lecture rapide par identifiant produit, un cache de session ou des événements consultés par clé. Une base de documents ou wide-column peut servir ces accès applicatifs. Cela ne remplace pas les scans et agrégations Spark/Parquet. Aucune base NoSQL n'a été installée ici."),
        ("Quelles limites des données TPCx-BB doivent être prises en compte lors de l'interprétation des résultats ?","Le kit est synthétique, la devise et la version locale du générateur ne sont pas attestées, certains champs manquent et la fusion refresh n'est pas spécifiée. Les libellés ne décrivent pas un catalogue réel. Les conclusions portent sur les fichiers initiaux étudiés, sans causalité ni score officiel de benchmark.")]
    write('documentation/questions_recul.md','# Dix questions de recul - TP3 section 11\n\n'+'\n\n'.join(f'## {i}. {q}\n\n{a}' for i,(q,a) in enumerate(questions,1)))
    proofs=[
        ['J3-P01','Environnement et HDFS','docker version ; jps ; dfsadmin -report','NameNode/DataNode actifs ; 1 vivant ; dépôts J2 conservés','executions/J3-P01-diagnostic.txt ; captures/J3-P01-hdfs.jpg','4.4 / 8.1'],
        ['J3-P02','Session Spark complète','python scripts/exploration/test_spark.py','35 lignes reason ; transformation, Parquet et relecture','executions/J3-P02-session-spark-final.log ; controles/J3-P02-session-spark.json','4.4'],
        ['J3-P03','Accès et copies sources','python scripts/exploration/preparer_entrees.py','2 DAT déposés sans écrasement ; SHA-256 égaux','executions/J3-P03-entrees.log ; controles/J3-P03-entrees-hdfs.json','4.5 / 8.1'],
        ['J3-P04','Exploration exécutée','python scripts/exploration/notebook.py','5 cellules code exécutées ; schémas, nulls et domaines','notebooks/UC06_exploration.ipynb (racine J3) ; controles/J3-P04-*.json ; captures/J3-P04-notebook.jpg','4.6 / 8.5'],
        ['J3-P05','Jointure contrôlée','cellule 4 du notebook','667 579 avant/après ; 0 clé dupliquée ; 0 référence absente','controles/J3-P05-jointure-exploration.json ; captures/J3-P05-bilan.jpg','4.8.3'],
        ['J3-P06','Transformations et Silver','python scripts/transformation/transformer.py','2 Silver relus ; 2 575 trims ; 0 rejet','executions/J3-P06-transformation.log ; controles/J3-P06-transformation.json','4.7-4.9'],
        ['J3-P07','Gold analytique','même pipeline, groupBy produit','17 820 agrégats ; top 10 et totaux conservés','controles/J3-P06-transformation.json (top10, totals, outputs)','4.10 / 8.3'],
        ['J3-P08','Écriture/relecture Parquet','parquet_checked ; hdfs dfs -ls et -du','3 jeux relus ; volumes et types conformes','parquet/J3-P08-parquet.json ; parquet/J3-P08-listing-hdfs.txt','4.11 / 8.4'],
        ['J3-P09','Qualité et calcul indépendant','assertions du pipeline et inventaire Python','73 contrôles ; 0 bloquant en échec ; anomalies signalées','controles/J3-P09-qualite.json ; controles/registre_qualite.csv','4.12 / 8.2 / 8.5'],
        ['J3-P10','Relecture autonome','python scripts/qualite/verifier.py','Sorties, totaux, notebook et SHA-256 reason J2 vérifiés','executions/J3-P10-verification.log ; controles/J3-P10-verification.json','8.1-8.5'],
        ['J3-P11','Protection et livraison','python verification/verifier_fichiers.py','158 fichiers de contenu protégés ; présence des livrables contrôlée','controles/J3-P11-verification-fichiers.json','4.13 / 10.2'],
        ['J3-P12','Refus de réécriture du même lot','Relance transformer.py avec le paramétrage du lot final','Arrêt avant écriture : Lot déjà présent, code 1 attendu','executions/J3-P12-reexecution-refusee.log','4.13 / sécurité des écritures']]
    write('preuves/index.md','# Registre des preuves\n\nLes chemins ci-dessous sont relatifs à preuves/, sauf mention explicite. Les captures sont des images authentiques du navigateur ; les journaux et résultats JSON constituent les preuves numériques reproductibles.\n\n'+table(['ID','Objectif','Commande / manipulation','Résultat réel','Fichier de preuve','TP'],proofs)+'''

## Captures complémentaires facultatives

Les captures fournies montrent HDFS, le notebook exécuté et le bilan des références. Aucune capture manuelle indispensable ne reste à réaliser. Pour un oral, ouvrir un terminal et lancer la relecture autonome, puis capturer le schéma Gold et les totaux. La commande exacte se trouve dans le README. Une capture d'un export HTML du notebook est identifiée comme telle et ne prétend pas montrer un serveur JupyterLab actif.

## Incidents conservés

J3-P06-tentative-initiale.log, J3-P06-tentative-r2.log, spark-thread-diagnostic.txt et spark-thread-diagnostic-r2.txt conservent les essais non validés et leur diagnostic. Le dernier lot r3 est le seul lot final. Les avertissements Java natifs sont présents dans les journaux, sans être effacés.
''')
    readme=rf'''# Retail Intelligence Platform - Jour 3 - UC-06

Travail exécuté sur les fichiers initiaux complets : 667 579 ventes magasin et 17 820 produits. Deux Silver et un Gold sont disponibles dans HDFS en Parquet Snappy. Le notebook a été exécuté de haut en bas. Le pipeline enregistre 73 contrôles, sans échec bloquant, et conserve les anomalies documentées. Livrable de synthèse : rapport/DAT_Retail_Intelligence_J3.pdf ; version modifiable : rapport/DAT_Retail_Intelligence_J3.md.

## 1. Prérequis et versions

Windows, PowerShell, Docker Desktop démarré en mode Linux/WSL2, environnement HDFS J2 conservé. Python de traitement 3.12.3, Java 17.0.18, Spark/PySpark 3.5.7, Hadoop serveur 3.5.0 et client Spark 3.3.4. Détails et limites de compatibilité : configuration/environnement.md. Aucun Java Windows n'a été remplacé. Aucun port Spark ou Jupyter n'est exposé.

## 2. Chemins réels

Racine J3 : {ROOT}

Racine J2 actuelle : {PROJECT/'J1_Retail_Intelligence_DAT/J2_Retail_Intelligence_Ingestion'}

Entrées Windows : {PROJECT/'01. Architecture DataLake, DataWarehouse, Lakehous/retail_project/retail_project/data'} ; fichiers store_sales/store_sales.dat et item/item.dat. Le conteneur Spark les voit sous /sources/data, en lecture seule. L'inventaire du refresh est informatif ; il n'est pas fusionné.

Copies Raw HDFS :

- {config['sources']['store_sales']['hdfs']}
- {config['sources']['item']['hdfs']}

Sorties finales :

- {config['silver']}/store_sales
- {config['silver']}/item
- {config['gold']}/ventes_par_produit

donnees_produites/manifest.json conserve les chemins, schémas, volumes et preuves de relecture. Les trois jeux Parquet sont aussi fournis sous donnees_produites/export, avec une copie complète validée et le manifeste détaillé sous donnees_produites/verification_export. Aucune source DAT brute n'est dupliquée dans la remise.

## 3. Démarrage et environnement isolé

Ouvrir PowerShell dans la racine J3 puis exécuter :

```powershell
& .\configuration\preparer.ps1
docker exec retail-j2-hdfs-1 hdfs dfsadmin -report
docker exec retail-j2-hdfs-1 hdfs dfsadmin -safemode get
```

Le script réutilise le conteneur HDFS et crée seulement retail-j3-spark s'il est absent. Il utilise le réseau retail-j2_default, l'image J2 déjà présente et un venv /tmp/retail-j3-venv. Aucun volume HDFS n'est monté directement dans Spark : les lectures/écritures passent par l'API HDFS. Le script n'installe les dépendances que si le venv manque. Le fichier configuration/requirements.lock.txt fixe toutes les versions Python observées.

Si HDFS vient de démarrer, attendre sa sortie automatique du mode sûr avant d'écrire. Si le démarrage échoue à cause des montages XML, consulter la fiche environnement ; ne pas reconstruire les volumes. Les deux chemins historiques ont été restaurés une fois, avec l'accord explicite de l'utilisateur. NiFi reste arrêté et n'est pas requis ici.

## 4. Relecture des résultats existants, sans nouveau lot

```powershell
docker exec retail-j3-spark /tmp/retail-j3-venv/bin/python /work/scripts/qualite/verifier.py
```

Cette commande relit les Parquet et recalcule les totaux ; elle vérifie également le notebook et les deux dépôts J2. Elle met à jour son compte rendu local J3-P10 sans réécrire les données HDFS.

## 5. Reproduction complète et ordre

```powershell
& .\scripts\reproduire.ps1
```

Ordre : préparer l'environnement ; archiver les preuves du lot précédent ; tester Spark ; inventorier toutes les lignes physiques avec Python ; créer de nouvelles copies Raw et vérifier leurs empreintes ; construire/exécuter le notebook ; appliquer les règles et écrire Silver puis Gold ; relire et vérifier. Les dépendances et chemins sont séparés du code. Les commandes individuelles exécutées dans Docker sont :

```text
/tmp/retail-j3-venv/bin/python /work/scripts/exploration/test_spark.py
/tmp/retail-j3-venv/bin/python /work/scripts/exploration/inventorier.py --sources /sources
/tmp/retail-j3-venv/bin/python /work/scripts/exploration/preparer_entrees.py
/tmp/retail-j3-venv/bin/python /work/scripts/exploration/notebook.py
/tmp/retail-j3-venv/bin/python /work/scripts/transformation/transformer.py
/tmp/retail-j3-venv/bin/python /work/scripts/qualite/verifier.py
```

Les règles documentées s'appliquent uniquement au périmètre décrit. Toute nouvelle anomalie bloquante doit être analysée avant validation d'un nouveau lot. Le rapport existant porte sur le lot {ident} ; une nouvelle exécution ne doit pas être confondue avec ce lot dans un tableau de restitution.

## 6. Fichiers et contrôles

scripts/uc06.py : session, lecture/typage, profils, normalisation et écriture contrôlée. scripts/exploration : inventaire physique, dépôt Raw et notebook. scripts/transformation : pipeline. scripts/qualite : relecture autonome. configuration/parametres : dictionnaire ordinal et chemins. preuves/controles : inventaire, contrôles, calcul indépendant et réconciliation. preuves/parquet : schémas avant/après, volumes et fichiers. documentation : inventaire, règles, modèle, résultats, qualité, formats et dix questions. verification/suivi_exigences.md : couverture du TP.

Pour ouvrir le notebook sans environnement Jupyter, utiliser l'export HTML preuves/notebook/UC06_exploration.html dans un navigateur. Il affiche les sorties sauvegardées, sans prétendre exécuter des cellules. Pour le recalcul, utiliser le script notebook.py, qui lance nbclient dans le venv. Aucun serveur JupyterLab n'est nécessaire.

## 7. Reprise sûre et incidents

Les écritures utilisent errorifexists et des chemins identifiés par un lot UTC + suffixe aléatoire. Relancer directement transformer.py avec le même paramétrage refuse la destination existante avant toute nouvelle écriture. Une exécution complète génère un nouveau lot, dont les preuves précédentes sont copiées dans preuves/historique. Il ne faut pas agréger plusieurs versions du même fichier source : sélectionner un lot validé unique. Une archive déjà existante provoque un arrêt plutôt qu'un écrasement.

Deux premières tentatives exceptAll ont été interrompues après diagnostic, sans supprimer leurs sorties. Elles ne constituent pas des publications valides. Le lot r3 utilise des empreintes agrégées, schémas, volumes et réconciliations indépendantes. Les avertissements NativeCodeLoader et de plan tronqué n'ont pas empêché les traitements finaux. Aucun repli pandas ou local n'a été utilisé ; les données analytiques sont dans HDFS.

## 8. Régénération documentaire

La documentation a été générée sous Windows avec le Python fourni par l'application (3.12.14), ReportLab 4.4.9, pypdf et pypdfium2, sans installation globale. Si ces outils sont absents sur un autre poste, installer configuration/requirements-rapport.txt dans un venv distinct. Après un nouveau lot, régénérer les documents, le PDF et l'export HTML ; vérifier les chiffres et adapter le récit si le périmètre change.

```text
python rapport/generer_documentation.py
python rapport/exporter_pdf.py
python verification/verifier_fichiers.py
```

La dernière commande se lance sur Windows depuis J3 et contrôle les 158 fichiers de contenu protégés à partir de chemins relatifs au projet. L'empreinte originale de J1/J2 reste la référence : ne pas la remplacer après une anomalie.

## 9. Arrêt adapté

Fermer toute session notebook en cours. Les scripts appellent spark.stop. Pour arrêter uniquement Spark :

```powershell
docker stop retail-j3-spark
```

Pour arrêter aussi HDFS une fois les autres travaux terminés :

```powershell
docker exec retail-j2-hdfs-1 hdfs --daemon stop datanode
docker exec retail-j2-hdfs-1 hdfs --daemon stop namenode
docker stop retail-j2-hdfs-1
```

NiFi étant déjà arrêté, aucune action n'est nécessaire. Conserver conteneurs et volumes. Ne pas lancer de formatage ni de suppression de volumes. Le venv est conservé dans la couche du conteneur Spark tant qu'il n'est pas supprimé.

## 10. Limites connues

Lab mono-nœud, réplication 1, pas de haute disponibilité. Contrôles exhaustifs des deux sources initiales, pas de validation de tout le kit. Devise inconnue, données synthétiques, aucune sémantique de refresh inventée. Les empreintes Parquet sont des contrôles probabilistes complétés par les contrôles métier. UC-05, HBase, formats de tables transactionnels, Azure et BI Jour 4 sont exclus. Le fichier Parquet seul n'est pas une table ACID.
'''
    readme += '\n\n' + (ROOT/'documentation/export_et_remise.md').read_text(encoding='utf-8')
    write('README.md',readme)
    deliverables=[
        ['1','Fiche environnement','configuration/environnement.md','J3-P01, P02'],
        ['2','Inventaire technique','documentation/inventaire_sources.md ; configuration/parametres/schemas.json','J3-P03, P04'],
        ['3',"Notebook d'exploration",'notebooks/UC06_exploration.ipynb ; export HTML','J3-P04, P10'],
        ['4','Règles de nettoyage','documentation/regles_nettoyage.md','J3-P06'],
        ['5','Scripts PySpark','scripts/uc06.py ; exploration/ ; transformation/ ; qualite/','J3-P02, P04, P06, P10'],
        ['6','Données Silver','HDFS lot '+ident+' : store_sales et item ; donnees_produites/manifest.json','J3-P06, P08, P10'],
        ['7','Données Gold','HDFS lot '+ident+' : ventes_par_produit ; documentation/modele_silver_gold.md','J3-P07, P10'],
        ['8','Données Parquet','3 répertoires HDFS ; preuves/parquet/J3-P08-parquet.json','J3-P08, P10'],
        ['9','Rapport qualité','documentation/rapport_qualite.md ; registre_qualite.csv','J3-P09, P10'],
        ['10','README','README.md ; scripts/reproduire.ps1','J3-P11'],
        ['11','Preuves','preuves/index.md ; journaux, JSON et captures authentiques','J3-P01 à P11']]
    for entry in deliverables:
        if entry[0] in ['6','7','8']:
            entry[2] += ' ; copies Windows : donnees_produites/export ; verification_export/manifeste_export.json et controle_export.md'
            entry[3] += ' ; J3-P13'
    requirements='# Suivi des exigences - UC-06\n\nLot final : '+ident+'. La section 4.15 comporte dix livrables ; la section 10.2 ajoute explicitement la fiche environnement, soit onze éléments.\n\n## Onze livrables (section 10.2)\n\n'+table(['N°','Livrable','Fichiers / sorties','Preuves','Statut'],[r+['Réalisé et vérifié'] for r in deliverables])+'\n\n## Dix étapes (section 4)\n\n'+table(['Étape TP','Réalisation et fichier','Preuve','Statut'],[
        ['4.4 Environnement','configuration/environnement.md ; test lecture/transformation/écriture/relecture','P01-P02','Réalisé et vérifié'],
        ['4.5 Sources','Deux fichiers initiaux complets ; dictionnaire ordinal vérifié','P03-P04','Réalisé et vérifié'],
        ['4.6 Exploration','Notebook exécuté, 5 cellules de code sans erreur','P04, P10','Réalisé et vérifié'],
        ['4.7 Nettoyage','Règles préalables et impact mesuré ; 2 575 trims','P06','Réalisé et vérifié'],
        ['4.8 Transformations','Typage, normalisation, jointure et agrégation','P05-P07','Réalisé et vérifié'],
        ['4.9 Silver','Deux sorties HDFS relues','P06, P08, P10','Réalisé et vérifié'],
        ['4.10 Gold','Agrégat produit, 17 820 lignes','P07, P10','Réalisé et vérifié'],
        ['4.11 Parquet','3 écritures/relectures ; comparaison argumentée','P08','Réalisé et vérifié'],
        ['4.12 Qualité','73 contrôles, anomalies et limites','P09-P10','Réalisé et vérifié'],
        ['4.13 Organisation','Paramètres, fonctions, scripts, procédure et journaux','P11','Réalisé et vérifié']])+'\n\n## Tests section 8\n\n'+table(['Section','Vérifications réalisées','Preuves','Statut'],[
        ['8.1 Lecture','Accessibilité, formats, schémas et volumes','P02-P04','Réalisé et vérifié'],
        ['8.2 Transformation','Règles écrites, types, exécution, jointure et grain','P05-P07','Réalisé et vérifié'],
        ['8.3 Zones','Silver/Gold produits, chemins et provenance','P06-P08, P10','Réalisé et vérifié'],
        ['8.4 Parquet','Écriture, lecture, schémas et nombres de lignes','P08, P10','Réalisé et vérifié'],
        ['8.5 Qualité','Nulls, doublons, clés, anomalies et limites','P04, P09-P10','Réalisé et vérifié']])+'''

## Questions, rapport et limites

Dix questions traitées dans documentation/questions_recul.md, suivant exactement la section 11. Le DAT Markdown et le PDF réunissent les résultats, sans remplacer les scripts ni les fichiers Parquet HDFS. Les éventuelles captures complémentaires d'oral ne conditionnent pas les onze livrables : les preuves existantes comprennent des captures authentiques et les journaux d'exécution.

La couverture est celle du socle obligatoire uniquement. Les essais interrompus sont documentés et exclus du lot valide. La qualité n'est pas déclarée parfaite. Les fonctionnalités UC-05 et avancées sont exclues à la demande de l'utilisateur, sans être comptées comme des exigences obligatoires non réalisées.
'''
    write('verification/suivi_exigences.md',requirements)
    intro=f'''# DAT Retail Intelligence Platform - Jour 3

## UC-06 - Transformation, qualité et organisation des données

Kevin GREGOIRE - IPSSI - Mastère Développement, Data & IA

18 novembre 2026 - Rapport d'exécution et de synthèse

## Bilan vérifié

Deux fichiers initiaux TPCx-BB complets ont été traités par PySpark, à partir de copies Raw dans HDFS. Silver contient 667 579 lignes de ventes et 17 820 produits ; Gold contient 17 820 agrégats produit. Les fichiers Parquet Snappy ont été écrits, relus et contrôlés. Les sommes sont de 33 755 474 unités et 1 150 529 586,37 unités monétaires de net payé. Le notebook comporte cinq cellules code exécutées sans erreur.

Le registre comprend 73 contrôles de transformation, sans échec bloquant, avec des anomalies documentées. Les 2 575 corrections produit concernent uniquement des espaces périphériques. Aucun rejet ni dédoublonnage n'a été appliqué. Les 495 971 profits négatifs sont conservés. La jointure n'a ni perdu ni multiplié les lignes.

Le lot final validé est {ident}. Les deux tentatives de comparaison interrompues restent conservées et ne constituent pas des sorties valides. Les onze livrables de la section 10.2 sont disponibles ; leur couverture est détaillée en fin de rapport et dans verification/suivi_exigences.md.

## Périmètre et méthode

Ce travail couvre uniquement les dix étapes UC-06 de la section 4, les tests de la section 8, les livrables des sections 4.15/10.2 et les dix questions de la section 11. Le TP3 (56 pages) et le Cours 3 (70 pages) ont été lus intégralement. Le TP est prioritaire. Les documents J1 et J2 ont été relus pour les besoins métier et la continuité HDFS. Les extractions lisibles sont conservées dans preuves/consignes.

Le DAT J1 place les unités vendues par produit (Q03/K02) et le net payé (Q05/K01) parmi les besoins de préparation analytique. J2 avait déposé reason.dat dans HDFS et préparé les zones sans les alimenter. J3 réutilise ce stockage, préserve les dépôts et apporte les transformations. Les chiffres actuels sont recalculés ; les anciennes notes ne sont pas utilisées comme preuve de l'état courant.

UC-05, installation HBase, défis Lakehouse, formats transactionnels supplémentaires, déploiement Azure et BI Jour 4 sont exclus. Aucune installation de cluster Spark distribué n'a été réalisée. Les sources, fichiers pédagogiques et livrables J1/J2 sont préservés ; aucun formatage ni suppression de volume n'a été lancé.
'''
    intro += '\n\n## Disponibilité des données dans la remise\n\nLes véritables fichiers Parquet Silver et Gold du lot final sont fournis dans donnees_produites/export et dans A_REMETTRE_J3, avec les neuf SHA-256 HDFS/Windows, les schémas et les comptages contrôlés. Leur relecture locale par Spark a réussi sans accès HDFS. Les résultats et analyses ci-dessous sont inchangés.'
    sections=[intro,env,inventory,(ROOT/'documentation/regles_nettoyage.md').read_text(encoding='utf-8'),model,results,fmt,quality,
              (ROOT/'documentation/questions_recul.md').read_text(encoding='utf-8'),
              '# Preuves et reproductibilité\n\nLes commandes complètes figurent dans README.md. Les preuves numériques demeurent la référence reproductible. Les captures ci-après montrent le navigateur sans reconstruction de terminal.\n\n'+table(['ID','Objectif','Résultat / preuve principale'],[[r[0],r[1],r[3]+' ; '+r[4]] for r in proofs]),
              '# Couverture des livrables\n\n'+table(['N°','Livrable','Statut / preuve'],[[r[0],r[1],'Réalisé et vérifié ; '+r[3]] for r in deliverables])+'''

## Références et précautions de reprise

IPSSI, TP 3 .pdf, version 8.1 : sections 4, 8, 10.2 et 11 ; Cours 3.pdf, parties Python/PySpark, zones et Parquet. DAT J1 : Q03, Q05, K01 et K02. DAT J2 : environnement HDFS et dépôts reason.dat. Annexe G officielle TPCx-BB 1.7.0 : pages 125 et 131-132. Documentation officielle Spark 3.5.7 : compatibilité et installation.

Les 158 fichiers sources, pédagogiques et livrables existants sont vérifiés par empreinte. Les 173 métadonnées Git recensées au départ sont distinguées des contenus : un journal interne de mise à jour origin/HEAD a évolué pendant la session, sans changement de livrable ; il n'a pas été restauré. Les deux dépôts reason J2 gardent leur SHA-256 d'origine. Ne pas lire plusieurs lots de la même source comme s'ils étaient des faits additionnels ; sélectionner le lot final documenté. Toute reprise doit conserver les volumes et refuser un chemin existant. Le README précise les commandes de démarrage, relecture, reproduction et arrêt. La portée reste celle d'un lab mono-nœud et de données synthétiques, sans devise attestée ni garantie transactionnelle de table.
''']
    annex='\n\n# Annexes visuelles\n\n'+ '\n\n'.join(
        f'![{caption}](../preuves/captures/{name})' for name,caption in [
            ('J3-P01-hdfs.jpg','J3-P01 - NameNode actif'),
            ('J3-P04-notebook.jpg','J3-P04 - Notebook exécuté'),
            ('J3-P05-bilan.jpg','J3-P05 - Jointure et anomalies')])
    write('rapport/DAT_Retail_Intelligence_J3.md','\n\n---\n\n'.join(sections)+annex)
    write('rapport/sections.json',json.dumps(sections,ensure_ascii=False,indent=2))
    print('Documents générés, contrôles',len(checks),'lot',ident)


if __name__=='__main__':
    main()
