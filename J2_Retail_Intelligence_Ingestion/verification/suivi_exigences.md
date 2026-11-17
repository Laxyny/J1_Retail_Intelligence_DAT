# Suivi des exigences et preuves · TP2

Bilan de la section 12.6 au 17 novembre 2026. **12 livrables applicables réalisés et vérifiés, 1 conditionnel sans objet pour la validation finale.** Les preuves couvrent l’initialisation autorisée, les deux dépôts et leur intégrité, l’erreur NiFi et le retour à la configuration valide, ainsi que la provenance.

## Les 13 livrables

| N° | Livrable §12.6 | État | Fichier ou preuve |
|---:|---|---|---|
| 1 | Fiche d’environnement | Réalisé et vérifié | [Diagnostic](../diagnostic_environnement.md), [fiche](../documentation/environnement.md), J2-P01, J2-P07 |
| 2 | Découverte Hadoop/HDFS | Réalisé et vérifié | [Fiche Hadoop](../documentation/architecture_hdfs.md), J2-P01 et J2-P02. Binaire, XML, volumes, processus et accès RPC vérifiés. |
| 3 | Inventaire des sources utilisées | Réalisé et vérifié | [Inventaire](../documentation/inventaire_sources.md), J2-P04 |
| 4 | Arborescence du Data Lake | Réalisé et vérifié | [Schéma et justification](../documentation/architecture_hdfs.md). Création et vérification des répertoires en J2-P03. |
| 5 | Commandes et résultats HDFS | Réalisé et vérifié | J2-P01, J2-P02 et J2-P03. Processus, inventaire HDFS, capacité et permissions. |
| 6 | Preuves du dépôt et contrôles HDFS | Réalisé et vérifié | J2-P05 et J2-P06. Présence, taille, permissions, lecture et SHA-256. |
| 7 | Schéma du flux NiFi | Réalisé et vérifié | [Schéma](../documentation/ingestion_nifi.md), J2-P09 |
| 8 | Export ou captures de configuration NiFi | Réalisé et vérifié | [Export](../ingestion/nifi/UC04-GetFile-PutHDFS.json), J2-P08, J2-P09 |
| 9 | Preuves d’exécution et de dépôt NiFi | Réalisé et vérifié | J2-P10. Compteurs, capture, listing HDFS et intégrité. |
| 10 | Tableau des erreurs et corrections | Réalisé et vérifié | [Diagnostic et test](../documentation/erreurs_corrections.md), J2-P11. Chemin absent, validation rejetée, retour à l’état valide. |
| 11 | Documentation de la provenance | Réalisé et vérifié | [Parcours et événements](../documentation/provenance.md), J2-P12. UUID, heures, destination et capture. |
| 12 | Script de repli, le cas échéant | Sans objet pour la validation finale | [Script local](../ingestion/scripts/repli_local.py) et J2-P13 conservés comme preuve de l’étape intermédiaire. |
| 13 | README de reproduction | Réalisé et vérifié | [README](../README.md). Versions, paramètres, commandes de démarrage, de dépôt, de vérification et d’arrêt. |

## Registre des preuves et tests

