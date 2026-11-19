# Organisation ADLS Gen2 et HNS

Proposition uniquement. Conteneur privé : retail-intelligence, compte StorageV2 avec HNS activé.
Exemple d'URI : abfss://retail-intelligence@stretailj4demo2026.dfs.core.windows.net/silver/store_sales/lot=20261118T113628Z-243a5fb5-r3/
Il ne s'agit ni d'un chemin créé ni d'une nouvelle arborescence HDFS.

```text
retail-intelligence/
  bronze/tpcxbb/initial/lot=<lot>/store_sales.dat et item.dat
  silver/store_sales/lot=<lot>/part-*.snappy.parquet
  silver/item/lot=<lot>/part-*.snappy.parquet
  gold/ventes_par_produit/lot=<lot>/part-*.snappy.parquet
  gold/analytics/lot=<lot>/kpi.csv et ventes_par_magasin.csv
  quality/lot=<lot>/controles.json et manifest.json
  documentation/j4/rapport.pdf et dictionnaire_kpi.md
```

| Zone | Données / grain / origine | Conservation proposée | Accès proposés |
| --- | --- | --- | --- |
| Bronze | DAT originaux J3, lignes brutes ; initial séparé du refresh | Pendant le projet puis 90 jours, à valider | Ingestion écrit son dépôt ; ingénieur lit |
| Silver | Parquet Snappy J3 : ligne vente et clé produit | Lot validé et précédent pendant le projet | Ingénieur lit/écrit ; analyste conditionnel |
| Gold | Parquet J3 produit ; CSV agrégés J4 | Lot validé pendant le projet et 90 jours | Ingénieur publie ; analyste/restitution lisent |
| Quality | CSV/JSON, règle de contrôle et manifeste par lot | Un an proposé, sans contenu personnel superflu | Services écrivent leurs traces ; ingénieur contrôle |
| Documentation | MD/PDF/PNG, version de document | Durée du projet et un an proposé | Ingénieur publie ; profils habilités lisent |


Les durées sont des choix pédagogiques à faire approuver par le responsable du futur environnement ; aucune suppression automatique
n'est activée. Toute purge devrait respecter les besoins de preuve et les règles de conservation applicables.
Noms en minuscules ASCII, séparateur underscore pour les tables, lot UTC avec suffixe unique ; le nom original des part Parquet
serait conservé lors d'une copie. Un manifeste relierait source, SHA-256, lot, schéma, compteurs et version de script.
Aucune date commerciale n'est inventée pour partitionner les données ; lot identifie une exécution, pas un jour de vente.

## Hierarchical Namespace

HNS organise de vrais répertoires et permet leur renommage par opération de métadonnées, utile aux publications de traitements.
Un stockage objet plat utilise des préfixes ressemblant à des dossiers, avec d'autres coûts d'opérations.
L'activation HNS ne peut pas être annulée ; les fonctionnalités compatibles doivent être vérifiées avant création ou mise à niveau [A2].
Les accès fins portent sur les chemins : la traversée des ancêtres requiert x ; une lecture/listage de répertoire nécessite r-x [A4].
Le chiffrement au repos relève des capacités Storage, pas d'un effet de la seule convention Bronze/Silver/Gold [A1].
Le driver ABFS et les endpoints dfs sont prévus ; les contraintes réseau doivent couvrir dfs et blob lorsqu'on utilise des endpoints privés [A8].
