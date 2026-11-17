# NiFi · Découverte et configuration du flux

L’instance Apache NiFi **2.12.0** répond en HTTPS sur [localhost:8443](https://localhost:8443/nifi/). Le compte local autorisé a pu accéder au canvas et à l’API de configuration. Le catalogue a retourné `GetFile` dans `nifi-standard-nar:2.12.0` et `PutHDFS` dans `nifi-hadoop-nar:2.12.0`. La preuve J2-P07 conserve la version, le contrôle du service et les extensions réellement chargées. [Catalogue filtré](../preuves/nifi/J2-P07-processeurs.json)

## Ce que le canvas et les menus permettent de suivre

| Objet | Rôle dans le lab |
|---|---|
| FlowFile | Contenu transporté et attributs. Le nom et l’UUID permettent de retrouver le fichier en provenance. |
| Processor | Une opération. GetFile lit une copie de travail et PutHDFS en écrit les octets dans HDFS. |
| Connection / Queue | La relation relie deux composants et la file peut conserver les FlowFiles en attente. |
| Process Group | Le groupe `UC-04 - Ingestion TPCx-BB` rassemble le flux et sa sortie d’erreur. |
| Controller Service | Configuration ou service partagé, par exemple des identifiants Kerberos dans un autre environnement. Le lab lit les XML Hadoop directement depuis PutHDFS. |
| Provenance Repository | Stocke les événements relatifs aux FlowFiles et fournit leur historique pendant la période de rétention. |

## Flux effectivement configuré

```text
Copie de travail reason.dat
           ↓
        GetFile ── success ──▶ PutHDFS ── écriture ──▶ HDFS /retail-lake/raw/nifi
                                  │
                               failure
                                  ↓
                        File vers port « Echecs a examiner » (arrêté)
```

| Processeur | Propriété | Valeur |
|---|---|---|
| GetFile | Input Directory | `/opt/nifi/nifi-current/retail-j2/input` |
| GetFile | Keep Source File | `false` |
| GetFile | Recurse Subdirectories | `false` |
| GetFile | File Filter | `^reason[.]dat$`, pour limiter le test au fichier prévu |
| PutHDFS | Hadoop Configuration Resources | `/etc/retail-j2/hadoop/core-site.xml,/etc/retail-j2/hadoop/hdfs-site.xml` |
| PutHDFS | Directory | `/retail-lake/raw/nifi` |
| PutHDFS | Conflict Resolution Strategy | `fail` |
| PutHDFS | Relations | `success` terminée automatiquement après écriture. `failure` reliée à une file dédiée. |

Le port de sortie reste arrêté pour conserver les FlowFiles en erreur dans la file. Deux processeurs suffisent pour l’exercice. Le statut de validation `VALID` des deux processeurs correspond à la validation de leur configuration. L’accès à HDFS et le dépôt se contrôlent séparément au moment de l’exécution. [Export du groupe](../ingestion/nifi/UC04-GetFile-PutHDFS.json) · [Configuration et état](../preuves/nifi/J2-P08-configuration.json)

Captures de l’instance locale. [GetFile](../preuves/captures/J2-P08-GetFile.png) · [PutHDFS](../preuves/captures/J2-P08-PutHDFS.png) · [Canvas](../preuves/captures/J2-P09-flux.png)

## Transfert exécuté et contrôlé

Le 17 novembre 2026, la copie de `reason.dat` placée dans le dossier d’entrée a été consommée par GetFile avec `Keep Source File=false`. PutHDFS a reçu un FlowFile de 3 105 octets. La file `success` et la file `failure` étaient vides après le traitement. [Trace de lancement](../preuves/nifi/J2-P10-execution.txt) · [Compteurs NiFi](../preuves/nifi/J2-P10-compteurs.json) · [Capture en exécution](../preuves/captures/J2-P10-execution-nifi.png)

`hdfs dfs -ls`, `-du` et `-stat` ont confirmé `/retail-lake/raw/nifi/reason.dat`, propriétaire `nifi`, mode 644, réplication 1. La copie obtenue par `hdfs dfs -get` est identique à la source. Le dépôt manuel a été relu depuis HDFS après le transfert NiFi et a conservé le même SHA-256. [Dépôt et contrôles](../preuves/nifi/J2-P10-depot-nifi.txt) · [Provenance du transfert](provenance.md)

## Manipulations et prises de preuve dans l’interface

1. Ouvrir NiFi, puis double-cliquer sur le groupe `UC-04 - Ingestion TPCx-BB`. Pour une autre instance vierge, ajouter un **Process Group** et sélectionner le JSON du groupe à importer.
2. Clic droit sur **GetFile** et **PutHDFS**, **Configure**, onglet **Properties**. Vérifier les propriétés du tableau. Les chemins sont ceux du conteneur NiFi.
3. Vérifier la flèche **success** de GetFile vers PutHDFS et la file **failure** vers le port arrêté. Pour examiner cette file, clic droit sur la connexion, **List queue**.
4. Depuis le terminal, vérifier la copie d’entrée et le répertoire HDFS. Dans le canvas, clic droit **Start** sur **PutHDFS**, puis sur **GetFile**.
5. Relever les compteurs **Out** de GetFile, **In** et **Read/Write** de PutHDFS ainsi que l’état des files. Capturer le canvas pendant que les compteurs de la fenêtre récente sont visibles. Contrôler ensuite liste, taille et empreinte de la destination via HDFS.

Pour les captures, conserver les intitulés, propriétés non sensibles, relations et compteurs à l’écran. Exclure la page de connexion et le champ d’identité de la barre d’outils.
