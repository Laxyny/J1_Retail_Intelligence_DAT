# Analyses métier : produits, magasins et catégories

## Analyse 1 - Contribution des produits au net payé

Question : quels produits contribuent le plus au net payé magasin ? Le besoin précise Q03 (produits par canal)
et Q05 (net payé) du DAT J1. Source : Gold ventes_par_produit, un seul lot et une seule ligne par ss_item_sk.
Méthode : tri décroissant de net_paid, départage par clé produit, sélection explicite des dix premières lignes.
La contribution rapporte chaque montant au total global K01. Les libellés sont ceux du kit, sans correction inventée.

| Clé produit | Net payé (UM) | Contribution (%) |
| --- | --- | --- |
| 10000 | 15 408 393,55 | 1,3392 |
| 10003 | 14 933 870,10 | 1,2980 |
| 10001 | 14 572 124,66 | 1,2666 |
| 10002 | 12 817 437,86 | 1,1140 |
| 17502 | 3 336 529,83 | 0,2900 |
| 10579 | 3 250 367,57 | 0,2825 |
| 8601 | 3 238 749,92 | 0,2815 |
| 5618 | 3 212 955,42 | 0,2793 |
| 2651 | 3 172 287,79 | 0,2757 |
| 16513 | 3 162 636,37 | 0,2749 |


Résultat : le produit 10000 contribue 15 408 393,55 UM, soit 1,3392 %.
Les dix premiers représentent 6,7017 % ; les cent premiers 28,1203 %.
Dix références ne représentent que 0,0561 % des produits : leur poids dans les ventes est disproportionné,
mais elles ne représentent pas la majorité du net payé. Le reste des produits porte 93,2983 %.

Contrôle : le montant total Gold et les 17 820 lignes produit se réconcilient avec une nouvelle agrégation Silver,
sans différence sur montant, quantité et nombre de lignes. La somme des contributions arrondies atteint
100,000000000863 %, conforme à la tolérance numérique documentée.

Interprétation : certaines références concentrent beaucoup plus de montant que la référence médiane.
Recommandation pédagogique : examiner leur disponibilité et leur contexte avant une décision d'assortiment.
Limites : données synthétiques, agrégats de tout le lot, absence de coûts qualifiés et de période commerciale normalisée.
Une forte contribution n'est pas une forte rentabilité. Le premier graphique utilise des barres horizontales et un axe à zéro.

## Analyse 2 - Répartition des montants et quantités par magasin

Question : comment les montants et quantités se répartissent-ils entre magasins ? Cette déclinaison précise Q05
et le besoin du responsable magasin Q07, sans prétendre répondre à toute l'analyse des familles de produits.
Source : Silver store_sales ; regroupement Spark par ss_store_sk. Aucune dimension store non qualifiée n'est jointe.

| Magasin | Net payé (UM) | Unités | Lignes | Part (%) |
| --- | --- | --- | --- | --- |
| 7 | 98 950 137,76 | 2 915 053 | 57 589 | 8,60 |
| 4 | 96 770 105,59 | 2 832 572 | 56 211 | 8,41 |
| 9 | 96 748 356,68 | 2 830 684 | 56 040 | 8,41 |
| 0 | 96 727 851,94 | 2 830 581 | 56 018 | 8,41 |
| 8 | 96 578 622,89 | 2 821 869 | 55 737 | 8,39 |
| 3 | 96 063 990,59 | 2 800 824 | 55 397 | 8,35 |
| 1 | 95 929 844,66 | 2 817 524 | 55 676 | 8,34 |
| 11 | 95 607 843,48 | 2 790 631 | 55 473 | 8,31 |
| 6 | 94 751 173,08 | 2 780 253 | 54 574 | 8,24 |
| 10 | 94 263 977,55 | 2 785 773 | 55 109 | 8,19 |
| 5 | 94 097 279,37 | 2 789 703 | 55 122 | 8,18 |
| 2 | 94 040 402,78 | 2 760 007 | 54 633 | 8,17 |


Résultat : le magasin 7 atteint 98 950 137,76 UM et 2 915 053 unités ; le magasin 2 atteint 94 040 402,78 UM
et 2 760 007 unités. L'écart est de 4 909 734,98 UM, soit 5,22 % du minimum.
Les parts monétaires restent proches, entre 8,17 % et 8,60 %, autour de 8,33 % pour une répartition uniforme.

Contrôle : sommes des douze magasins strictement égales aux trois totaux Silver, y compris au centime pour K01.
Le graphique à deux panneaux compare montant et quantité dans des unités séparées ; il couvre tous les magasins.
Les écarts de volume suivent globalement ceux des montants, sans démontrer une relation causale.
Recommandation : obtenir surface, fréquentation, durée d'ouverture et période fiable avant un jugement de performance.
Les noms commerciaux sont absents du périmètre qualifié ; seuls les identifiants sont affichés.

## Analyse 3 - Contribution des catégories au montant des ventes

Question : quelles catégories contribuent le plus au montant et au volume des ventes magasin ? Cette lecture
précise le besoin Q03 sur l'assortiment et Q07 sur les familles, sur le périmètre global magasin.
Source : Gold ventes_par_produit validé J3, regroupé directement par i_category, sans nouvelle jointure ni réécriture du Gold.
Méthode : sommes de net_paid, quantity_sold et sales_line_count, compte des produits et part du net payé global.

| Catégorie | Net payé (UM) | Unités | Lignes | Part (%) |
| --- | --- | --- | --- | --- |
| Music | 519 666 693,84 | 15 238 374 | 301 236 | 45,1676 |
| Books | 307 151 503,25 | 9 007 511 | 177 671 | 26,6965 |
| Movies & TV | 74 735 891,89 | 2 189 279 | 43 376 | 6,4958 |
| Clothing & Accessories | 56 754 855,82 | 1 640 550 | 32 372 | 4,9329 |
| Electronics | 55 715 087,49 | 1 632 098 | 32 619 | 4,8426 |
| Home & Kitchen | 41 260 511,11 | 1 226 839 | 24 380 | 3,5862 |
| Sports & Outdoors | 40 926 938,33 | 1 209 305 | 23 911 | 3,5572 |
| Toys & Games | 27 437 825,33 | 809 999 | 16 121 | 2,3848 |
| Tools & Home Improvement | 26 880 279,31 | 801 519 | 15 893 | 2,3363 |


Les 9 catégories couvrent tous les 17 820 produits et aucune catégorie n'est nulle ou vide.
Music apporte 45,1676 % du net payé ; Books 26,6965 %.
Ensemble, elles totalisent 826 818 197,09 UM, soit 71,8641 %.
Cette concentration décrit la contribution monétaire ; les quantités constituent une autre mesure, publiée dans le tableau.
Les libellés réels restent inchangés. Toute catégorie manquante aurait été conservée comme groupe explicite et signalée.

Contrôles : montants, quantités et lignes par catégorie sont strictement égaux à K01, K02 et J4-L01 ;
les parts se réconcilient avec 100 % à la tolérance documentée. Le tableau complet sert au troisième graphique.
La précision des divisions Decimal est préservée avant affichage ; le tracé utilise seulement neuf agrégats Pandas.

Interprétation : Music et Books concentrent une grande part du montant de ce jeu synthétique. Cela ne démontre ni
rentabilité supérieure ni demande future. Recommandation pédagogique conditionnelle : examiner demande, marges,
disponibilité et période comparable avant toute décision sur l'assortiment ou les stocks ; aucun ajustement direct n'est proposé.
