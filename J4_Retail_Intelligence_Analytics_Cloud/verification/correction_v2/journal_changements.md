# Journal des corrections - J4 initial vers J4 V2

Correction réalisée le 19 novembre 2026, sans relancer le pipeline du Jour 3.

## Sauvegarde et périmètre

Les 186 fichiers du dossier J4 initial ont été copiés et comparés par SHA-256 avant toute modification,
dans Projet/Sauvegardes_J4/J4_initial_20261119T104631. La sauvegarde comprend le PDF de 22 pages,
l'ancien dossier A_REMETTRE_J4 et son ZIP. Elle est exclue de la remise V2.
Les travaux J1, J2, J3, les sources et le lac sont protégés par les preuves avant/après et le contrôle preservation.json.

## Changements fonctionnels

- K01 et K02 conservent leurs définitions et leurs totaux. J4-L01 conserve 667 579 lignes et devient secondaire.
- K03 est réintégré : 89 100 tickets magasin, sans valeur nulle ni association multiple à un magasin, une date ou un client.
- K04 est calculé après somme des lignes de chaque ticket : moyenne Spark Decimal 12 912,7899704826038159 UM,
  soit 12 912,79 UM au centime. Les paniers réconcilient K01, les quantités et toutes les lignes.
- Les 82 713 tickets multilignes et 4 136 répétitions ticket-produit sont conservés. Aucune déduplication.
- Le Gold est regroupé directement en neuf catégories, sans jointure. Music et Books représentent ensemble
  826 818 197,09 UM, soit 71,8641403824 % du montant.
- Un troisième graphique présente les catégories ; les deux PNG initiaux sont strictement identiques à la sauvegarde.

## Précision et contrôles

Le calcul des parts de catégories borne le numérateur en Decimal(17,2) avant division. Cette capacité couvre les montants
observés et évite la réduction de l'échelle décimale après SUM par Spark ; les valeurs en CSV sont contrôlées indépendamment
avec Decimal à partir des agrégats produit. Aucun montant source n'a été arrondi pour produire les résultats.
Les 26 contrôles initiaux ont été réexécutés et complétés, pour 45 contrôles Spark réussis.
La validation indépendante compare les KPI aux preuves J1, recalcule les catégories depuis les produits,
contrôle le notebook exécuté et ses trois images, puis la concordance avec le PDF et les onze livrables.
Les résultats exacts et le nombre final de vérifications figurent dans controle_final.json.

## Documents et présentation

Le dictionnaire présente K01 à K04 en priorité et explique la clé de transaction, HT, le périmètre et l'arrondi.
La synthèse commence par le montant, les unités, les transactions, le panier et les catégories, sans chemins ni identifiant de lot.
UM est défini dès sa première apparition. Les analyses, statistiques, réponses affectées, README et preuves sont actualisés.
Le rapport passe de 22 à 25 pages : tableaux K03/K04, qualification, analyse des catégories et troisième graphique.
Le fond blanc, les titres noirs, les tableaux simples et les architectures sont conservés.

UC-07 reste identique, sauf une phrase nécessaire dans le scénario : « trois agrégats » devient « des agrégats »
puisque kpi.csv contient désormais cinq indicateurs. Aucun service ajouté, aucun droit HDFS modifié, aucun appel Azure.

## Publication

La nouvelle remise est préparée dans un dossier candidat, puis vérifiée avant de remplacer les noms publics
A_REMETTRE_J4 et A_REMETTRE_J4.zip. L'ancienne publication est déplacée dans la sauvegarde, sans suppression.
La nouvelle archive contient uniquement la version V2, ses sources historiques identifiées et ses preuves.
