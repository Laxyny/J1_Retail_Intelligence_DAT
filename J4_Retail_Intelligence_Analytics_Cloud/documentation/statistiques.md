# Analyses statistiques

Périmètre exhaustif du même lot, sans échantillonnage. Les statistiques Silver décrivent les lignes, celles de Gold les produits.
Les médianes sont exactes : moyenne Decimal des une/deux valeurs centrales triées avec Spark.
Les sommes et moyennes monétaires restent décimales ; les écarts-types de population sont des flottants, arrondis ici.
Les cellules nulles seraient exclues des statistiques de mesure et leur couverture resterait publiée, sans remplacement par zéro.

| Jeu / mesure | Minimum | Médiane | Moyenne | Maximum | Écart-type |
| --- | --- | --- | --- | --- | --- |
| store_sales / ss_quantity | 1,00 | 51,00 | 50,56 | 100,00 | 28,88 |
| store_sales / ss_net_paid | 0,00 | 878,54 | 1 723,44 | 18 745,00 | 2 167,90 |
| ventes_par_produit / quantity_sold | 230,00 | 1 044,00 | 1 894,25 | 454 954,00 | 9 315,96 |
| ventes_par_produit / net_paid | 2 786,76 | 34 949,04 | 64 563,95 | 15 408 393,55 | 317 929,78 |
| ventes_par_produit / sales_line_count | 6,00 | 21,00 | 37,46 | 9 029,00 | 184,43 |

Les cinq mesures ont une couverture de 100 %. Les sommes sont exportées avec les effectifs dans statistiques.csv.
Le référentiel et Gold ont chacun 17 820 clés distinctes ; 12 identifiants magasin sont observés.
Le net payé par ligne a une moyenne de 1 723,44 UM, près du double de la médiane 878,54 UM : les montants sont dispersés.
La médiane Gold de 34 949,04 UM et son maximum de 15 408 393,55 UM montrent une forte hétérogénéité entre produits.
Ces constats ne suffisent pas à qualifier des anomalies de saisie dans un jeu synthétique.
3 954 lignes ont un net payé nul ; aucune n'est exclue. Les valeurs net payé et quantité ne sont pas négatives ; les profits négatifs restent conservés.
La répartition complète par magasin est publiée dans ventes_par_magasin.csv ; celle par produit dans contributions_produits.csv.

La V2 ajoute la distribution du nombre de lignes par ticket dans repartition_lignes_par_ticket.csv : 89 100 tickets, dont 82 713 multilignes, de 1 à 14 lignes. Le panier moyen est 12 912,79 UM ; il ne remplace pas la moyenne par ligne. La répartition des neuf catégories est dans ventes_par_categorie.csv.
