# Retail Intelligence Platform - Jour 4

UC-08 exécuté sur HDFS ; UC-07 étudié et simulé documentairement en parcours B. Aucun service Azure déployé.
Rapport : rapport/DAT_Retail_Intelligence_J4.pdf ; version modifiable : rapport/DAT_Retail_Intelligence_J4.md.
Les onze livrables sont indexés dans verification/suivi_exigences.md ; preuves dans preuves/registre_preuves.md.

Version améliorée V2 : K03 et K04 sont qualifiés et calculés à partir des transactions Silver ;
le classement par catégories complète les produits et magasins. Les quatre KPI métier sont prioritaires,
J4-L01 reste secondaire. L'ancienne remise est sauvegardée séparément, hors de la nouvelle archive.

## Prérequis et sources

Java 17, Python 3.12, PySpark 3.5.7, Pandas 2.2.3, Matplotlib 3.9.4 ; Notebook 7.3.3/JupyterLab 4.3.8.
Versions observées et dépendances complètes : configuration/environnement.md et preuves/environnement/requirements.lock.txt.
Dans le poste d'origine, réutiliser le venv /tmp/retail-j3-venv/bin/python du conteneur retail-j3-spark.
Sur un autre poste, créer un venv et installer le gel dans ce venv ; Java et les accès HDFS restent des prérequis séparés.
Le runtime Windows de documentation est distinct et n'exécute pas Spark. Son gel est dans configuration/requirements-rapport.txt.

Entrées : lot 20261118T113628Z-243a5fb5-r3, Silver store_sales (667 579), item (17 820), Gold ventes_par_produit (17 820).
Les URI exactes sont dans preuves/analyses/inventaire.json. Les données brutes et Parquet volumineux ne sont pas dans la remise J4.
Une copie complète vérifiée est déjà dans le J3 adjacent : donnees_produites/export, avec son manifeste d'export.

## Poste d'origine : démarrage sans transformation

Ouvrir PowerShell dans la racine du dossier J4. Les conteneurs doivent déjà exister ; ne pas recréer les volumes.
Ne pas relancer reproduire.ps1 ni les transformations J3. Démarrer les deux conteneurs seulement s'ils sont arrêtés :

```powershell
docker start retail-j2-hdfs-1 retail-j3-spark
docker exec retail-j2-hdfs-1 jps
```

Si les démons ne figurent pas dans jps, démarrer seulement ceux qui manquent :

```powershell
docker exec retail-j2-hdfs-1 hdfs --daemon start namenode
docker exec retail-j2-hdfs-1 hdfs --daemon start datanode
docker exec retail-j2-hdfs-1 hdfs dfsadmin -report
docker exec retail-j2-hdfs-1 hdfs dfsadmin -safemode get
```

Attendre le démarrage normal ; ne jamais formater le NameNode. NiFi n'est pas requis.
Copier J4 dans un nouveau répertoire de travail du conteneur ; choisir un nom neuf si cette copie existe déjà :

```powershell
docker cp . retail-j3-spark:/tmp/retail-j4-relecture
docker exec -u root retail-j3-spark chown -R hadoop:hadoop /tmp/retail-j4-relecture
docker exec retail-j3-spark /tmp/retail-j3-venv/bin/python /tmp/retail-j4-relecture/analytics/scripts/executer_notebook.py
```

Ce script reconstruit le notebook depuis analyser.py, l'exécute avec nbclient et produit les sorties HTML, CSV, JSON et PNG.
Pour le script seul : remplacer executer_notebook.py par analyser.py. Il calcule les quatre KPI métier, le volume technique et les contrôles avec asserts.
Les résultats sont écrits exclusivement dans la copie J4 du conteneur ; ils ne sont pas automatiquement recopiés vers Windows.
Pour récupérer une nouvelle exécution, copier ses sous-dossiers analytics/outputs, analytics/visualisations, analytics/notebooks et preuves/analyses
vers un dossier Windows neuf et contrôler les résultats avant d'en faire une remise. Les documents rédigés reflètent le lot étudié ici.

## Relecture portable à partir des copies Parquet J3

Sur une machine Linux avec Java/Python compatibles, depuis la racine J4, définir des chemins adaptés :

```bash
export J4_MODE=local
export J4_J3_EXPORT=/chemin/vers/J3/donnees_produites/export
python analytics/scripts/executer_notebook.py
```

