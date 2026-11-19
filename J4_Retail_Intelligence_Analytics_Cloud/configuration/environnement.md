# Environnement réellement utilisé

Exécution le 19 novembre 2026 (Europe/Paris). Les journaux et le lot portent l'heure UTC.
Windows et Docker Desktop/WSL2 hébergent les deux conteneurs déjà utilisés au Jour 3.
retail-j3-spark exécute Spark local[2], dans la limite existante de 4 Gio et 4 CPU ; aucun port publié.
retail-j2-hdfs-1 héberge un NameNode et un DataNode. NiFi reste arrêté.

| Composant | Valeur constatée |
| --- | --- |
| Python calcul | 3.12.3 |
| Interpréteur | /tmp/retail-j3-venv/bin/python |
| Spark / PySpark | 3.5.7 |
| Java | 17.0.18 |
| Hadoop serveur / client Spark | 3.5.0 / 3.3.4 |
| pandas | 2.2.3 |
| matplotlib | 3.9.4 |
| numpy | 2.5.5 |
| notebook | 7.3.3 |
| jupyterlab | 4.3.8 |
| nbformat | 5.10.4 |
| nbclient | 0.10.4 |
| nbconvert | 7.16.6 |
| ipykernel | 6.31.0 |
| Lecture | HDFS RPC, hdfs://hdfs:9000 |
| Driver / shuffle | 1 536 Mio / 4 partitions |


Le venv /tmp/retail-j3-venv a été conservé. Pandas 2.2.3, Matplotlib 3.9.4 et Notebook 7.3.3 ont été ajoutés ;
Notebook fournit également JupyterLab 4.3.8. Aucun Python ni Java global n'a été remplacé.
Le gel complet est dans preuves/environnement/requirements.lock.txt. Les versions J3 des cinq bibliothèques
PySpark, nbformat, nbclient, nbconvert et ipykernel sont restées identiques.

## Tests fonctionnels

Le notebook est exécuté de haut en bas par nbclient dans ce venv : création Spark, lectures des trois Parquet,
schémas, comptages, qualification des tickets, paniers, agrégations, conversion de 10 produits, 12 magasins et 9 catégories vers Pandas, trois figures Matplotlib
et export PNG. Les figures sont également enregistrées dans les sorties du notebook.
JupyterLab est installé et sa version est contrôlée ; le serveur interactif n'a pas été exposé ni utilisé pour les calculs.

## Difficultés résolues

Les conteneurs étaient arrêtés. Leur redémarrage a conservé les volumes. Le NameNode a quitté automatiquement
le mode sûr ; aucun forçage ni formatage. La copie de travail /tmp/retail-j4 a nécessité d'être attribuée à hadoop,
sans modifier les droits des données J3. Les avertissements NativeCodeLoader et WindowExec sont conservés
dans le journal : les médianes exactes trient dans une partition, acceptable pour ce lot pédagogique.
Une première extraction PDF a rencontré l'encodage Windows ; la lecture UTF-8 a résolu le problème.
