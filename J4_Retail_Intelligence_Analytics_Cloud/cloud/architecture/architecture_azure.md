# Architecture Azure proposée

Architecture proposée - Aucun service Azure déployé.

Le parcours B est définitif. La capture utilisateur du 19 novembre 2026 montre l'inéligibilité à l'offre gratuite
et propose uniquement le paiement à l'utilisation. Aucun abonnement payant, carte bancaire, compte de contournement
ou ressource Azure n'a été créé. Aucun coût Azure réel n'a été engagé par les travaux J4.
Le socle TP4 §9.2 autorise cette étude et la démonstration locale sans installer l'ensemble du Lakehouse.

## Ressources et responsabilités

Un abonnement porterait la facturation et les quotas. Le groupe de ressources rg-retail-j4-etude rassemblerait
le stockage et les éventuels services associés. Un compte StorageV2, nommé ici stretailj4demo2026 à titre indicatif,
contiendrait le conteneur privé retail-intelligence. Ce nom n'a pas été réservé ni sa disponibilité vérifiée.
ADLS Gen2 désigne les capacités Data Lake de Blob Storage obtenues avec HNS, pas un second disque à créer [A1].
Les arborescences Bronze/Silver/Gold assureraient la continuité avec les zones HDFS déjà employées.

Azure Data Factory serait envisagé pour copier et orchestrer les arrivées des fichiers. Pour une source Windows
privée, il faudrait prévoir une connectivité autorisée ou un runtime d'intégration adapté. Les sources synthétiques
et les données complémentaires éventuelles seraient distinguées. Aucune donnée complémentaire n'est utilisée ici [A5].

Synapse Analytics proposerait un workspace analytique. Synapse Studio servirait d'interface aux notebooks,
pipelines et requêtes. Un Spark Pool définirait le calcul managé ; les transformations PySpark utiliseraient
des chemins abfss et une identité autorisée au lieu de l'adresse HDFS locale. Les capacités SQL serverless
permettraient d'explorer des fichiers ; un pool SQL dédié réserverait des ressources et répondrait à un autre
besoin de charge. Les formats compatibles et autorisations devraient être vérifiés avant leur utilisation [A6, A7].

Les choix restent hypothétiques : aucune version du runtime Synapse n'est présumée identique à Spark 3.5.7.
Il faudrait tester les bibliothèques et les résultats après migration. ADF ne remplace pas le stockage ;
Spark calcule ; ADLS conserve les données. Les exports CSV et notebooks pourraient restituer les petits résultats.

## Architecture locale démontrée

Les sources du kit ont été copiées en Raw HDFS au J3, puis transformées par PySpark en Parquet Silver/Gold.
J4 relit ces trois jeux par HDFS RPC et produit des agrégats dans son espace distinct. Matplotlib et le notebook
restituent ces résultats. Le stockage est dans les volumes Docker existants ; Spark local[2] s'exécute dans WSL2.
NiFi apparaît uniquement dans l'historique J2 GetFile vers PutHDFS de reason.dat. Il n'a pas ingéré les faits J3.
Ni Azure, ni MinIO, Iceberg, Trino, Airflow ou Superset ne sont déployés dans cette réalisation.
