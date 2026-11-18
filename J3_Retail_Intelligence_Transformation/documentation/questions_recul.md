# Dix questions de recul - TP3 section 11

## 1. Pourquoi est-il nécessaire de vérifier les schémas avant de commencer les transformations ?

Sans en-tête, une position mal affectée pourrait transformer le prix en quantité. Nous avons vérifié 23 et 22 champs, l'ordre de l'Annexe G, les types et les identités monétaires sur tout le fichier.

## 2. Quelle différence existe entre une donnée brute, une donnée Silver et une donnée Gold ?

Raw conserve les deux DAT et leurs empreintes. Silver garde les lignes typées, les dates et textes harmonisés, avec provenance. Gold résume les ventes au grain produit et expose quantité, net payé et nombre de lignes.

## 3. Pourquoi faut-il connaître la granularité d'une table avant de réaliser une agrégation ?

Une ligne de vente n'est pas un ticket complet. Nous additionnons les quantités de chaque ligne, puis Gold contient une ligne par clé produit. COUNT(*) mesure ici les lignes de vente et non les transactions.

## 4. Quels risques présente une jointure réalisée sur une clé supposée ?

Une dimension ayant deux lignes pour la même clé multiplierait les ventes et les montants. Nous avons vérifié l'unicité de i_item_sk, la compatibilité long, les références et 667 579 lignes avant comme après jointure.

## 5. Pourquoi ne faut-il pas supprimer automatiquement les valeurs atypiques ?

Les 495 971 profits négatifs sont des valeurs du kit dont la négativité ne démontre pas une erreur. Les supprimer changerait le périmètre. Les 4 136 répétitions ticket-produit ne sont pas non plus des doublons exacts.

## 6. Quels contrôles permettent de vérifier la cohérence d'un jeu de données transformé ?

Comparer les volumes, les types, les nulls, les clés et les références ; réconcilier les sommes avant/après jointure et agrégation ; relire les fichiers. Ici chaque produit Gold a aussi été comparé à un calcul indépendant en Decimal.

## 7. Pourquoi Parquet est-il adapté aux usages analytiques ?

Son organisation en colonnes permet de lire les champs utiles, de conserver les types et de compresser les valeurs. Nos trois sorties Snappy se relisent dans Spark ; Silver ventes occupe 34 766 704 octets pour 92 764 700 octets de DAT source, à schéma enrichi.

## 8. Pourquoi Parquet seul ne fournit-il pas les garanties d'une table transactionnelle Lakehouse ?

Un format de fichier ne coordonne pas les transactions sur plusieurs fichiers, les versions et les écritures concurrentes. Nos lots uniques et errorifexists préviennent les écrasements accidentels, sans offrir d'upsert ni de transaction de table.

## 9. Dans quels cas une base NoSQL pourrait-elle compléter une architecture Data Lake ?

Pour une lecture rapide par identifiant produit, un cache de session ou des événements consultés par clé. Une base de documents ou wide-column peut servir ces accès applicatifs. Cela ne remplace pas les scans et agrégations Spark/Parquet. Aucune base NoSQL n'a été installée ici.

## 10. Quelles limites des données TPCx-BB doivent être prises en compte lors de l'interprétation des résultats ?

Le kit est synthétique, la devise et la version locale du générateur ne sont pas attestées, certains champs manquent et la fusion refresh n'est pas spécifiée. Les libellés ne décrivent pas un catalogue réel. Les conclusions portent sur les fichiers initiaux étudiés, sans causalité ni score officiel de benchmark.
