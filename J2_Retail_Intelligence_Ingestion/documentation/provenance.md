# Provenance NiFi

Le dépôt de provenance de NiFi conserve des événements liés à l’identifiant d’un FlowFile. Le nom de fichier permet de filtrer les résultats. L’UUID permet de distinguer plusieurs tentatives portant le même nom. L’heure, le processeur, l’événement et l’URI de transit reconstituent le parcours. Une preuve de provenance se complète par le listing HDFS et le contrôle de lecture des octets.

## Trace observée le 17 novembre 2026

FlowFile `acc42d0e-ed77-42dd-b81f-c9bf1123277e`, fichier `reason.dat`, **3 105 octets**. NiFi affiche les heures en UTC. À Paris, l’exécution s’est déroulée à 12 h 50.

| ID | Heure UTC | Processeur | Événement | Information de traçabilité |
|---:|---|---|---|---|
| 0 | 11:50:31.769 | GetFile | `RECEIVE` | Lecture de `file:/opt/nifi/nifi-current/retail-j2/input/reason.dat`. |
| 1 | 11:50:32.816 | PutHDFS | `SEND` | Écriture vers `hdfs://hdfs:9000/retail-lake/raw/nifi/reason.dat`. |
| 2 | 11:50:32.827 | PutHDFS | `ATTRIBUTES_MODIFIED` | Les attributs `absolute.hdfs.path` et `hadoop.file.url` renseignent la destination. |
| 3 | 11:50:32.827 | PutHDFS | `DROP` | Fin du FlowFile interne par auto-terminaison de `success`. |

Les quatre événements partagent le même UUID. HDFS a retourné le fichier après le dernier événement et son empreinte correspond à la source. L’export JSON des événements et la définition du groupe sont conservés dans le dossier Jour 2. [Export de provenance](../preuves/nifi/J2-P12-provenance.json) · [Intégrité côté HDFS](../preuves/nifi/J2-P10-depot-nifi.txt) · [Export du groupe](../ingestion/nifi/UC04-GetFile-PutHDFS.json)

[Vue des quatre événements](../preuves/captures/J2-P12-provenance.png) · [Détail de l’événement SEND](../preuves/captures/J2-P12-detail-envoi.png)

## Relever une trace exploitable

1. Ouvrir le groupe UC-04. Clic droit sur **PutHDFS**, puis **View data provenance**. On peut également ouvrir **Data Provenance** depuis le menu principal et rechercher `reason.dat` par **Filename** pour retrouver les événements de GetFile et PutHDFS.
2. Ouvrir le détail de l’événement. Relever l’**Event Id**, l’heure avec son fuseau, le **FlowFile UUID**, le type d’événement, le composant et l’URI de transit. Dans les attributs, vérifier `filename=reason.dat`.
3. Corréler les événements du même UUID et conserver la capture de la liste ou du détail. Pour reproduire l’export de preuve, interroger `POST /nifi-api/provenance`, lire la requête terminée via `GET /nifi-api/provenance/{id}` et lire le détail de chaque événement via `GET /nifi-api/provenance-events/{id}`. Conserver les événements de `reason.dat` pour ce groupe et ses deux processeurs.

Le test doit suivre la copie de travail. Le dépôt manuel de l’UC-03 se trace par les commandes HDFS et le SHA-256, avec son propre chemin de destination.
