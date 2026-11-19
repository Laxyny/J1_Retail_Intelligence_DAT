# Inventaire analytique

Périmètre : fichiers initiaux synthétiques TPCx-BB traités au Jour 3, lot 20261118T113628Z-243a5fb5-r3 uniquement.
Aucun refresh n'est fusionné. Les sources DAT ne sont ni modifiées ni relues pour transformer les données.
Les volumes et types ci-dessous proviennent de la lecture Spark J4, contrôlée par le manifeste J3 copié en annexe.

| Jeu / zone | Grain | Lignes / usage |
| --- | --- | --- |
| store_sales / Silver | Une ligne de vente, sans clé de ligne validée | 667 579 ; K01, K02, J4-L01, magasins |
| item / Silver | Une clé i_item_sk par produit | 17 820 ; contrôle de couverture et unicité |
| ventes_par_produit / Gold | Un agrégat par ss_item_sk | 17 820 ; classement et contribution produits |


## Provenance et chemins

Racine locale J3 vérifiée : J3_Retail_Intelligence_Transformation, à côté de J4.
J2 est sous J1_Retail_Intelligence_DAT/J2_Retail_Intelligence_Ingestion ; son ancien chemin racine n'est pas sa copie de travail actuelle.
DAT et dictionnaire UC-01 : J1_Retail_Intelligence_DAT/J1_Retail_Intelligence_Architecture/travail/DAT_Retail_Intelligence_J1.md
et annexes/UC01_dictionnaire_KPI.xlsx. Le rapport J2 est sous rapport/DAT_Retail_Intelligence_J2.pdf dans le J2 actuel.
Le rapport J3 et son manifeste restent sous rapport/ et donnees_produites/ dans le J3 racine.
Le Compose J2 et le lanceur configuration/preparer.ps1 de J3 ont été consultés, pas modifiés ni relancés pour transformer.
Les rapports J2 et J3 confirment respectivement le test reason.dat et le traitement complet des ventes/produits.
NiFi n'est pas déclaré comme l'ingestion des faits du Jour 3.

### store_sales

Chemin de lecture réellement exécuté : `hdfs://hdfs:9000/retail-lake/silver/j3/20261118T113628Z-243a5fb5-r3/store_sales`.

Format : Parquet Snappy, deux fichiers part et un marqueur _SUCCESS par jeu selon le manifeste J3.


### item

Chemin de lecture réellement exécuté : `hdfs://hdfs:9000/retail-lake/silver/j3/20261118T113628Z-243a5fb5-r3/item`.

Format : Parquet Snappy, deux fichiers part et un marqueur _SUCCESS par jeu selon le manifeste J3.


### ventes_par_produit

Chemin de lecture réellement exécuté : `hdfs://hdfs:9000/retail-lake/gold/j3/20261118T113628Z-243a5fb5-r3/ventes_par_produit`.

Format : Parquet Snappy, deux fichiers part et un marqueur _SUCCESS par jeu selon le manifeste J3.


## Colonnes exploitées et qualité

store_sales : ss_item_sk, ss_store_sk, ss_quantity, ss_net_paid ; ss_ticket_number pour le diagnostic des répétitions,
ss_net_profit pour la conservation des signes. item : i_item_sk pour l'intégrité référentielle.
Gold : ss_item_sk, i_product_name, i_category, quantity_sold, net_paid, sales_line_count, _run_id.
Les métadonnées de provenance J3 sont conservées ; aucune jointure temporelle ni géographique n'est ajoutée.

Le Jour 3 a contrôlé 73 règles : 64 OK, 8 observations et une anomalie documentée ; aucun échec bloquant.
Le Jour 4 revérifie les mesures retenues, le lot, l'unicité des clés produit, les références et tous les agrégats produit.
4 136 répétitions du couple ticket-produit subsistent ; ce couple ne constitue pas une clé de ligne.
Les 495 971 profits négatifs et 3 954 nets payés nuls sont conservés. Aucun net payé ni quantité négative.
Les nulls facultatifs de démographie/adresse/promotion, de marque et de description sont conservés ; les fins de validité produit
restent toutes nulles. Les trois mesures analytiques et les clés produit/magasin utilisées sont complètes.
17 820 produits sont vendus ; aucun produit Silver sans vente dans ce lot. Un autre lot pourrait en contenir.

Limites : synthétique, devise inconnue, canal magasin uniquement, absence de calendrier qualifié dans les Parquet retenus,
pas de contexte de surface/traffic magasin. Les sommes sont des montants avant retours, sans mesure de profitabilité.
Les données de clients ne sont pas exportées dans les résultats analytiques remis.
Le détail machine des nulls et des fichiers lus est dans qualite.json et inventaire.json.
