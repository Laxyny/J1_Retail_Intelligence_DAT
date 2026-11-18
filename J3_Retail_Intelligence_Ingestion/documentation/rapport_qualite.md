# Rapport qualité

Périmètre exhaustif : deux fichiers initiaux, 667 579 lignes ventes et 17 820 lignes produit, puis trois sorties relues. Les affichages de cinq ou dix lignes sont uniquement des aperçus. Le registre détaillé est disponible dans preuves/controles/registre_qualite.csv et J3-P09-qualite.json : identifiant, règle, cible, résultat numérique, attendu, statut, méthode, justification et limites.

## Bilan des contrôles

73 contrôles enregistrés : 64 OK, 8 OBSERVE, 1 ANOMALIE_DOCUMENTEE. Zéro contrôle bloquant en échec ne signifie pas absence d'anomalies. Les valeurs nulles facultatives et la non-unicité du couple ticket-produit restent explicitement signalées.

| Dimension | Résultat exécuté | Décision |
|---|---|---|
| Complétude | Nulls par colonne contrôlés sur tout le fichier | Conservation des nulls facultatifs ; aucun zéro imputé |
| Types | 0 conversion impossible ; échelle décimale contrôlée | Schémas explicites ; arrêt en cas d’erreur |
| Unicité produit | 17 820 clés distinctes / 17 820 lignes | Dimension utilisable pour jointure |
| Doublons exacts | 0 ventes ; 0 produits | Aucune déduplication |
| Clé ticket-produit | 4 136 répétitions au-delà du premier couple | Clé candidate refusée ; lignes conservées |
| Référentiel | 0 vente non rapprochée ; même volume avant/après | Jointure plusieurs-vers-un vérifiée |
| Cohérence monétaire | 0 écart net + taxe ; 0 écart prix × quantité | Montants cohérents pour ces deux identités |
| Valeurs signées | 495 971 profits négatifs ; 0 quantité ou net payé négatif | Aucune exclusion au seul motif du signe |
| Parquet | 3 sorties lisibles ; schémas/types et volumes contrôlés | Empreintes égales ; réconciliation métier séparée |
| Réconciliation | 0 écart sur les 17 820 produits vs Python Decimal | Agrégats acceptés sur ce périmètre |

## Valeurs manquantes

| Source | Champ | Nulls | Part du fichier |
|---|---|---|---|
| store_sales | ss_cdemo_sk | 238 | 0.0357 % |
| store_sales | ss_hdemo_sk | 295 | 0.0442 % |
| store_sales | ss_addr_sk | 448 | 0.0671 % |
| store_sales | ss_promo_sk | 158 | 0.0237 % |
| item | i_rec_end_date | 17820 | 100.0000 % |
| item | i_item_desc | 4 | 0.0224 % |
| item | i_brand_id | 8 | 0.0449 % |
| item | i_brand | 6 | 0.0337 % |

Les 17 820 fins de validité produit vides sont maintenues comme valeurs ouvertes/inconnues, sans inventer une date de fin. Quatre descriptions, huit identifiants de marque et six libellés de marque manquent. Le groupement Gold garde le produit, même si sa marque manque. Un null de marque n'entraîne donc pas de perte de vente.

## Domaines et valeurs atypiques

Les quantités vont de 1 à 100, le net payé de 0,00 à 18 745,00 et le résultat de -9 866,60 à 9 134,00 UM. Ces bornes sont observées, pas imposées comme règle universelle à d'autres lots. Les clés produit vont de 0 à 17 819. Neuf catégories sont présentes ; les unités comprennent des libellés tels que Unknown et N/A et i_container vaut Unknown dans tout le référentiel. Aucune conversion d'unités n'est déduite de ces codes. Les dates ISO présentes passent le typage ; la fin étant toujours nulle, le contrôle fin >= début ne teste pas de paire fermée.

## Volumes et grain

| Passage | Volume | Explication |
|---|---|---|
| Raw ventes → Silver ventes | 667 579 → 667 579 | 0 rejet, aucune déduplication |
| Raw produits → Silver produits | 17 820 → 17 820 | 2 575 lignes avec trim ; 0 rejet |
| Ventes → jointure | 667 579 → 667 579 | 0 référence absente ; pas de multiplication |
| Jointure → Gold | 667 579 → 17 820 | Changement de grain : plusieurs ventes par produit |

Gold contient 17 820 produits, mais SUM(sales_line_count) reste 667 579. Les quantités et montants sont également conservés. Comparer directement le nombre de faits et le nombre de produits sans tenir compte du grain serait incorrect.

## Anomalies et rejets

Zéro ligne mise à l'écart dans les fichiers retenus. Les anomalies non bloquantes restent dans Silver et dans le registre. La règle d'isolement est codée pour une entrée ultérieure, sans fabriquer de faux rejets sur les données actuelles. Une erreur de type ou un conflit de clé produit arrête la publication et conserve les sources.

## Limites des contrôles

L'intégrité référentielle est vérifiée uniquement pour le lien produit utilisé. Les autres dimensions, la fraîcheur métier, les périodes civiles, les prix concurrents, les retours et la sémantique du refresh ne sont pas validés par ce pipeline. L'égalité de deux formules ne prouve pas toute la validité économique du kit. Les empreintes agrégées Parquet sont probabilistes. La relecture autonome J3-P10 s'ajoute aux 73 contrôles de transformation ; son nombre n'est pas artificiellement additionné au registre.
