# Modèle Silver et Gold

## Question métier et continuité

Le DAT J1, partie 2, Q03, demande quels produits se vendent le plus par canal (K02, unités vendues). Q05 et K01 définissent le net payé des ventes avant retours. Le Jour 3 prépare cette lecture pour le canal magasin initial : quels produits cumulent les quantités et montants nets les plus importants ? Il ne reproduit pas les 27 KPI. Le stockage HDFS de J2 est réutilisé ; NiFi n'est pas requis pour ce traitement.

## Chaîne exécutée

Sources Windows en lecture seule, contrôles physiques Python, nouvelles copies Raw HDFS vérifiées par SHA-256, exploration PySpark, règles écrites, conversions et normalisation, Silver Parquet relu, jointure contrôlée, agrégation, Gold Parquet relu, réconciliation indépendante et contrôles finaux.

## Silver

store_sales : les 23 colonnes natives typées, sans déduplication, plus _source_uri, _source_sha256, _source_batch, _run_id. Grain : une ligne du fichier de ventes, qui peut partager son couple ticket-produit avec une autre ligne distincte. 667 579 lignes acceptées, zéro rejet et zéro correction de texte ; toutes les lignes sont typées et tracées.

item : 22 colonnes natives, textes trim, dates de validité converties en date, mêmes quatre colonnes de provenance. Grain : un enregistrement par i_item_sk dans ce lot. 17 820 lignes acceptées, dont 2 575 corrigées uniquement pour espaces périphériques et 15 245 sans cette correction ; zéro rejet. Les 17 820 dates de début sont harmonisées en date ; les fins nulles restent nulles.

Chaque ligne acceptée est conservée. Les rejets, s'il en existe sur un autre lot, sont écrits dans quality/j3 avec un motif. Aucun fichier de rejets vide artificiel n'est créé pour cette exécution.

## Jointure et calcul

Jointure gauche : store_sales.ss_item_sk = item.i_item_sk. Relation plusieurs-vers-un, attendue et vérifiée. Types long, dimension unique, aucune clé requise nulle. Avant : 667579 ; après : 667579 ; sans correspondance : 0. Le grain de vente est conservé avant agrégation. L'enrichissement est une étape intermédiaire, sans troisième Silver artificiel.

## Gold : ventes_par_produit

Grain final : une ligne par clé de substitution produit du lot initial, dans le canal magasin. La clé n'est pas assimilée à une gamme ni à un produit commercial durable à travers toutes ses versions. Dimensions : ss_item_sk, i_product_name, i_category, i_brand. Ces attributs sont fonctionnellement dépendants de la clé dans le référentiel vérifié.

| Mesure | Formule | Type observé |
|---|---|---|
| quantity_sold | SUM(ss_quantity) | bigint / long |
| net_paid | SUM(ss_net_paid) | decimal(17,2) |
| sales_line_count | COUNT(*) | bigint / long |

Trois colonnes de traçabilité : _run_id, _source_sales_sha256, _source_item_sha256. Aucun filtre de signe ni remplacement des nulls facultatifs. Les lignes rejetées selon R03 seraient exclues de Gold, mais leur nombre est zéro ici. Aucun calcul de prix unitaire moyen, taux de retour ou résultat net réel de l'entreprise n'est ajouté.

Sorties validées :

- hdfs://hdfs:9000/retail-lake/silver/j3/20261118T113628Z-243a5fb5-r3/store_sales
- hdfs://hdfs:9000/retail-lake/silver/j3/20261118T113628Z-243a5fb5-r3/item
- hdfs://hdfs:9000/retail-lake/gold/j3/20261118T113628Z-243a5fb5-r3/ventes_par_produit

Seul le lot 20261118T113628Z-243a5fb5-r3 est la publication complète validée. Les deux essais précédents ne contiennent que Silver ventes et ne doivent pas être lus avec un glob englobant tous les lots.

## Limites

Les montants sont exprimés en unités monétaires du kit, sans devise attestée. Le net payé est avant retours, sans déduire une seconde fois coupons ou remises déjà pris en compte. L'agrégat est descriptif sur le lot initial et ne constitue ni chiffre d'affaires réel d'une enseigne ni benchmark officiel. Aucun calendrier n'est joint ; aucune période civile nouvelle n'est déduite des clés numériques de vente. Les lots refresh ne sont pas fusionnés.
