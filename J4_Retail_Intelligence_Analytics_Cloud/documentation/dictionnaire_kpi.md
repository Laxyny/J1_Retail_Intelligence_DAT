# Dictionnaire des KPI

Les quatre KPI métier K01 à K04 sont prioritaires ; J4-L01 reste un indicateur technique secondaire.
Leur périmètre commun couvre toutes les lignes Silver store_sales du lot initial J3 final.
Aucun filtre, aucune déduplication, aucune imputation. Les quantités et les lignes sont des entiers ; les montants sont en Decimal.
Les résultats numériques sont générés dans analytics/outputs/kpi.csv. Les clés des contrôles sont dans controles.csv.

## K01 - Net payé HT avant retours

| Attribut | Définition |
| --- | --- |
| Objectif | Mesurer la valeur des ventes magasin selon UC-01 |
| Définition exacte | Somme des nets payés, hors taxe, avant imputation de retours |
| Formule | SUM(ss_net_paid) |
| Source | Silver store_sales ; contre-vérification Gold ventes_par_produit |
| Colonnes / types | ss_net_paid decimal(7,2) ; Gold net_paid decimal(17,2) |
| Filtres | Aucun ; lot final uniquement |
| Granularité | Ligne de vente en entrée ; total du canal magasin en sortie |
| Unité | unités monétaires |
| Résultat calculé | 1 150 529 586,37 |
| Contrôles | Référence J3, Gold, sommes magasin et catégories ; rapprochement exhaustif par produit |
| Limites | Ni devise confirmée, ni chiffre d’affaires comptable, ni rentabilité. |

## K02 - Unités vendues

| Attribut | Définition |
| --- | --- |
| Objectif | Mesurer le volume vendu selon UC-01 |
| Définition exacte | Somme des quantités portées par les lignes de vente |
| Formule | SUM(ss_quantity) |
| Source | Silver store_sales ; contre-vérification Gold ventes_par_produit |
| Colonnes / types | ss_quantity integer ; Gold quantity_sold bigint |
| Filtres | Aucun ; lot final uniquement |
| Granularité | Ligne de vente en entrée ; total du canal magasin en sortie |
| Unité | unités |
| Résultat calculé | 33 755 474 |
| Contrôles | Référence J3, Gold, sommes magasin et catégories ; rapprochement exhaustif par produit |
| Limites | Unités du kit ; pas de conversion entre conditionnements ni nombre de références. |

## K03 - Transactions magasin distinctes

| Attribut | Définition |
| --- | --- |
| Objectif | Mesurer le nombre de paniers enregistrés selon UC-01 |
| Définition exacte | En-têtes distincts magasin, après qualification des associations ticket/magasin/date/client |
| Formule | COUNT(*) après GROUP BY ss_ticket_number qualifié |
| Source | Silver store_sales ; agrégation de toutes les lignes par ticket qualifié |
| Colonnes / types | ss_ticket_number bigint ; ss_store_sk, ss_sold_date_sk et ss_customer_sk pour qualifier la clé |
| Filtres | Aucun ; lot final uniquement |
| Granularité | Transaction magasin en sortie ; lignes conservées en entrée |
| Unité | transactions |
| Résultat calculé | 89 100 |
| Contrôles | Complétude, dépendances ticket vers magasin/date/client, références UC-01 et conservation des totaux des paniers |
| Limites | Valable pour le canal magasin initial fourni ; inclure canal et périmètre de lot avant toute réutilisation. |

## K04 - Panier moyen HT par transaction

| Attribut | Définition |
| --- | --- |
| Objectif | Mesurer la valeur moyenne du panier selon UC-01 |
| Définition exacte | Moyenne des sommes de net payé des transactions complètes du fichier fourni |
| Formule | AVG(transaction_net_paid), avec transaction_net_paid = SUM(ss_net_paid) par ticket qualifié |
| Source | Silver store_sales ; agrégation de toutes les lignes par ticket qualifié |
| Colonnes / types | ss_ticket_number bigint ; ss_net_paid decimal(7,2) ; moyenne Spark Decimal à 16 décimales |
| Filtres | Aucun ; lot final uniquement |
| Granularité | Transaction magasin en sortie ; lignes conservées en entrée |
| Unité | UM par transaction |
| Résultat calculé | 12 912,79 |
| Contrôles | Complétude, dépendances ticket vers magasin/date/client, références UC-01 et conservation des totaux des paniers |
| Limites | Avant retours et hors taxe selon UC-01 ; ne mesure pas la moyenne par ligne ni la rentabilité. |

