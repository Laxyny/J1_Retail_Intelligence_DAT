# Registre des preuves

Les chemins ci-dessous sont relatifs à preuves/, sauf mention explicite. Les captures sont des images authentiques du navigateur ; les journaux et résultats JSON constituent les preuves numériques reproductibles.

| ID | Objectif | Commande / manipulation | Résultat réel | Fichier de preuve | TP |
|---|---|---|---|---|---|
| J3-P01 | Environnement et HDFS | docker version ; jps ; dfsadmin -report | NameNode/DataNode actifs ; 1 vivant ; dépôts J2 conservés | executions/J3-P01-diagnostic.txt ; captures/J3-P01-hdfs.jpg | 4.4 / 8.1 |
| J3-P02 | Session Spark complète | python scripts/exploration/test_spark.py | 35 lignes reason ; transformation, Parquet et relecture | executions/J3-P02-session-spark-final.log ; controles/J3-P02-session-spark.json | 4.4 |
| J3-P03 | Accès et copies sources | python scripts/exploration/preparer_entrees.py | 2 DAT déposés sans écrasement ; SHA-256 égaux | executions/J3-P03-entrees.log ; controles/J3-P03-entrees-hdfs.json | 4.5 / 8.1 |
| J3-P04 | Exploration exécutée | python scripts/exploration/notebook.py | 5 cellules code exécutées ; schémas, nulls et domaines | notebooks/UC06_exploration.ipynb (racine J3) ; controles/J3-P04-*.json ; captures/J3-P04-notebook.jpg | 4.6 / 8.5 |
| J3-P05 | Jointure contrôlée | cellule 4 du notebook | 667 579 avant/après ; 0 clé dupliquée ; 0 référence absente | controles/J3-P05-jointure-exploration.json ; captures/J3-P05-bilan.jpg | 4.8.3 |
| J3-P06 | Transformations et Silver | python scripts/transformation/transformer.py | 2 Silver relus ; 2 575 trims ; 0 rejet | executions/J3-P06-transformation.log ; controles/J3-P06-transformation.json | 4.7-4.9 |
| J3-P07 | Gold analytique | même pipeline, groupBy produit | 17 820 agrégats ; top 10 et totaux conservés | controles/J3-P06-transformation.json (top10, totals, outputs) | 4.10 / 8.3 |
| J3-P08 | Écriture/relecture Parquet | parquet_checked ; hdfs dfs -ls et -du | 3 jeux relus ; volumes et types conformes | parquet/J3-P08-parquet.json ; parquet/J3-P08-listing-hdfs.txt | 4.11 / 8.4 |
| J3-P09 | Qualité et calcul indépendant | assertions du pipeline et inventaire Python | 73 contrôles ; 0 bloquant en échec ; anomalies signalées | controles/J3-P09-qualite.json ; controles/registre_qualite.csv | 4.12 / 8.2 / 8.5 |
| J3-P10 | Relecture autonome | python scripts/qualite/verifier.py | Sorties, totaux, notebook et SHA-256 reason J2 vérifiés | executions/J3-P10-verification.log ; controles/J3-P10-verification.json | 8.1-8.5 |
| J3-P11 | Protection et livraison | python verification/verifier_fichiers.py | 158 fichiers de contenu protégés ; présence des livrables contrôlée | controles/J3-P11-verification-fichiers.json | 4.13 / 10.2 |
| J3-P12 | Refus de réécriture du même lot | Relance transformer.py avec le paramétrage du lot final | Arrêt avant écriture : Lot déjà présent, code 1 attendu | executions/J3-P12-reexecution-refusee.log | 4.13 / sécurité des écritures |

## Captures complémentaires facultatives

Les captures fournies montrent HDFS, le notebook exécuté et le bilan des références. Aucune capture manuelle indispensable ne reste à réaliser. Pour un oral, ouvrir un terminal et lancer la relecture autonome, puis capturer le schéma Gold et les totaux. La commande exacte se trouve dans le README. Une capture d'un export HTML du notebook est identifiée comme telle et ne prétend pas montrer un serveur JupyterLab actif.

## Incidents conservés

J3-P06-tentative-initiale.log, J3-P06-tentative-r2.log, spark-thread-diagnostic.txt et spark-thread-diagnostic-r2.txt conservent les essais non validés et leur diagnostic. Le dernier lot r3 est le seul lot final. Les avertissements Java natifs sont présents dans les journaux, sans être effacés.


## J3-P13 - Export vérifié et finalisation

Objectif : rendre les Parquet du lot final transmissibles sans accès au PC d'origine. Commande : python scripts/qualite/exporter_parquet.py, puis python scripts/qualite/relire_export.py. Résultat : six Parquet et trois _SUCCESS, neuf SHA-256 concordants, schémas et comptages confirmés, HDFS inchangé. Preuves : executions/J3-P13-export-parquet.log et donnees_produites/verification_export/ (racine J3). Correspondance TP : 4.9, 4.10, 4.11, 8.3, 8.4, 10.2. Le pipeline n'a pas été relancé.

Contrôles ciblés de l'orchestrateur : verification/audit_reproduction.md. Cinq tests isolés avec Docker simulé ; ils ne constituent pas une nouvelle exécution complète réelle.
