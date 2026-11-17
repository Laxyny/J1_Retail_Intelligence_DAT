# Fiche d’environnement technique

L’hôte est Windows 11 Professionnel (build 26200). Docker Desktop utilise son moteur Linux sur WSL2. Le projet Compose `retail-j2` isole les conteneurs et le stockage de ce TP. Deux comptes de service Linux exécutent les applications. L’installation Windows de Java n’est pas sollicitée. [Diagnostic initial](../diagnostic_environnement.md)

| Composant | Version observée | Chemin, paramètres et preuve |
|---|---|---|
| Docker Desktop / Engine / Compose | 4.84.0.234817 / 29.6.2 / 5.3.1 | Contexte `desktop-linux`, projet `retail-j2`. |
| Hadoop / Java | Hadoop 3.5.0, Temurin 17.0.18+8 | Ubuntu 24.04.4 LTS, `/opt/hadoop`, utilisateur système `hadoop`. [J2-P01](../preuves/hadoop/J2-P01-versions.txt) |
| Configuration et données HDFS | `hdfs://hdfs:9000`, réplication 1 | XML de référence dans `installation/hadoop`. Volumes `retail-j2_namenode` et `retail-j2_datanode`. NameNode actif et un DataNode actif. [J2-P02](../preuves/hadoop/J2-P02-hdfs-actif.txt) |
| NiFi / Java | Apache NiFi 2.12.0, BellSoft 21.0.12.1+1-LTS | Debian 12, `/opt/nifi/nifi-current`, utilisateur système `nifi`, interface [locale](https://localhost:8443/nifi/). [J2-P07](../preuves/nifi/J2-P07-service.txt) |
| Dépendances NiFi | `nifi-hadoop-nar` et `nifi-hadoop-libraries-nar` 2.12.0 | NAR Apache téléchargés depuis Maven Central, montés en lecture seule. Client Hadoop 3.5.0 dans le NAR de bibliothèques. [Empreintes](../preuves/nifi/J2-P07-nar.txt) |
| Python hôte | 3.13.14 | Profilage, vérifications et automatisation du test. |

## Réseau et accès

- Le RPC NameNode et l’accès aux blocs DataNode passent par le réseau privé Docker. Les processus sur Windows utilisent `docker compose exec` pour appeler le client HDFS dans ce réseau.
- L’interface HDFS est publiée sur `127.0.0.1:9870` et NiFi sur `127.0.0.1:8443`. NiFi utilise HTTPS local, un certificat autosigné et l’authentification mono-utilisateur de l’image. Les identifiants restent dans l’instance locale.
- L’image Hadoop est dérivée de l’image Apache afin que le compte non privilégié `hadoop` possède les deux points de montage dès la création des volumes. Le démarrage d’origine de l’image est remplacé par un processus d’attente. Les démarrages des démons et la première initialisation du volume sont des commandes distinctes.
- Le premier démarrage a été effectué après accord explicite et contrôle de l’exclusivité et de la vacuité des volumes. Le lab possède désormais des métadonnées et des dépôts HDFS. Pour une reprise, le démarrage des démons suffit. [Initialisation](../preuves/hadoop/J2-P02-initialisation-namenode.txt)
- Une cible de production demanderait notamment authentification HDFS, droits distribués, certificats de confiance et plusieurs machines. Le lab utilise la résolution `hdfs` du réseau Compose.

Versions et configuration reproductible dans [le README](../README.md) et [le fichier Compose](../installation/compose.yaml).
