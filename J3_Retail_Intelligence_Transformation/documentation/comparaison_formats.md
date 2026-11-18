# Comparaison des formats et contrôle Parquet

DAT est ici du texte délimité, comparable à un CSV sans en-tête. JSON est étudié et utilisé pour paramètres, contrôles et traces ; il n'est pas présenté comme une source native des ventes.

| Critère | DAT / CSV | JSON | Parquet |
|---|---|---|---|
| Organisation | Enregistrements en lignes, séparateur  /  | Objets et tableaux | Colonnes binaires |
| Types | Schéma externe à appliquer | Types primitifs, date et Decimal à encadrer | Types persistés dans le fichier |
| Compression | Sources non comprimées | Traces lisibles non comprimées | Snappy effectivement utilisé |
| Lisibilité | Lecture humaine possible | Lecture humaine possible | Lecture via Spark ou outil Parquet |
| Analyse | Parsing et scans texte | Adapté aux structures imbriquées | Projection de colonnes et agrégations |
| Limite | En-tête absent ; ordre à prouver | Plus verbeux ; pas de Decimal natif universel | Binaire ; gestion de table à organiser |

## Volumes réellement mesurés

| Jeu | Texte source (octets) | Parquet (octets) | Lignes relues |
|---|---|---|---|
| Silver ventes | 92764700 | 34766704 | 667579 |
| Silver produits | 6799286 | 3571219 | 17820 |
| Gold par produit | Pas de texte équivalent exporté | 1307151 | 17820 |

Pour Silver ventes, Parquet représente 37,48 % du volume DAT ; pour Silver produits, 52,52 %. Ces rapports comparent les sources aux sorties typées, avec provenance et normalisation ajoutées : ce n'est pas une expérience de compression à schéma strictement identique, ni un test de vitesse. La réduction Gold reflète surtout l'agrégation ; on ne l'attribue pas à la compression seule. Les volumes HDFS sont logiques, hors métadonnées du système de fichiers ; réplication 1.

## Vérifications exécutées

Pour chacune des trois sorties : écriture errorifexists, fichiers part-*.snappy.parquet et marqueur _SUCCESS présents, relecture Spark, égalité des noms et types, nombre de lignes avant/après identique. Les schémas complets avant et après sont dans J3-P08-parquet.json. Les champs de provenance déclarés non nullables par les expressions peuvent devenir nullables après lecture Parquet ; cette différence de métadonnée est documentée, pas masquée.

Deux sommes de fragments d'empreinte SHA-256 de chaque ligne sérialisée, incluant les nulls, sont calculées avant et après relecture. Elles sont égales pour les trois sorties et tiennent compte des multiplicités de lignes. Ce contrôle probabiliste n'est pas une preuve mathématique d'identité de tous les enregistrements ; il comporte un risque théorique de collision. Les sommes métier sont contrôlées séparément, dont une réconciliation indépendante pour chaque produit.

## Incident et correction

Les deux premières tentatives de contrôle par exceptAll restent en attente avec des tâches non terminées ; les lectures simples fonctionnent. Les journaux et états de threads sont conservés. Désactiver l'optimisation adaptative n'a pas résolu le problème et n'a pas été retenu. Le contrôle a été remplacé par schémas, volumes, empreintes agrégées et réconciliations métier, puis exécuté avec succès. La cause interne exacte du blocage n'est pas déterminée. Les sorties d'essai sont conservées et identifiées comme non validées ; aucune n'est écrasée.

## Garanties

Parquet stocke des fichiers typés en colonnes. Il ne fournit pas, à lui seul, de transactions multi-fichiers ACID, d'upsert métier, de contrôle de concurrence ni d'historique de table. Les lots uniques et errorifexists évitent nos écrasements, mais ne constituent pas une couche transactionnelle. Aucune installation Delta, Iceberg ou Hudi n'a été réalisée.
