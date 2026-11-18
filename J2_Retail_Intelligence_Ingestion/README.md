# Retail Intelligence Platform — Jour 2

**IPSSI — Mastère Développement, Data & IA**  
**TP2 — UC-03 : Hadoop/HDFS et Data Lake ; UC-04 : ingestion Apache NiFi**  
**Environnement pédagogique réalisé le 17 novembre 2026**

## 1. Objectif et bilan

Ce dossier rassemble les réalisations du socle obligatoire du TP2 : mise en place d'un Data Lake HDFS, dépôt manuel d'un fichier TPCx-BB, ingestion automatisée avec NiFi, vérifications, test d'erreur et traçabilité.

| Élément | Résultat constaté |
|---|---|
| Hadoop / HDFS | Hadoop 3.5.0 ; NameNode actif et un DataNode vivant lors des tests |
| Organisation du Data Lake | Huit répertoires feuilles créés et vérifiés sous `/retail-lake` |
| Dépôt manuel (UC-03) | `reason.dat` dans `/retail-lake/raw/tpcxbb/initial/` |
| Dépôt NiFi (UC-04) | `GetFile → PutHDFS`, vers `/retail-lake/raw/nifi/` |
| Contrôle des dépôts | 3 105 octets chacun ; SHA-256 identique à la source |
| Gestion d'erreur | Dossier d'entrée temporairement inexistant : GetFile `INVALID`, puis `VALID` après correction |
| Provenance | Quatre événements NiFi conservés dans les preuves |
| Livrables | 12 applicables vérifiés, 1 conditionnel sans objet (script de repli) |

**Important :** ces résultats proviennent des exécutions consignées dans `preuves/`. Ils ne signifient pas que les services sont nécessairement encore en cours d'exécution aujourd'hui.

## 2. Organisation du dossier

```text
J2_Retail_Intelligence_Ingestion/
├── documentation/       # Architecture, environnement, inventaire, NiFi, erreurs, provenance, questions de recul
├── ingestion/
│   ├── nifi/            # Export JSON du flux GetFile → PutHDFS
├── installation/
│   ├── compose.yaml     # Définition des services Docker
│   ├── preparer-nifi.ps1
│   └── hadoop/          # Dockerfile, core-site.xml, hdfs-site.xml
├── preuves/
│   ├── captures/        # Captures authentiques Hadoop et NiFi
│   ├── hadoop/          # Versions, initialisation et état des services
│   ├── hdfs/            # Arborescence, dépôt manuel, intégrité
│   ├── nifi/            # Configuration, exécution, erreur et provenance
├── rapport/             # PDF final et, éventuellement, version Word modifiable
├── verification/
│   └── suivi_exigences.md
└── README.md
```

Le document de rendu recommandé est **`DAT_Retail_Intelligence_J2.pdf`**. Le placer dans `rapport/` et vérifier qu'il s'agit bien de la **version complète de 18 pages**, et non de l'ancienne synthèse de 2 pages. Si les fichiers ont été réorganisés ou archivés, adapter les liens et chemins ci-dessous à l'arborescence réelle.

La matrice de correspondance avec les treize livrables du TP se trouve dans [`verification/suivi_exigences.md`](verification/suivi_exigences.md). Les 14 questions de recul figurent dans [`documentation/questions_recul.md`](documentation/questions_recul.md).

## 3. Environnement utilisé

| Composant | Version ou paramètre vérifié |
|---|---|
| Système hôte | Windows 11 Pro ; Docker Desktop 4.84 ; WSL2 |
| Docker Compose | 5.3.1 lors de l'exécution |
| Conteneur HDFS | Ubuntu 24.04.4 ; Hadoop 3.5.0 ; Java 17.0.18 |
| Conteneur NiFi | Debian 12 ; NiFi 2.12.0 ; Java 21.0.12.1 |
| Extensions NiFi | `nifi-hadoop-nar` et `nifi-hadoop-libraries-nar`, version 2.12.0 |
| HDFS | `hdfs://hdfs:9000` sur le réseau Docker Compose ; réplication 1 |
| Interface NameNode | http://localhost:9870 (accès local) |
| Interface NiFi | https://localhost:8443/nifi/ (accès local sécurisé) |

Le projet est **mono-nœud pédagogique** et non un cluster de production. Les ports exposés dans `compose.yaml` sont liés à `127.0.0.1`.

## 4. Démarrer l'environnement existant

Ouvrir PowerShell **dans le dossier racine `J2_Retail_Intelligence_Ingestion`**. S'assurer que Docker Desktop est lancé et que son moteur Linux fonctionne.

