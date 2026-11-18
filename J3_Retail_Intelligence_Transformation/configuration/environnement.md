# Fiche environnement

Exécution le 18 novembre 2026 (Europe/Paris). Les journaux Docker utilisent UTC, soit une heure de moins à cette date. Les identifiants de lots portent l'heure UTC.

| Composant | Valeur observée |
|---|---|
| Hôte | Windows 11 Professionnel 10.0.26200 ; 16 380 056 Kio de RAM totale |
| Virtualisation | WSL2, distribution docker-desktop ; moteur Linux Docker Desktop |
| Docker Desktop / Engine | 4.84.0 / 29.6.2 |
| Ressources du moteur | 16 processeurs visibles ; 8 126 324 736 octets de RAM |
| Conteneur Spark | retail-j3-spark ; limite 4 Gio et 4 CPU ; aucun port publié |
| Système Spark | Ubuntu 24.04.4 LTS ; image existante retail-j2-hadoop:3.5.0 |
| Python traitement | 3.12.3 ; /tmp/retail-j3-venv/bin/python |
| Java traitement | Temurin OpenJDK 17.0.18, déjà installé dans l’image J2 |
| Spark / PySpark / Py4J | 3.5.7 / 3.5.7 / 0.10.9.7 |
| Hadoop serveur / client Spark | 3.5.0 / 3.3.4 embarqué ; accès RPC réellement testé |
| Mode Spark | local[2], driver 1 536 Mio, shuffle 4 partitions, UI désactivée |
| Notebook | nbclient 0.10.4, nbformat 5.10.4, ipykernel 6.31.0 ; nbconvert 7.16.6 |
| Jupyter interactif | Pas de serveur JupyterLab installé ; notebook exécuté par nbclient |
| HDFS | hdfs://hdfs:9000, NameNode et DataNode dans retail-j2-hdfs-1 ; un DataNode vivant |
| HDFS stockage | Volumes retail-j2_namenode et retail-j2_datanode conservés ; réplication J3 à 1 |
| NiFi | Conteneur J2 existant, resté arrêté ; aucune modification de configuration |
| Windows Java / Python rapport | Java 21.0.2 non utilisé pour Spark ; Python fourni 3.12.14 pour documentation |

## Validation réelle

J3-P02 prouve la lecture HDFS de reason.dat, 35 lignes, printSchema, trim, écriture et relecture Parquet. Les traitements complets J3-P06 et la relecture autonome J3-P10 confirment ensuite le fonctionnement sur les données retenues. L'avertissement NativeCodeLoader indique l'utilisation des classes Java de remplacement ; il n'a pas empêché les écritures ni les relectures.

## Réparation minimale autorisée

Le dossier J2 est actuellement sous J1. Le conteneur existant pointait vers l'ancien chemin Projet/J2_Retail_Intelligence_Ingestion/installation/hadoop. Docker y avait créé deux dossiers vides portant les noms des XML. Après autorisation explicite de l'utilisateur, ces deux dossiers vides ont été déplacés dans configuration/restauration_montages et remplacés par des copies identiques des XML actuels. Les fichiers originaux et les volumes n'ont pas été modifiés par cette réparation. Le NameNode et le DataNode existants ont ensuite été démarrés. Le mode sûr de démarrage s'est désactivé automatiquement. Aucun formatage n'a été lancé.

Les deux fichiers reason.dat J2 sont contrôlés par SHA-256 avant et après le travail. Les autres fichiers pédagogiques, J1/J2 et sources Windows sont protégés par un manifeste de 158 fichiers de contenu, avec 173 métadonnées Git recensées séparément.

## Références techniques

Compatibilité Java 17 / Python 3.8+ vérifiée dans la documentation officielle [Spark 3.5.7](https://spark.apache.org/docs/3.5.7/) et [Installation PySpark 3.5.7](https://spark.apache.org/docs/3.5.7/api/python/getting_started/install.html). Le client Hadoop embarqué n'est pas remplacé par les bibliothèques du serveur. La compatibilité utilisée ici est démontrée par les tests HDFS ; cela ne vaut pas certification de toutes les fonctionnalités Hadoop.
