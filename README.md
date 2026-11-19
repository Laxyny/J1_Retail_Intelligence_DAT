# Retail Intelligence Platform

**Projet fil rouge — Mastère Développement, Data & IA · IPSSI**  
**Architecture Data, ingestion, transformations Big Data et analyse décisionnelle**

## Présentation

Retail Intelligence Platform est un projet pédagogique réalisé sur quatre journées de travaux pratiques. Son objectif est de concevoir puis de mettre en œuvre les principales étapes d'une chaîne de traitement de données : qualification des sources, stockage dans un Data Lake, ingestion, transformation, contrôle qualité et restitution d'indicateurs métier.

Le projet repose sur **TPCx-BB**, un jeu de données synthétiques du secteur de la distribution. Il ne représente pas les résultats d'une entreprise réelle et ne constitue pas une exécution officielle du benchmark TPCx-BB.

L'environnement technique utilisé est **local**, principalement sous Windows, Docker/WSL2 et Linux. La déclinaison Microsoft Azure du Jour 4 est **une étude et une simulation documentées**, sans déploiement cloud.

## Organisation du dépôt

| Journée | Périmètre | Réalisations principales | Accès |
| --- | --- | --- | --- |
| **J1 — Architecture** | UC-01 et UC-02 | Analyse métier, inventaire et qualité des sources, dictionnaire de KPI, conception de l'architecture Data Lake | [Jour 1](J1_Retail_Intelligence_Architecture/) |
| **J2 — Ingestion** | UC-03 et UC-04 | Hadoop/HDFS, organisation du Data Lake, dépôt de données, flux NiFi `GetFile → PutHDFS`, traçabilité | [Jour 2](J2_Retail_Intelligence_Ingestion/) |
| **J3 — Transformation** | UC-06 | Traitements PySpark exécutés, deux jeux Silver, un jeu Gold, Parquet Snappy, contrôles qualité | [Jour 3](J3_Retail_Intelligence_Transformation/) |
| **J4 — Analytics & Cloud** | UC-08 et UC-07 | KPI et analyses métier, visualisations, architecture cible Azure / ADLS Gen2, parcours local/open source | [Jour 4](J4_Retail_Intelligence_Analytics_Cloud/) |

### Rapports

- [DAT — Jour 1 : architecture et analyse](J1_Retail_Intelligence_Architecture/DAT_Retail_Intelligence_J1.pdf)
- [DAT — Jour 2 : Hadoop et ingestion NiFi](J2_Retail_Intelligence_Ingestion/rapport/DAT_Retail_Intelligence_J2.pdf)
- [DAT — Jour 3 : PySpark, Silver et Gold](J3_Retail_Intelligence_Transformation/rapport/DAT_Retail_Intelligence_J3.pdf)
- [DAT — Jour 4 : analyse décisionnelle et architecture Azure](J4_Retail_Intelligence_Analytics_Cloud/rapport/DAT_Retail_Intelligence_J4.pdf)

## Chaîne de données réalisée

```text
Sources TPCx-BB
    │
    ├── Jour 1 : qualification des données et conception
    │
    ├── Jour 2 : infrastructure Hadoop/HDFS
    │              + démonstration d'ingestion NiFi sur reason.dat
    │
    └── Jour 3 : chargement de store_sales.dat et item.dat dans HDFS
                   │
                   ▼
              Raw (HDFS)
                   │
                   ▼
              PySpark
           typage, nettoyage,
           jointure et contrôles
                   │
                   ▼
              Silver (Parquet)
            store_sales + item
                   │
                   ▼
              Gold (Parquet)
            ventes_par_produit
                   │
                   ▼
              Jour 4 : KPI, analyses métier,
                       statistiques et graphiques
```

Le flux NiFi du Jour 2 constitue une démonstration d'ingestion distincte : les fichiers de ventes et de produits utilisés au Jour 3 n'ont **pas** été ingérés par ce flux.

## Technologies

| Fonction | Outils |
| --- | --- |
| Conteneurisation et environnement | Docker Desktop, WSL2, Linux, PowerShell |
| Stockage Data Lake | Apache Hadoop / HDFS 3.5.0 |
| Ingestion | Apache NiFi 2.12.0 |
| Traitements et qualité | Python 3.12.3, Apache Spark / PySpark 3.5.7 |
| Formats analytiques | Fichiers DAT, Apache Parquet (Snappy), CSV et JSON de contrôle |
| Analyse et visualisation | Jupyter, Pandas, Matplotlib |
| Architecture cloud étudiée | Azure Data Lake Storage Gen2, HNS, Entra ID, RBAC/ACL, Data Factory et Synapse |

Ces versions correspondent aux environnements documentés pendant les TP ; elles ne constituent pas une matrice de compatibilité universelle.

## Quelques résultats vérifiés

Les résultats analytiques du Jour 4 utilisent les **ventes en magasin du lot initial TPCx-BB**, préparées au Jour 3.

| Indicateur | Résultat |
| --- | ---: |
| Lignes de vente traitées | 667 579 |
| Références produit dans le référentiel utilisé | 17 820 |
| Magasins analysés | 12 |
| Montant net payé avant retours | 1 150 529 586,37 UM |
| Quantités vendues | 33 755 474 unités |
| Transactions magasin distinctes | 89 100 |
| Panier moyen par transaction | 12 912,79 UM |

**UM** signifie *unité monétaire* : la devise des données synthétiques n'est pas établie. Le panier moyen est calculé à partir des transactions qualifiées, **et non du nombre de lignes de vente**. Ces résultats ne sont pas des indicateurs réels de performance commerciale.

Le Jour 4 comprend également des comparaisons par produit, catégorie et magasin, ainsi que trois graphiques disponibles dans [les visualisations](J4_Retail_Intelligence_Analytics_Cloud/analytics/visualisations/).

## Reproduction et preuves

Chaque journée possède sa propre documentation et ses fichiers de contrôle :

- [Instructions Jour 2](J2_Retail_Intelligence_Ingestion/README.md)
- [Instructions Jour 3](J3_Retail_Intelligence_Transformation/README.md)
- [Instructions Jour 4](J4_Retail_Intelligence_Analytics_Cloud/README.md)

Le dossier du Jour 3 contient les **copies exportées des jeux Silver et Gold en Parquet**, leurs manifestes et leurs contrôles d'intégrité. Les scripts et notebooks du Jour 4 s'appuient sur ces données ou sur leur version conservée dans HDFS.

La reproduction intégrale depuis les sources nécessite le **kit TPCx-BB original**, l'environnement adapté et les configurations documentées. Les volumes Docker/HDFS existants ne doivent pas être supprimés ou reformatés pour simplement consulter les résultats. Les rapports et preuves consignent les exécutions réalisées ; une reproduction complète sur un autre ordinateur n'a pas été validée.

## Limites et périmètre

- Données **synthétiques**, périmètre analytique J3/J4 centré sur les ventes magasin initiales ; les fichiers de rafraîchissement ne sont pas fusionnés dans ces analyses.
- HDFS exécuté dans un environnement pédagogique local, avec **un DataNode et un facteur de réplication de 1** : ce n'est pas une infrastructure de production hautement disponible.
- Qualité, granularité et relations entre jeux de données documentées dans les rapports ; certains indicateurs restent hors périmètre lorsque les données nécessaires ne sont pas qualifiées.
- **Aucune ressource Azure déployée ni facturation cloud** : l'UC-07 repose sur le parcours B local/open source et une architecture cible étudiée.