```powershell
$c = '.\installation\compose.yaml'
docker info --format '{{.OSType}} {{.ServerVersion}}'
```

La valeur `OSType` doit être `linux`. Vérifier que les fichiers de configuration et extensions requis sont présents. Le script ci-dessous prépare ou contrôle le cache des extensions Hadoop pour NiFi ; il peut télécharger les fichiers manquants et en vérifie les empreintes SHA-256.

```powershell
& .\installation\preparer-nifi.ps1
docker compose -f $c up -d --build hdfs
docker compose -f $c exec -T hdfs jps
```

Si le NameNode et le DataNode ne sont pas déjà actifs, démarrer les démons HDFS dans **le conteneur existant**, sans réinitialiser les volumes :

```powershell
docker compose -f $c exec -T hdfs hdfs --daemon start namenode
docker compose -f $c exec -T hdfs hdfs --daemon start datanode
docker compose -f $c exec -T hdfs jps
docker compose -f $c exec -T hdfs hdfs dfsadmin -report
docker compose -f $c exec -T hdfs hdfs dfsadmin -safemode get
```

Le contrôle attendu pour ce lab est **un DataNode vivant** et un HDFS accessible. Si les démons sont déjà actifs, ne pas les démarrer à nouveau.

Démarrer ensuite NiFi sans recréer volontairement son conteneur :

```powershell
docker compose -f $c up -d --no-recreate nifi
docker compose -f $c exec -T nifi ./bin/nifi.sh status
```

Ouvrir http://localhost:9870 et https://localhost:8443/nifi/. Les identifiants NiFi ne doivent pas être copiés dans le README, les captures ou un dépôt public.

### Avertissement sur les volumes

**Ne pas réexécuter `hdfs namenode -format`.** Le NameNode a déjà été initialisé le 17 novembre 2026 et les volumes Docker contiennent les fichiers du TP. Ne pas lancer `docker compose down -v`, `docker volume rm` ou une opération équivalente. Ne pas recréer NiFi sans avoir sauvegardé le flux, les paramètres utiles et la provenance.

Les volumes HDFS sont ceux du projet Compose `retail-j2` (notamment `retail-j2_namenode` et `retail-j2_datanode`). Leur existence ne garantit pas à elle seule que les services sont démarrés : utiliser les commandes ci-dessus pour vérifier leur état.

## 5. Vérifier les résultats d'UC-03 — HDFS

Les fichiers déjà déposés doivent pouvoir être consultés **sans refaire les dépôts** :

```powershell
docker compose -f $c exec -T hdfs hdfs dfs -ls -R /retail-lake
docker compose -f $c exec -T hdfs hdfs dfs -du -h /retail-lake
docker compose -f $c exec -T hdfs hdfs dfs -df -h /
docker compose -f $c exec -T hdfs hdfs dfs -ls -h /retail-lake/raw/tpcxbb/initial
docker compose -f $c exec -T hdfs hdfs dfs -stat '%n %b octets %a' /retail-lake/raw/tpcxbb/initial/reason.dat
```

Arborescence attendue :

```text
/retail-lake/
├── raw/
│   ├── tpcxbb/
│   │   ├── initial/
│   │   └── refresh/
│   └── nifi/
├── bronze/tpcxbb/
├── silver/
├── gold/
├── quality/
└── logs/
```

Les zones `silver/` et `gold/` ont été préparées pour les journées suivantes, **sans transformation métier exécutée lors du Jour 2**.

Le fichier retenu provient de `data/reason/reason.dat` (lot initial TPCx-BB) : **35 lignes, 3 champs délimités par `|`, 3 105 octets**. Son SHA-256 documenté est :

```text
d5edc45cb1e76afde3b7c0718cdd5d5d45e5f1d720fb940b36db0cd4dcf6b091
```

Pour vérifier l'intégrité des deux dépôts sur les volumes existants sans modifier HDFS :

```powershell
docker compose -f $c exec -T hdfs hdfs dfs -get /retail-lake/raw/tpcxbb/initial/reason.dat /tmp/j2-manuel-relue.dat
docker compose -f $c exec -T hdfs hdfs dfs -get /retail-lake/raw/nifi/reason.dat /tmp/j2-nifi-relue.dat
docker compose -f $c exec -T hdfs sha256sum /tmp/j2-manuel-relue.dat /tmp/j2-nifi-relue.dat
```