| ID | Commande ou manipulation exacte | Résultat observé ou état | Fichier ou capture | Exigence |
|---|---|---|---|---|
| J2-P01 | `docker compose exec -T hdfs` puis `hadoop version`, `java -version`, `jps`, `hdfs getconf -confKey` | Hadoop 3.5.0, Java 17, URI HDFS et réplication 1. | [J2-P01-versions.txt](../preuves/hadoop/J2-P01-versions.txt) | UC-03 étape 1 |
| J2-P02 | `docker volume inspect`, `docker ps --filter volume=`, `docker top`, `find` et `jps -l`. Première initialisation `hdfs namenode -format -nonInteractive`, démarrage des deux démons et `dfsadmin -report`, `dfs -ls /`, `-du -h /`, `-df -h /`. | Volumes neufs, vides, montage exclusif et démons arrêtés avant l’initialisation. Code 0. Ensuite NameNode actif, un DataNode vivant, mode sans échec désactivé. | [Précontrôles](../preuves/hadoop/J2-P02-controles-avant-format.txt) · [Initialisation](../preuves/hadoop/J2-P02-initialisation-namenode.txt) · [HDFS actif](../preuves/hadoop/J2-P02-hdfs-actif.txt) · [Capture](../preuves/captures/J2-P02-hdfs-up.png) | UC-03 étapes 1–2, accès HDFS §15 |
| J2-P03 | `hdfs dfs -mkdir -p` et `-test -d` pour les huit chemins feuilles, `hdfs dfs -ls -R /retail-lake`. | Tous les chemins existent. Répertoires mode 755, `raw/nifi` appartient à `nifi`. | [Arborescence](../preuves/hdfs/J2-P03-arborescence.txt) | UC-03 étape 3, création et permissions §15 |
| J2-P04 | Python `read_bytes`, `splitlines`, contrôle des champs et `sha256` | `reason.dat` initial, 3 105 octets, 35 lignes, trois champs. | [J2-P04-source.txt](../preuves/hdfs/J2-P04-source.txt) | Inventaire, UC-03 étape 4 |
| J2-P05 | `hdfs dfs -put /tmp/j2-reason.dat /retail-lake/raw/tpcxbb/initial/reason.dat`, `hdfs dfs -ls -h` de la destination. | Le fichier de 3,0 K apparaît en Raw initial. | [Dépôt manuel](../preuves/hdfs/J2-P05-depot-manuel.txt) | UC-03 étape 4, dépôt §15 |
| J2-P06 | `hdfs dfs -stat`, `-cat`, `-get` du fichier et `sha256sum` puis `cmp` de la copie relue. | 3 105 octets, mode 644, réplication 1. Lecture et comparaison réussies. | [Intégrité](../preuves/hdfs/J2-P06-integrite.txt) | UC-03 étape 5, lecture, taille et permissions §15 |
| J2-P07 | `nifi.sh status`, HTTP GET `/nifi/`, API `GET /flow/about`, `GET /flow/processor-types` | Service UP, HTTP 200, GetFile et PutHDFS 2.12.0 présents. | [Service](../preuves/nifi/J2-P07-service.txt) · [Catalogue](../preuves/nifi/J2-P07-processeurs.json) · [NAR](../preuves/nifi/J2-P07-nar.txt) | UC-04 étapes 6–7 |
| J2-P08 | Configurer les deux processeurs, lire leur état via l’API, exporter le groupe via `GET /process-groups/{id}/download`, ouvrir leurs propriétés. | Processeurs configurés et `VALID`. | [État et paramètres](../preuves/nifi/J2-P08-configuration.json) · [Export](../ingestion/nifi/UC04-GetFile-PutHDFS.json) · [Capture GetFile](../preuves/captures/J2-P08-GetFile.png) · [Capture PutHDFS](../preuves/captures/J2-P08-PutHDFS.png) | UC-04 étape 8 |
| J2-P09 | Ouvrir le groupe NiFi et afficher les processeurs et files. | Canvas réel, relations `success` et `failure`. | [J2-P09-flux.png](../preuves/captures/J2-P09-flux.png) | UC-04 étape 8, capture §16 |
| J2-P10 | Démarrer PutHDFS puis GetFile, relever les compteurs, `hdfs dfs -ls -h`, `-du -h`, `-stat` et `-get` de la destination NiFi, comparer SHA-256. | Un FlowFile de 3 105 octets. Fichier HDFS présent et identique à la source, dépôt manuel préservé. | [Lancement](../preuves/nifi/J2-P10-execution.txt) · [Compteurs](../preuves/nifi/J2-P10-compteurs.json) · [Capture](../preuves/captures/J2-P10-execution-nifi.png) · [Dépôt](../preuves/nifi/J2-P10-depot-nifi.txt) | UC-04 étape 9, lecture et dépôt §15 |
| J2-P11 | Après le transfert, arrêter les processeurs. Régler `Input Directory` sur le chemin absent, relever l’erreur et rétablir le chemin vérifié. | GetFile passe de `VALID` à `INVALID` avec « Directory does not exist », puis revient à `VALID`. | [Exécution](../preuves/nifi/J2-P11-test-erreur.txt) · [Capture](../preuves/captures/J2-P11-erreur-controlee.png) · [Rétablissement](../preuves/nifi/J2-P11-restore.json) | UC-04 étape 10, erreur contrôlée §15 |
| J2-P12 | **Data Provenance**, **View Details** sur `SEND` et lecture des événements par l’API NiFi. | Quatre événements horodatés, un UUID. `SEND` confirme l’URI HDFS et l’attribut `filename` vaut `reason.dat`. | [Capture](../preuves/captures/J2-P12-provenance.png) · [Détail SEND](../preuves/captures/J2-P12-detail-envoi.png) · [JSON des événements](../preuves/nifi/J2-P12-provenance.json) | UC-04 étape 11, traçabilité §15 |
| J2-P13 | `python ingestion/scripts/repli_local.py <source>`, relance avec le même fichier puis avec une source absente. | Copie locale vérifiée, codes 0/1/1. La collision a conservé le premier résultat. | [Journal](../preuves/repli_local/J2-P13-journal.txt) · [Contrôles](../preuves/repli_local/J2-P13-controles.txt) | Repli §12.4 |

Les 14 questions de recul sont traitées dans [la fiche §19](../documentation/questions_recul.md). Les preuves répertoriées répondent aux tests HDFS et NiFi de la section 15 et aux exigences de conservation des sections 16 et 17.
