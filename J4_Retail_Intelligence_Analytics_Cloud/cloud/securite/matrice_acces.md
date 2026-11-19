# Sécurité et matrice des permissions

Matrice cible seulement, non appliquée à Azure. L = lecture, E = écriture, A = administration temporaire,
C = accès conditionnel et limité à un sous-répertoire/une mission, - = aucun accès.
L'accès du conteneur n'est pas public. Les permissions ci-dessous ne constituent pas une preuve de test Azure.

| Profil | Bronze | Silver | Gold | Quality | Documentation |
| --- | --- | --- | --- | --- | --- |
| Administrateur | A/C | A/C | A/C | A/C | A/C |
| Service ingestion | E/C | - | - | E/C | L/C |
| Data Engineer | L | L/E | L/E | L/E | L/E |
| Analyste métier | - | L/C | L | L/C | L |
| Service restitution | - | - | L/C | - | L/C |

## Traduction technique proposée

L'administrateur gérerait le plan de contrôle via un rôle adapté ; l'administration des données demanderait
une habilitation Storage Blob Data Owner temporaire et auditée. Aucun droit de lecture métier permanent n'est justifié par le seul rôle administratif.
Les profils ordinaires utiliseraient des groupes Entra ou identités managées, et des ACL limitées aux chemins nécessaires.
Un rôle Data Contributor attribué au conteneur entier donnerait trop de droits : une ACL ne peut pas retirer un accès déjà accordé par RBAC [A3].

Pour le service ingestion, C signifie un sous-répertoire d'arrivée neuf et ses propres traces. wx permet de créer des enfants ;
cette permission peut aussi permettre leur suppression. Elle n'est donc pas une garantie append-only. La publication finale devrait
être réalisée par un autre rôle, puis le dépôt rendu non modifiable par l'ingestion. L'analyste peut lire Silver uniquement après
autorisation d'un sous-ensemble utile et minimisé. La restitution lit uniquement les agrégats Gold approuvés.

Les fichiers Gold seraient r-- pour l'analyste, leurs répertoires r-x et les ancêtres --x. Pour l'ingénieur, rw- sur fichiers
et rwx sur les zones de sortie nécessaires, avec masque ACL cohérent. Les ACL par défaut préparent les droits des futurs enfants ;
elles ne corrigent pas rétroactivement les enfants existants. Des tests négatifs doivent contrôler les accès interdits [A4].

## Identité, réseau et secrets

Microsoft Entra ID authentifierait utilisateurs, groupes et applications. Les identités de service seraient distinctes
pour ingestion, calcul et restitution. Privilégier les identités managées, éviter les clés dans scripts/notebooks et utiliser
un coffre de secrets autorisé si un secret est nécessaire. Les accès anonymes et les clés partagées banalisées compromettraient
la séparation prévue. Les rôles de gestion ne doivent pas être confondus avec les rôles d'accès aux données [A3].

Proposition : réseau privé, pare-feu limitant les sources, chiffrement du transport et journalisation des accès refusés.
Les endpoints privés dfs ET blob et la résolution DNS doivent être testés ensemble [A8].
Même avec des données synthétiques, minimiser les attributs client dans les exports et masquer les identifiants personnels
des captures. Avec des données réelles, classification, droits d'accès, rétention et diffusion demanderaient une revue spécifique.

## Mécanismes locaux réellement observés

HDFS utilise hadoop.security.authentication=simple et dfs.permissions.enabled=true. Le répertoire Gold est détenu
par hadoop:supergroup, avec droits rwxr-xr-x ; les fichiers Parquet sont rw-r--r--. Il n'y a pas de Kerberos démontré.
Le calcul s'exécute comme hadoop ; tous les profils de la matrice ne sont donc pas isolés par des identités locales distinctes.
Le RPC reste sur le réseau Docker, le port web NameNode sur 127.0.0.1:9870 ; Spark ne publie aucun port.
Le montage des sources dans Spark est en lecture seule ; le montage /work de J3 est techniquement accessible en écriture,
mais aucun script J4 ne lui écrit et ses fichiers sont comparés par empreintes avant/après.
Cette protection de lab n'est pas l'équivalent d'Entra/RBAC ; aucun test d'intrusion ni validation de sécurité de production n'est revendiqué.
