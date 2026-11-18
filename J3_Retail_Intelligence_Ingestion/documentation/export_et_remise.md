## 11. Copies Parquet fournies avec la remise

Le lot final reste **20261118T113628Z-243a5fb5-r3**. Une copie complète de ses trois répertoires Parquet est désormais présente sur Windows :

- donnees_produites/export/silver/store_sales : 667 579 lignes ; deux fichiers Parquet et _SUCCESS ; 34 766 704 octets.
- donnees_produites/export/silver/item : 17 820 lignes ; deux fichiers Parquet et _SUCCESS ; 3 571 219 octets.
- donnees_produites/export/gold/ventes_par_produit : 17 820 lignes ; deux fichiers Parquet et _SUCCESS ; 1 307 151 octets.

Total : six fichiers Parquet, trois marqueurs _SUCCESS, 39 645 074 octets. Le manifeste HDFS original donnees_produites/manifest.json reste inchangé. Le nouveau donnees_produites/verification_export/manifeste_export.json relie chaque fichier local à son chemin HDFS, sa taille et ses deux SHA-256. SHA256SUMS.txt contient les neuf empreintes. controle_export.md et relecture_locale.log consignent les contrôles exécutés.

Le téléchargement a utilisé hdfs dfs -get, sans écrasement, vers un dossier de validation neuf. Le dossier export n'a été publié qu'après vérification des fichiers, schémas, nombres de lignes, identifiant de lot et totaux. Les neuf SHA-256 HDFS correspondent aux copies Windows, y compris les marqueurs vides. Les états HDFS avant/après sont identiques sur les chemins, tailles, dates de modification et checksums Hadoop de tous les fichiers du lac. Le pipeline n'a pas été relancé.

### Relire les copies sans HDFS

Dans l'environnement Docker existant :

```powershell
docker exec retail-j3-spark /tmp/retail-j3-venv/bin/python /work/scripts/qualite/relire_export.py
```

Ce script configure explicitement file:/// et relit les copies Windows montées sous /work. Il vérifie les neuf SHA-256, les schémas, les trois comptages et les totaux Gold : 33 755 474 unités, 1 150 529 586,37 UM et 667 579 lignes de vente agrégées. Cette relecture a réellement été exécutée.

Sur un autre poste disposant de Java 17 et d'un environnement Python/PySpark compatible, depuis la racine du dossier remis :

```text
python scripts/qualite/relire_export.py --racine .
```

Cette lecture ne requiert ni HDFS ni les DAT originaux. Pour installer les bibliothèques sur un nouvel environnement, utiliser un venv et configuration/requirements.lock.txt ; aucune installation globale. La combinaison effectivement vérifiée est Ubuntu dans Docker, Python 3.12.3 et Java 17.0.18. Une installation native Windows sur un autre poste n'a pas été testée.

### Reproduction et état de l'orchestrateur

La procédure complète reste scripts/reproduire.ps1, avec les mêmes prérequis, commandes de démarrage et d'arrêt documentés plus haut. Les étapes de traitement ont été exécutées lors de la réalisation initiale. Lors de cette mission corrective, les vérifications supplémentaires portent sur les chemins, l'ordre, les paramètres, les dépendances, les erreurs, les lots et l'archivage. Cinq tests du pilotage sur copies isolées utilisent une fonction Docker explicitement simulée : ils ne lancent pas Spark et ne constituent pas une exécution complète en production. Les relectures des Parquet exportés utilisent en revanche le vrai Spark.

Corrections ciblées : contrôle des scripts et du manifeste avant action ; validation du format du lot avant de construire le chemin d'archive ; archivage du manifeste des résultats ; propagation des erreurs de diagnostic/démarrage HDFS ; contrôle des deux fichiers item et des bibliothèques notebook nécessaires. Le refus d'une archive existante est conservé et testé. Les nouveaux lots restent créés dans preparer_entrees.py par horodatage UTC et suffixe UUID ; les écritures de transformation restent en errorifexists.

L'exécution complète réelle de reproduire.ps1 reste non vérifiée. La simulation valide le pilotage et les protections, sans prouver un nouveau traitement complet. Les détails et résultats sont dans verification/audit_reproduction.md. L'export validé n'est jamais écrasé par reproduire.ps1 ; pour un autre lot, prévoir un nouvel export et sa validation.

### Dossier transmissible

A_REMETTRE_J3 contient le rapport final, les documents, le notebook exécuté, les scripts/configurations, les trois jeux Parquet et les preuves sélectionnées. LIRE_AVANT_REMISE.md explique l'évaluation sans le PC d'origine. MANIFESTE_REMISE.json et verification/verifier_remise.py permettent de contrôler les fichiers reçus. L'archive A_REMETTRE_J3.zip contient ce dossier ; sa liste, ses CRC et les SHA-256 de chaque entrée ont été vérifiés après création.

Les DAT bruts complets et volumes Docker ne sont pas inclus. Une nouvelle transformation depuis Raw demande donc le kit original et l'environnement Hadoop décrit, tandis que l'examen des résultats et leur relecture locale sont autonomes. Les données restent synthétiques, la devise n'est pas attestée et Parquet seul n'est pas une table transactionnelle.
