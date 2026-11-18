# Retail Intelligence Platform - Jour 3 - UC-06

Travail exécuté sur les fichiers initiaux complets : 667 579 ventes magasin et 17 820 produits. Deux Silver et un Gold sont disponibles dans HDFS en Parquet Snappy. Le notebook a été exécuté de haut en bas. Le pipeline enregistre 73 contrôles, sans échec bloquant, et conserve les anomalies documentées. Livrable de synthèse : rapport/DAT_Retail_Intelligence_J3.pdf ; version modifiable : rapport/DAT_Retail_Intelligence_J3.md.

## 1. Prérequis et versions

Windows, PowerShell, Docker Desktop démarré en mode Linux/WSL2, environnement HDFS J2 conservé. Python de traitement 3.12.3, Java 17.0.18, Spark/PySpark 3.5.7, Hadoop serveur 3.5.0 et client Spark 3.3.4. Détails et limites de compatibilité : configuration/environnement.md. Aucun Java Windows n'a été remplacé. Aucun port Spark ou Jupyter n'est exposé.

## 2. Chemins réels

Racine J3 : C:\Users\Kevin GREGOIRE\Desktop\Projet\J3_Retail_Intelligence_Transformation

Racine J2 actuelle : C:\Users\Kevin GREGOIRE\Desktop\Projet\J1_Retail_Intelligence_DAT\J2_Retail_Intelligence_Ingestion

Entrées Windows : C:\Users\Kevin GREGOIRE\Desktop\Projet\01. Architecture DataLake, DataWarehouse, Lakehous\retail_project\retail_project\data ; fichiers store_sales/store_sales.dat et item/item.dat. Le conteneur Spark les voit sous /sources/data, en lecture seule. L'inventaire du refresh est informatif ; il n'est pas fusionné.

Copies Raw HDFS :

- hdfs://hdfs:9000/retail-lake/raw/j3/20261118T113628Z-243a5fb5/store_sales.dat
- hdfs://hdfs:9000/retail-lake/raw/j3/20261118T113628Z-243a5fb5/item.dat

Sorties finales :

- hdfs://hdfs:9000/retail-lake/silver/j3/20261118T113628Z-243a5fb5-r3/store_sales
- hdfs://hdfs:9000/retail-lake/silver/j3/20261118T113628Z-243a5fb5-r3/item
- hdfs://hdfs:9000/retail-lake/gold/j3/20261118T113628Z-243a5fb5-r3/ventes_par_produit

donnees_produites/manifest.json conserve les chemins, schémas, volumes et preuves de relecture. Les trois jeux Parquet sont aussi fournis sous donnees_produites/export, avec une copie complète validée et le manifeste détaillé sous donnees_produites/verification_export. Aucune source DAT brute n'est dupliquée dans la remise.

## 3. Démarrage et environnement isolé

Ouvrir PowerShell dans la racine J3 puis exécuter :

```powershell
& .\configuration\preparer.ps1
docker exec retail-j2-hdfs-1 hdfs dfsadmin -report
docker exec retail-j2-hdfs-1 hdfs dfsadmin -safemode get
```

Le script réutilise le conteneur HDFS et crée seulement retail-j3-spark s'il est absent. Il utilise le réseau retail-j2_default, l'image J2 déjà présente et un venv /tmp/retail-j3-venv. Aucun volume HDFS n'est monté directement dans Spark : les lectures/écritures passent par l'API HDFS. Le script n'installe les dépendances que si le venv manque. Le fichier configuration/requirements.lock.txt fixe toutes les versions Python observées.

Si HDFS vient de démarrer, attendre sa sortie automatique du mode sûr avant d'écrire. Si le démarrage échoue à cause des montages XML, consulter la fiche environnement ; ne pas reconstruire les volumes. Les deux chemins historiques ont été restaurés une fois, avec l'accord explicite de l'utilisateur. NiFi reste arrêté et n'est pas requis ici.

## 4. Relecture des résultats existants, sans nouveau lot

```powershell
docker exec retail-j3-spark /tmp/retail-j3-venv/bin/python /work/scripts/qualite/verifier.py
```

Cette commande relit les Parquet et recalcule les totaux ; elle vérifie également le notebook et les deux dépôts J2. Elle met à jour son compte rendu local J3-P10 sans réécrire les données HDFS.

## 5. Reproduction complète et ordre

```powershell
& .\scripts\reproduire.ps1
```

Ordre : préparer l'environnement ; archiver les preuves du lot précédent ; tester Spark ; inventorier toutes les lignes physiques avec Python ; créer de nouvelles copies Raw et vérifier leurs empreintes ; construire/exécuter le notebook ; appliquer les règles et écrire Silver puis Gold ; relire et vérifier. Les dépendances et chemins sont séparés du code. Les commandes individuelles exécutées dans Docker sont :