Ces commandes ne doivent être relancées que si les noms temporaires ne sont pas déjà utilisés, car `-get` peut refuser une destination locale existante. Si c'est le cas, choisir de nouveaux noms temporaires au lieu d'utiliser une option d'écrasement.

Les preuves détaillées sont dans `preuves/hdfs/` : `P03-arborescence.txt`, `P04-source.txt`, `P05-depot-manuel.txt` et `P06-integrite.txt`.

## 6. Vérifier les résultats d'UC-04 — NiFi

Le flux réellement configuré est :

```text
GetFile --success--> PutHDFS --> /retail-lake/raw/nifi/
                         |
                       failure
                         |
                  file d'erreur visible
```

Paramètres principaux :

| Processeur | Paramètre | Valeur |
|---|---|---|
| GetFile | Input Directory | `/opt/nifi/nifi-current/retail-j2/input` |
| GetFile | Keep Source File | `false` |
| GetFile | Recurse Subdirectories | `false` |
| GetFile | File Filter | `^reason[.]dat$` |
| PutHDFS | Hadoop Configuration Resources | `/etc/retail-j2/hadoop/core-site.xml,/etc/retail-j2/hadoop/hdfs-site.xml` |
| PutHDFS | Directory | `/retail-lake/raw/nifi` |
| PutHDFS | Conflict Resolution Strategy | `fail` |

L'export du groupe est enregistré dans [`ingestion/nifi/UC04-GetFile-PutHDFS.json`](ingestion/nifi/UC04-GetFile-PutHDFS.json). Le premier transfert a été vérifié : **un FlowFile de 3 105 octets**, présence du fichier dans HDFS et empreinte SHA-256 concordante.

**Ne pas redémarrer GetFile pour « tester » le flux sur le même nom de fichier** sans vérifier le dossier d'entrée et la destination. La stratégie `fail` évite l'écrasement silencieux, mais une nouvelle exécution peut créer un échec ou un doublon selon la destination.

Pour contrôler la destination :

```powershell
docker compose -f $c exec -T hdfs hdfs dfs -ls -h /retail-lake/raw/nifi
docker compose -f $c exec -T hdfs hdfs dfs -du -h /retail-lake/raw/nifi
```

L'erreur contrôlée du TP a consisté à sélectionner temporairement un chemin d'entrée inexistant (`INVALID`), puis à rétablir le chemin réel (`VALID`). Les quatre événements de provenance sont archivés dans `preuves/nifi/P12-provenance.json`. La configuration, les captures et les explications sont regroupées dans [`documentation/ingestion_nifi.md`](documentation/ingestion_nifi.md), [`documentation/erreurs_corrections.md`](documentation/erreurs_corrections.md) et [`documentation/provenance.md`](documentation/provenance.md).

Le test terminé, les deux processeurs étaient **valides et arrêtés** ; NiFi restait accessible. Leur état courant doit être revérifié dans l'interface.

## 7. Arrêter proprement les services

Dans l'interface NiFi, **arrêter GetFile puis PutHDFS**, et attendre que les files soient dans l'état souhaité. Ensuite, depuis PowerShell :

```powershell
docker compose -f $c stop nifi
docker compose -f $c exec -T hdfs hdfs --daemon stop datanode
docker compose -f $c exec -T hdfs hdfs --daemon stop namenode
docker compose -f $c stop hdfs
```

**Ne pas supprimer les volumes** après l'arrêt. Le Jour 3 devra pouvoir réutiliser le Data Lake créé aujourd'hui.

## 8. Preuves et limites

- **UC-03** : `preuves/hadoop/`, `preuves/hdfs/`, capture `P02-hdfs-up.png`.
- **UC-04** : `preuves/nifi/`, captures `P08-*` à `P12-*`.
- **Repli local** : `ingestion/scripts/repli_local.py` et `preuves/repli_local/` (si conservés) ; c'était une démonstration intermédiaire, **pas un dépôt HDFS**. Le repli est sans objet pour la validation finale, puisque NiFi a réellement transféré le fichier.
- **Suivi des livrables** : `verification/suivi_exigences.md` (12 vérifiés, 1 conditionnel sans objet).
- **Limites** : environnement mono-nœud, réplication 1, un seul fichier de test ; les zones Silver et Gold n'ont pas encore été alimentées. Ne pas présenter le lab comme un cluster de production.

### Suite du projet

Conserver `installation/`, l'export NiFi, les deux volumes HDFS et les preuves pour le Jour 3. Le traitement et la transformation des données ne font pas partie du socle réalisé au Jour 2.

---