## J4-L01 - Nombre de lignes de vente

| Attribut | Définition |
| --- | --- |
| Objectif | Qualifier le volume de faits analysé |
| Définition exacte | Comptage de toutes les lignes physiques conservées en Silver |
| Formule | COUNT(*) |
| Source | Silver store_sales ; contre-vérification Gold ventes_par_produit |
| Colonnes / types | Toutes les lignes ; Gold sales_line_count bigint |
| Filtres | Aucun ; lot final uniquement |
| Granularité | Ligne de vente en entrée ; total du canal magasin en sortie |
| Unité | lignes |
| Résultat calculé | 667 579 |
| Contrôles | Référence J3, Gold, sommes magasin et catégories ; rapprochement exhaustif par produit |
| Limites | Indicateur ajouté en J4 ; ne mesure ni ticket, ni commande, ni client. |

## Qualification de K03 et K04

La clé retenue est ss_ticket_number dans le canal magasin et le lot initial étudié. Elle détermine un seul magasin,
une seule date et un seul client renseigné. Les cinq colonnes d'en-tête et de montant n'ont aucune valeur nulle.
Les 89 100 tickets correspondent exactement aux 89 100
en-têtes composites ticket/magasin/date/client : ajouter ces dimensions ne scinde aucun panier.
Aucun ticket négatif, aucune clé date non positive, aucune quantité nulle ou non positive.

82 713 tickets ont plusieurs lignes, avec 1 à 14 lignes par ticket.
Les 4 136 répétitions du couple ticket-produit sont conservées, comme au Jour 3. Aucun dédoublonnage.
La somme des paniers est 1 150 529 586,37 UM, strictement égale à K01 ; les effectifs et quantités se réconcilient aussi.

K04 = 1 150 529 586,37 / 89 100 = 12 912,7899704826038159 UM.
La moyenne est calculée avec Spark sur les paniers agrégés ; le quotient indépendant Decimal la confirme à moins de 0,000000000001 UM.
L'arrondi décimal au centime donne 12 912,79 UM, égal au résultat J1. Le montant moyen par ligne,
1 723,44 UM, est une autre mesure. HT reprend le DAT initial : net hors taxe et après coupons ; les deux identités
net + taxe = TTC et vente - coupon = net présentent zéro écart sur toutes les lignes.

Le SHA-256 source Silver correspond à l'inventaire initial J1 : 7e0a7f16b47483741754bb641c92601dd7384dacc8331d0bcfb8abac82ed3d2e.
Les contrôles J1 de résolution des dates et de complétude des transactions sont conservés en provenance ; leurs associations sont
revérifiées en J4 V2. La complétude porte sur le fichier livré, sans preuve externe d'exhaustivité de caisse ni d'annulations absentes.
Les 89 100 identifiants partagés historiquement entre web et magasin interdisent d'étendre la clé à plusieurs canaux sans le canal.

## Indicateurs non retenus et indicateurs indisponibles

K03 et K04, non retenus dans la version initiale J4, sont désormais qualifiés et calculés en V2.
K12 (taux de retour) reste suspendu : retours non présents dans les Parquet choisis, lien vente-retour et maturité non validés.
K05 (variation mensuelle) exige le calendrier et des mois comparables : une clé date numérique ne suffit pas ici.
K01 par canal comparé au web ne peut pas être produit avec les seules ventes magasin retenues. Une marge commerciale fiable
exigerait une qualification des coûts et du périmètre ; la présence de ss_net_profit ne démontre pas cette qualification.

Les parts produit, magasin et catégorie sont des décompositions de K01 : 100 × montant du groupe / montant global.
Le dénominateur est strictement positif ; les parts sont publiées à 12 décimales et contrôlées avec une tolérance de 0,0000001 point.
