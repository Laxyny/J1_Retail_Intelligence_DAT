# Questions de recul · TP2 §19

1. **Quel est le rôle du NameNode dans HDFS ?** Il gère l’espace de noms, les permissions et la correspondance entre fichiers, blocs et DataNodes. Le client lui demande où lire ou écrire les blocs.
2. **Quelle différence existe entre un NameNode et un DataNode ?** Le NameNode tient les métadonnées. Le DataNode stocke et sert les blocs, puis signale son état et ses blocs au NameNode.
3. **Pourquoi HDFS découpe-t-il les fichiers en blocs ?** Des morceaux d’un gros fichier peuvent être stockés et lus sur plusieurs nœuds. Le bloc est aussi l’unité de réplication.
4. **Quel est l’intérêt de la réplication ?** Plusieurs copies sur des DataNodes distincts permettent de continuer à lire un bloc après certaines pannes. Avec un seul DataNode et un facteur de 1, cette protection est absente.
5. **Pourquoi organiser un Data Lake en plusieurs zones ?** Chaque zone a un contrat d’usage. Raw préserve la livraison, Bronze organise la réception, Silver fiabilise et Gold publie les données destinées à l’analyse. `quality` et `logs` gardent les résultats de contrôle et les traces techniques.
6. **Pourquoi conserver les données sources dans Raw ?** Les octets reçus servent à vérifier l’intégrité, auditer un traitement ou le rejouer à partir d’un lot identifiable.
7. **Quel est le rôle d’un FlowFile dans NiFi ?** Il représente l’unité transportée. Son contenu correspond ici au fichier `reason.dat` et ses attributs portent par exemple `filename` et son UUID.
8. **Quelle différence existe entre un Processor et une Connection ?** Le processeur réalise une opération. La connexion achemine les FlowFiles d’une relation et les met en file d’attente.
9. **Pourquoi la provenance est-elle importante ?** Elle relie des événements horodatés au même FlowFile. Ici le même UUID relie la lecture de `reason.dat` par GetFile à l’envoi de l’objet dans HDFS par PutHDFS.
10. **Comment distinguer un échec technique d’un rejet métier ?** Un chemin inaccessible empêche l’opération technique. Une ligne lisible dont la clé viole une règle de gestion relève de la validation métier.
11. **Quels risques apparaissent si un flux est relancé sans contrôle des doublons ?** Une relance peut créer plusieurs objets pour le même lot, écraser un résultat ou doubler les données comptées en aval. Une destination protégée et une comparaison lot/empreinte aident à décider d’un rejeu.
12. **Quelles limites présente un environnement mono-nœud ?** NameNode et DataNode dépendent de la même machine. Il ne démontre ni la continuité face à la perte d’un nœud, ni les performances d’un cluster multi-machines.
13. **Pourquoi une copie locale ne constitue-t-elle pas une preuve de dépôt HDFS ?** Une copie locale ne passe pas par le NameNode et le DataNode. Pour les deux dépôts du TP, on a listé les fichiers via HDFS, puis comparé le SHA-256 des copies récupérées par `hdfs dfs -get`.
14. **Quelles informations doivent être conservées pour reproduire une ingestion ?** Versions, configurations non sensibles, chemins source et cible, identifiant du lot, taille et SHA-256, règles de conflit, ordre de lancement, journaux et résultats de vérification.
