# Les quatorze questions de recul du TP4, section 15

Formulations du document pédagogique, avec typographie normalisée.

## 1. Pourquoi faut-il vérifier la granularité avant de calculer un KPI ?

Une ligne Silver représente une vente détaillée ; une ligne Gold représente un produit. COUNT(*) donne donc 667 579 faits ou 17 820 produits. La bonne somme dépend de ce grain ; Gold doit sommer sales_line_count pour retrouver les faits.

## 2. Quelle différence existe entre un nombre de lignes et un nombre de transactions ?

Un ticket peut regrouper plusieurs lignes. Les 667 579 lignes ne sont pas 667 579 transactions. Le canal et les dimensions identifiant un en-tête doivent être vérifiés avant un compte distinct ou un panier moyen ; le couple ticket-produit se répète 4 136 fois.

## 3. Quelles limites avez-vous rencontrées dans les données utilisées pour vos analyses ?

Le lot est synthétique, la devise n’est pas établie et le périmètre ne contient que les ventes magasin. Des attributs facultatifs sont nuls, les noms magasins et un calendrier qualifié ne sont pas utilisés. Les différences ne sont pas normalisées par taille ou fréquentation.

## 4. Quels indicateurs n’avez-vous pas pu calculer, et pour quelles raisons ?

K12 reste suspendu : les retours ne sont pas dans ces Parquet et leur rattachement n’est pas validé. La variation mensuelle nécessite un calendrier qualifié et la comparaison par canal le web. K03 et K04 sont désormais validés en V2 après qualification des tickets ; la marge n’est pas défendue sans coûts qualifiés.

## 5. Comment avez-vous vérifié la cohérence des résultats ?

Les trois totaux Silver correspondent aux références J3, aux sommes Gold, aux douze magasins et aux neuf catégories. Une nouvelle agrégation Silver rapproche les 17 820 produits sans écart. Les 45 contrôles incluent la qualification des tickets, les paniers, références, lot, nulls et parts. Les PNG sont reliés aux tableaux numériques puis inspectés visuellement.

## 6. Quelle différence existe entre un constat statistique et une conclusion causale ?

Le magasin 7 présente plus de net payé que le 2 : c’est un constat. L’attribuer à une meilleure équipe serait causal et non démontré. Il faudrait contrôler période, clientèle, taille, assortiment et autres facteurs, puis une méthode capable de distinguer ces explications.

## 7. Pourquoi les données synthétiques doivent-elles être identifiées dans la restitution ?

Elles servent à apprendre à traiter et vérifier les données. La concentration des produits du générateur ne décrit pas nécessairement une enseigne réelle. Le signaler empêche d’utiliser ces montants comme une observation commerciale ou une prévision.

## 8. Quel est le rôle d’ADLS Gen2 dans votre architecture ?

Il serait le stockage durable des zones et des fichiers, avec les capacités Data Lake de Blob Storage. Il remplacerait fonctionnellement le stockage HDFS pour les moteurs autorisés, sans faire lui-même les calculs Spark [A1].

## 9. Quel intérêt apporte le Hierarchical Namespace ?

Il fournit des répertoires réels et des opérations de métadonnées adaptées aux traitements. Le renommage de répertoires facilite la publication d’une sortie. Son activation est irréversible et demande une vérification des fonctionnalités compatibles [A2].

## 10. Quelle différence existe entre RBAC et ACL ?

RBAC attribue des rôles sur une portée de ressources ; les ACL portent sur les chemins et utilisent r/w/x. Une ACL ne peut pas retirer l’accès accordé par un rôle de données trop large. Les groupes et les ancêtres doivent être correctement configurés [A3, A4].

## 11. Dans quels cas Azure Data Factory serait-il utile ?

Pour planifier les dépôts, copier plusieurs sources, enchaîner le contrôle puis le calcul et suivre les erreurs. Les scripts suffisent au lot pédagogique actuel ; ADF resterait à envisager pour des arrivées récurrentes avec connectivité et droits maîtrisés [A5].

## 12. Quel rôle pourrait jouer Synapse Analytics ?

Un workspace et Synapse Studio centraliseraient l’analyse ; Spark traiterait les fichiers ADLS et SQL offrirait des interrogations adaptées. Ce service intégré ne se réduit ni à Iceberg, ni à un répertoire Parquet. Son runtime et ses coûts devraient être qualifiés [A6, A7].

## 13. Quels éléments de votre architecture sont réellement déployés et lesquels restent théoriques ?

HDFS, Docker/WSL2, PySpark et Parquet J3 sont réutilisés ; J4 exécute notebook, Pandas et Matplotlib. NiFi appartient au test J2 et reste arrêté. Azure, les ACL cibles, ADF, Synapse et les composants Lakehouse facultatifs restent proposés ou étudiés.

## 14. Quels seraient les principaux risques de coût ou de sécurité dans une mise en production ?

Calcul laissé actif, scans et transferts répétés, rétention de copies et journaux peuvent générer des dépenses. Les droits excessifs, clés exposées, endpoints publics et données personnelles exportées élargiraient l’exposition. Il faudrait chiffrer les hypothèses, tester les refus et contrôler l’exploitation [A3, A8, A9].