J4_SALES, J4_ITEM et J4_GOLD peuvent remplacer individuellement les URI d'entrée. J4_ROOT choisit le dossier de sortie du script seul ;
le constructeur de notebook utilise sa propre racine. Les asserts refusent un lot Gold différent ou des références incohérentes.
Le mode local ne doit pas être présenté comme une lecture HDFS. Le notebook remis a été exécuté en mode hdfs.
Le mode local J4 sur un autre poste reste non exécuté dans cette mission ; la relecture locale J3 est documentée séparément.

## Ouvrir et exécuter le notebook

Jupyter installé peut ouvrir analytics/notebooks/TP4_Retail_Intelligence.ipynb avec le noyau du même venv.
Le script ci-dessus ne nécessite pas d'exposer un serveur. Dans un environnement personnel autorisé :

```bash
python -m jupyter lab analytics/notebooks/TP4_Retail_Intelligence.ipynb --ip=127.0.0.1 --no-browser
```

Choisir le bon noyau et exécuter toutes les cellules. Les variables d'entrée doivent être définies avant le lancement.
Les conteneurs du poste d'origine ne publient aucun port Jupyter ; l'export HTML permet d'examiner le notebook hors connexion.

## Résultats et vérifications

analytics/outputs/kpi.csv : K01 à K04, puis J4-L01 secondaire. statistiques.csv : cinq profils numériques, avec médianes exactes.
transactions.json et repartition_lignes_par_ticket.csv : qualification, panier moyen et distribution des lignes par ticket.
top10_produits.csv, ventes_par_magasin.csv et ventes_par_categorie.csv : petits tableaux des trois graphiques ; contributions_produits.csv : agrégats des 17 820 produits.
analytics/visualisations : trois PNG. preuves/analyses/controles.csv : tous les contrôles réexécutés, dont totaux J3, tickets, paniers, catégories et rapprochement par produit.
preuves/analyses/qualification_transactions.json : nulls, collisions magasin/date/client et provenance initiale J1.
verification/verifier_livrables.py contrôle les sorties sauvegardées, le notebook, les figures et la couverture documentaire.
verification/verifier_remise.py contrôle les empreintes du dossier transmissible sans Spark ni données brutes.

## Documents Azure et génération du rapport

cloud/architecture : cible, schémas modifiables, correspondance et sources officielles.
cloud/adls_gen2 : zones, nommage, rétention et HNS ; cloud/securite : matrice et limites locales ; cloud/simulation : scénario et coûts.
Ne pas exécuter des créations Azure : ces documents sont une étude, pas un déploiement.
La capture de refus gratuit est recadrée sans identifiants personnels dans preuves/architecture.
Questions : documentation/questions_recul.md, quatorze formulations du TP.
Génération documentaire Windows (avec un venv fournissant les dépendances rapport) :

```text
python rapport/preparer_documents.py
python rapport/dessiner_architectures.py
python rapport/exporter_pdf.py
python verification/verifier_livrables.py
```

preparer_documents.py est l'outil de maintenance du poste d'origine : il référence les documents antérieurs et la capture locale.
Dans une remise autonome, les documents et l'image anonymisée sont déjà fournis ; exporter_pdf.py les réutilise sans les sources J1/J2/J3.
La génération du PDF n'oblige donc pas à reconstruire tout le projet. Le conditionnement prépare et vérifie une remise candidate,
conserve l'ancienne hors du dossier final, puis publie la nouvelle après validation. Le journal V2 est dans verification/correction_v2/journal_changements.md.

## Arrêt et limites

Les scripts arrêtent la session Spark. Fermer Jupyter s'il est lancé ; puis, si aucun autre travail n'utilise ces conteneurs :

```powershell
docker stop retail-j3-spark
docker exec retail-j2-hdfs-1 hdfs --daemon stop datanode
docker exec retail-j2-hdfs-1 hdfs --daemon stop namenode
docker stop retail-j2-hdfs-1
```

Conserver les conteneurs et les volumes. Aucun docker compose down -v ni formatage.
Lab mono-nœud, authentification HDFS simple, devise inconnue, données synthétiques, aucune cause commerciale démontrée.
Les PDF/CSV/notebook peuvent être évalués sans réexécution ; le recalcul exige le lot J3 et un environnement compatible.
