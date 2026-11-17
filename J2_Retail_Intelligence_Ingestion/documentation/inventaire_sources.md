# Inventaire des sources

Les chemins ci-dessous sont relatifs à `C:\Users\Kevin GREGOIRE\Desktop\Projet`, sauf indication contraire.

| Référence | Chemin vérifié | Utilisation |
|---|---|---|
| TP Jour 2 (31 pages) | `J1_Retail_Intelligence_DAT/TP 2.pdf` | Référence principale, §1, 12, 15–17 et 19 |
| Cours Jour 2 (53 diapositives) | `J1_Retail_Intelligence_DAT/Cours 2.pdf` | HDFS, organisation des zones, ingestion et provenance |
| TP Jour 1 | `01. Architecture DataLake, DataWarehouse, Lakehous/TP1.pdf` | Qualification des sources, architecture Raw/Bronze, Silver et Gold |
| Projet fil rouge | `01. Architecture DataLake, DataWarehouse, Lakehous/projet_fil_rouge.pdf` | §3.1, 4 et 5, origine et architecture cible |
| DAT Jour 1 | `J1_Retail_Intelligence_DAT/DAT_Retail_Intelligence_J1.pdf` et `J1_Retail_Intelligence_DAT/travail/DAT_Retail_Intelligence_J1.md` | Inventaire, clés observées, lots séparés, contrôle d’intégrité |
| Spécification TPCx-BB v1.7.0 | [TPC, spécification officielle](https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPCX-BB_v1.7.0.pdf) | Annexes B et G, référence du modèle |
| README du kit TPCx-BB | `C:\Users\Kevin GREGOIRE\Downloads\5F1AE975-5557-4A17-BBE6-CFCF29E2B3D6-TPCX-BB-Tool\TPCX-BB_Tools_1.7.0\README.md` | Documentation de l’outil de génération, aucune exécution du benchmark |

Les deux supports du Jour 2 ont été lus en intégralité. Le dossier de données est `01. Architecture DataLake, DataWarehouse, Lakehous/retail_project/retail_project`.

| Lot | Domaines observés | Fichiers | Octets |
|---|---:|---:|---:|
| `data/` · initial | 23 | 24 | 1 024 448 074 |
| `data_refresh/` · refresh | 11 | 12 | 9 545 513 |

Chaque lot comprend un CSV d’audit de `item_marketprices` en plus de ses fichiers `.dat`. Le refresh reste identifiable comme lot distinct. La signification d’une fusion avec l’initial dépend des règles métier établies au Jour 1. Le contexte de génération documenté par le cours mentionne le kit 1.7.0. Le lot local est identifié par son chemin et son empreinte. Son journal de génération n’est pas fourni à côté des données.

## Fichier retenu

- Chemin exact `C:\Users\Kevin GREGOIRE\Desktop\Projet\01. Architecture DataLake, DataWarehouse, Lakehous\retail_project\retail_project\data\reason\reason.dat`.
- Lot `data` (initial), référentiel synthétique des motifs de retour. La petite taille permet de relire les données et de comparer les octets. Aucun `reason.dat` relevé dans le refresh.
- Fichier lisible de **3 105 octets**, **35 lignes CRLF**, texte ASCII compatible UTF-8, séparateur `|`, sans en-tête.
- Trois champs reconnus dans le schéma réutilisé du Jour 1, `r_reason_sk` entier, `r_reason_id` identifiant textuel, `r_reason_desc` description textuelle. Les 35 clés numériques sont distinctes. Les trois colonnes sont renseignées sur les 35 lignes. Ce profil décrit l’échantillon fourni.
- SHA-256 `d5edc45cb1e76afde3b7c0718cdd5d5d45e5f1d720fb940b36db0cd4dcf6b091`.
- Aperçu et contrôles reproductibles dans [J2-P04](../preuves/hdfs/J2-P04-source.txt).
