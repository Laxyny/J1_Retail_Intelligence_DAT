# Inventaire technique des sources

Les deux sources de traitement sont des données structurées : store_sales et item, lot initial complet. Aucun échantillonnage du traitement. Le refresh item a été examiné séparément pour lever l'incertitude sur la couverture, puis exclu du pipeline. Il contient 180 lignes, clés 17 820 à 17 999 ; toutes les ventes initiales utilisent 0 à 17 819, déjà présents dans item initial.

## Localisation vérifiée

Racine du kit sur Windows :

C:\Users\Kevin GREGOIRE\Desktop\Projet\01. Architecture DataLake, DataWarehouse, Lakehous\retail_project\retail_project

Montage en lecture seule dans Spark : /sources. Racine des nouveaux dépôts HDFS :

hdfs://hdfs:9000/retail-lake/raw/j3/20261118T113628Z-243a5fb5

| Source / lot | Lignes et champs | Octets | Granularité |
|---|---|---|---|
| data/store_sales | 667 579 / 23 | 92 764 700 | Ligne de vente magasin |
| data/item | 17 820 / 22 | 6 799 286 | Enregistrement produit par clé de substitution |
| data_refresh/item | 180 / 22 | 69 173 | Enregistrement produit par clé de substitution |

Format vérifié sur toutes les lignes : DAT texte délimité par |, sans en-tête, fins CRLF. Le décodage UTF-8 strict réussit et aucun octet non ASCII n'est rencontré : ASCII est compatible UTF-8 ; on ne peut pas distinguer davantage les encodages compatibles sur ce contenu. Le split conserve les derniers champs vides. Chaque ligne retenue a exactement 23 ou 22 champs ; aucun séparateur terminal surnuméraire n'est retiré arbitrairement.

## Schéma ordinal fiable

Les positions ci-dessous proviennent du DDL des tables temporaires Hive de l'Annexe G de TPCx-BB 1.7.0, pages 125 et 131-132. Le dictionnaire de J1 a été recopié puis revalidé contre une nouvelle copie du PDF officiel dans preuves/consignes. La section B.1 n'a pas servi à supposer l'ordre physique. La version exacte du générateur du kit local reste inconnue ; la largeur, le typage, les relations et les égalités de montants corroborent la correspondance.

Référence : [TPCx-BB 1.7.0, juin 2025](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPCX-BB_v1.7.0.pdf). Le script verification/verifier_reference.py conserve l'empreinte du PDF et vérifie les deux listes ordinales.

## Dictionnaire store_sales

| Position physique | Colonne | Type Raw interprété / Silver |
|---|---|---|
| 1 | ss_sold_date_sk | bigint |
| 2 | ss_sold_time_sk | bigint |
| 3 | ss_item_sk | bigint |
| 4 | ss_customer_sk | bigint |
| 5 | ss_cdemo_sk | bigint |
| 6 | ss_hdemo_sk | bigint |
| 7 | ss_addr_sk | bigint |
| 8 | ss_store_sk | bigint |
| 9 | ss_promo_sk | bigint |
| 10 | ss_ticket_number | bigint |
| 11 | ss_quantity | int |
| 12 | ss_wholesale_cost | decimal(7,2) |
| 13 | ss_list_price | decimal(7,2) |
| 14 | ss_sales_price | decimal(7,2) |
| 15 | ss_ext_discount_amt | decimal(7,2) |
| 16 | ss_ext_sales_price | decimal(7,2) |
| 17 | ss_ext_wholesale_cost | decimal(7,2) |
| 18 | ss_ext_list_price | decimal(7,2) |
| 19 | ss_ext_tax | decimal(7,2) |
| 20 | ss_coupon_amt | decimal(7,2) |
| 21 | ss_net_paid | decimal(7,2) |
| 22 | ss_net_paid_inc_tax | decimal(7,2) |
| 23 | ss_net_profit | decimal(7,2) |

## Dictionnaire item

| Position physique | Colonne | Type Raw interprété / Silver |
|---|---|---|
| 1 | i_item_sk | bigint |
| 2 | i_item_id | string |
| 3 | i_rec_start_date | string ISO / date |
| 4 | i_rec_end_date | string ISO / date |
| 5 | i_item_desc | string |
| 6 | i_current_price | decimal(7,2) |
| 7 | i_wholesale_cost | decimal(7,2) |
| 8 | i_brand_id | int |
| 9 | i_brand | string |
| 10 | i_class_id | int |
| 11 | i_class | string |
| 12 | i_category_id | int |
| 13 | i_category | string |
| 14 | i_manufact_id | int |
| 15 | i_manufact | string |
| 16 | i_size | string |
| 17 | i_formulation | string |
| 18 | i_color | string |
| 19 | i_units | string |
| 20 | i_container | string |
| 21 | i_manager_id | int |
| 22 | i_product_name | string |

## Clés et anomalies

ss_item_sk et i_item_sk sont des bigint / long et représentent la clé de substitution produit. i_item_sk est unique et non nul : 17 820 clés pour 17 820 lignes ; le minimum est zéro. Les 667 579 références de vente sont rapprochées sans ambiguïté. ss_ticket_number × ss_item_sk présente 4 136 répétitions au-delà de la première occurrence ; il ne constitue pas une clé unique de ligne. Aucun doublon exact n'a été constaté, avec deux méthodes exhaustives (empreintes de lignes Python et distinct Spark). La clé i_item_id est conservée mais n'est pas utilisée pour la jointure.

Les colonnes ventes sont numériques : identifiants, quantité entière, 12 montants decimal(7,2). Aucun champ temporel calendaire n'est directement présent dans store_sales ; les clés de date et d'heure restent des références. item contient 8 colonnes numériques et 14 chaînes à la lecture, dont deux dates ISO converties en Silver.

Les listes de nulls, extrema, domaines et empreintes sont conservées dans inventaire_python.json et J3-P04-*.json. Les valeurs atypiques et champs manquants sont détaillés dans le rapport qualité. Les valeurs Unknown et N/A du référentiel restent des libellés sources, pas des nulls inventés.