```text
/tmp/retail-j3-venv/bin/python /work/scripts/exploration/test_spark.py
/tmp/retail-j3-venv/bin/python /work/scripts/exploration/inventorier.py --sources /sources
/tmp/retail-j3-venv/bin/python /work/scripts/exploration/preparer_entrees.py
/tmp/retail-j3-venv/bin/python /work/scripts/exploration/notebook.py
/tmp/retail-j3-venv/bin/python /work/scripts/transformation/transformer.py
/tmp/retail-j3-venv/bin/python /work/scripts/qualite/verifier.py
```

Les règles documentées s'appliquent uniquement au périmètre décrit. Toute nouvelle anomalie bloquante doit être analysée avant validation d'un nouveau lot. Le rapport existant porte sur le lot 20261118T113628Z-243a5fb5-r3 ; une nouvelle exécution ne doit pas être confondue avec ce lot dans un tableau de restitution.

## 6. Fichiers et contrôles

scripts/uc06.py : session, lecture/typage, profils, normalisation et écriture contrôlée. scripts/exploration : inventaire physique, dépôt Raw et notebook. scripts/transformation : pipeline. scripts/qualite : relecture autonome. configuration/parametres : dictionnaire ordinal et chemins. preuves/controles : inventaire, contrôles, calcul indépendant et réconciliation. preuves/parquet : schémas avant/après, volumes et fichiers. documentation : inventaire, règles, modèle, résultats, qualité, formats et dix questions. verification/suivi_exigences.md : couverture du TP.

Pour ouvrir le notebook sans environnement Jupyter, utiliser l'export HTML preuves/notebook/UC06_exploration.html dans un navigateur. Il affiche les sorties sauvegardées, sans prétendre exécuter des cellules. Pour le recalcul, utiliser le script notebook.py, qui lance nbclient dans le venv. Aucun serveur JupyterLab n'est nécessaire.

## 7. Reprise sûre et incidents

Les écritures utilisent errorifexists et des chemins identifiés par un lot UTC + suffixe aléatoire. Relancer directement transformer.py avec le même paramétrage refuse la destination existante avant toute nouvelle écriture. Une exécution complète génère un nouveau lot, dont les preuves précédentes sont copiées dans preuves/historique. Il ne faut pas agréger plusieurs versions du même fichier source : sélectionner un lot validé unique. Une archive déjà existante provoque un arrêt plutôt qu'un écrasement.

Deux premières tentatives exceptAll ont été interrompues après diagnostic, sans supprimer leurs sorties. Elles ne constituent pas des publications valides. Le lot r3 utilise des empreintes agrégées, schémas, volumes et réconciliations indépendantes. Les avertissements NativeCodeLoader et de plan tronqué n'ont pas empêché les traitements finaux. Aucun repli pandas ou local n'a été utilisé ; les données analytiques sont dans HDFS.

## 8. Régénération documentaire

La documentation a été générée sous Windows avec le Python fourni par l'application (3.12.14), ReportLab 4.4.9, pypdf et pypdfium2, sans installation globale. Si ces outils sont absents sur un autre poste, installer configuration/requirements-rapport.txt dans un venv distinct. Après un nouveau lot, régénérer les documents, le PDF et l'export HTML ; vérifier les chiffres et adapter le récit si le périmètre change.

```text
python rapport/generer_documentation.py
python rapport/exporter_pdf.py
python verification/verifier_fichiers.py
```

La dernière commande se lance sur Windows depuis J3 et contrôle les 158 fichiers de contenu protégés à partir de chemins relatifs au projet. L'empreinte originale de J1/J2 reste la référence : ne pas la remplacer après une anomalie.

## 9. Arrêt adapté

Fermer toute session notebook en cours. Les scripts appellent spark.stop. Pour arrêter uniquement Spark :

```powershell
docker stop retail-j3-spark
```

Pour arrêter aussi HDFS une fois les autres travaux terminés :

```powershell
docker exec retail-j2-hdfs-1 hdfs --daemon stop datanode
docker exec retail-j2-hdfs-1 hdfs --daemon stop namenode
docker stop retail-j2-hdfs-1
```

NiFi étant déjà arrêté, aucune action n'est nécessaire. Conserver conteneurs et volumes. Ne pas lancer de formatage ni de suppression de volumes. Le venv est conservé dans la couche du conteneur Spark tant qu'il n'est pas supprimé.

## 10. Limites connues

Lab mono-nœud, réplication 1, pas de haute disponibilité. Contrôles exhaustifs des deux sources initiales, pas de validation de tout le kit. Devise inconnue, données synthétiques, aucune sémantique de refresh inventée. Les empreintes Parquet sont des contrôles probabilistes complétés par les contrôles métier. UC-05, HBase, formats de tables transactionnels, Azure et BI Jour 4 sont exclus. Le fichier Parquet seul n'est pas une table ACID.


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
