# Découverte de Hadoop et organisation de HDFS

Hadoop Common fournit les bibliothèques et clients. HDFS sert ici au stockage. Le NameNode gère l’espace de noms, les droits et l’association des fichiers à leurs blocs. Le DataNode persiste les blocs et répond aux lectures et écritures. Le client interroge le NameNode, puis échange les données avec le DataNode.

Le déploiement du TP est pseudo-distribué, avec un processus NameNode et un processus DataNode sur un même conteneur Linux. Le facteur de réplication 1 correspond à cette topologie pédagogique et laisse une seule copie de chaque bloc sur le DataNode. [J2-P01 · paramètres](../preuves/hadoop/J2-P01-versions.txt)

Le 17 novembre 2026 à 12 h 46 (heure de Paris), les volumes `retail-j2_namenode` et `retail-j2_datanode` étaient vides et montés exclusivement dans `retail-j2-hdfs-1`. Les contrôles de processus ont confirmé l’absence de démons HDFS. Après accord explicite, l’unique commande `hdfs namenode -format -nonInteractive` a créé les métadonnées du NameNode et retourné le code 0. Le DataNode a rejoint le même identifiant de cluster au démarrage. [Contrôles avant initialisation](../preuves/hadoop/J2-P02-controles-avant-format.txt) · [Journal d’initialisation](../preuves/hadoop/J2-P02-initialisation-namenode.txt)

`jps -l` a listé les deux processus et `hdfs dfsadmin -report` a indiqué **un DataNode actif**, aucun bloc manquant et le statut Normal. Le mode sans échec était désactivé. Les commandes `-ls /`, `-du -h /` et `-df -h /` ont ensuite répondu via `hdfs://hdfs:9000`. La racine était vide avant création du Data Lake. `-df` indiquait 948,9 G disponibles dans le système de fichiers du conteneur. [Rapport et commandes](../preuves/hadoop/J2-P02-hdfs-actif.txt) · [Capture NameNode](../preuves/captures/J2-P02-hdfs-up.png)

## Arborescence HDFS du TP2

```text
/retail-lake/
  raw/
    tpcxbb/
      initial/
      refresh/
    nifi/
  bronze/
    tpcxbb/
  silver/
  gold/
  quality/
  logs/
```

| Zone | Rôle dans le projet |
|---|---|
| `raw/tpcxbb/initial`, `raw/tpcxbb/refresh` | Garder le contenu d’origine pour le contrôle et le rejeu. Le chemin rend les deux lots identifiables. |
| `raw/nifi` | Destination du seul essai automatisé. Elle isole ce dépôt du dépôt manuel `raw/tpcxbb/initial`. |
| `bronze/tpcxbb` | Structurer les octets reçus et leurs métadonnées de réception par domaine et lot. Le Jour 1 regroupait Raw et Bronze comme zone de réception. Le Jour 2 explicite le point d’arrivée et l’organisation du lot. |
| `silver` | Accueillir les tables typées, fiabilisées et harmonisées. |
| `gold` | Publier les jeux destinés à la BI et aux indicateurs métier. |
| `quality` | Conserver résultats de contrôles, rejets et anomalies par lot, à part des données métier. |
| `logs` | Conserver les traces techniques des exécutions et des reprises. |

Les huit répertoires feuilles ont été créés avec `hdfs dfs -mkdir -p`, testés individuellement avec `-test -d` et listés avec `-ls -R`. Les répertoires sont en mode 755. Le seul répertoire attribué au compte `nifi` est `/retail-lake/raw/nifi`. [Arborescence et permissions](../preuves/hdfs/J2-P03-arborescence.txt)

## Dépôt manuel vérifié

`hdfs dfs -put` a écrit `reason.dat` sous `/retail-lake/raw/tpcxbb/initial/reason.dat`. HDFS a retourné **3 105 octets**, propriétaire `hadoop`, groupe `supergroup`, mode 644 et réplication 1. `-cat` et `-get` ont confirmé la lecture. La copie relue est identique octet pour octet au fichier source et présente le SHA-256 de J2-P04. [Dépôt](../preuves/hdfs/J2-P05-depot-manuel.txt) · [Lecture et intégrité](../preuves/hdfs/J2-P06-integrite.txt)

Un lot se retrace par son chemin source, sa destination, sa méthode de dépôt, son empreinte et l’horodatage du traitement. La provenance NiFi y associe l’UUID du FlowFile.
