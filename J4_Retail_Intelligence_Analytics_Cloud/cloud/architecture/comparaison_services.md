# Correspondance fonctionnelle Azure / open source

Les noms ne constituent pas des équivalences complètes. Tous les services Azure restent étudiés.

| Fonction | Azure proposé | Composant du parcours B / état | Limite de correspondance |
| --- | --- | --- | --- |
| Stockage Data Lake | ADLS Gen2 avec HNS | HDFS réel J2/J3, relu en J4 | HDFS mono-nœud n'est ni stockage objet managé ni service hautement disponible. MinIO serait un stockage S3 étudié, non installé. |
| Transformation | Synapse Spark | PySpark 3.5.7 réellement utilisé | Même famille de moteur, mais exploitation, réseau et runtimes diffèrent. |
| Requêtes SQL | Synapse SQL serverless ou dédié selon besoin | Spark SQL utilisé pour les médianes ; Trino étudié | Spark SQL ne reproduit pas tout le service SQL managé ; Trino serait un moteur supplémentaire. |
| Orchestration / intégration | ADF envisagé | Scripts et nbclient J4 ; NiFi réel J2, arrêté J4 | Les scripts ne fournissent pas toute la supervision ADF ; Airflow pourrait planifier, sans transformer lui-même. |
| Tables analytiques | Fichiers/tables adaptés aux moteurs Azure | Parquet Snappy réel | Parquet seul n'assure pas des transactions ACID. Iceberg serait un format de table avec métadonnées, pas un moteur ni Synapse. |
| Catalogue | Métadonnées des services Azure | Schémas Parquet et manifestes JSON réels | Pas de catalogue partagé installé. Nessie ou Hive Metastore seraient étudiés seulement si des tables Iceberg devaient être ajoutées. |
| Visualisation | Power BI éventuel | Jupyter et Matplotlib réels | Images et notebook n'offrent pas une plateforme BI de diffusion. Aucun tableau de bord ajouté. |
| Identités / accès | Entra, RBAC, ACL | Compte hadoop, permissions HDFS et isolation Docker constatés | Authentification simple et permissions larges de lab ; pas d'équivalence avec l'identité fédérée Azure. |
| Exécution | Services managés | Docker Desktop/WSL2 existant | Administration, sauvegarde et disponibilité restent locales. |

Synapse regroupe plusieurs fonctions ; les reproduire demanderait stockage, Spark, moteur SQL, catalogue et orchestration.
Le socle TP4 autorise de s'arrêter à la démonstration locale et à cette comparaison argumentée.
MinIO, Iceberg, Trino, Nessie, Hive Metastore supplémentaire, Airflow, Superset, Delta Lake et Hudi n'ont pas été installés.
