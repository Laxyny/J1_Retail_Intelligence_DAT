# Suivi des exigences - UC-06

Lot final : 20261118T113628Z-243a5fb5-r3. La section 4.15 comporte dix livrables ; la section 10.2 ajoute explicitement la fiche environnement, soit onze éléments.

## Onze livrables (section 10.2)

| N° | Livrable | Fichiers / sorties | Preuves | Statut |
|---|---|---|---|---|
| 1 | Fiche environnement | configuration/environnement.md | J3-P01, P02 | Réalisé et vérifié |
| 2 | Inventaire technique | documentation/inventaire_sources.md ; configuration/parametres/schemas.json | J3-P03, P04 | Réalisé et vérifié |
| 3 | Notebook d'exploration | notebooks/UC06_exploration.ipynb ; export HTML | J3-P04, P10 | Réalisé et vérifié |
| 4 | Règles de nettoyage | documentation/regles_nettoyage.md | J3-P06 | Réalisé et vérifié |
| 5 | Scripts PySpark | scripts/uc06.py ; exploration/ ; transformation/ ; qualite/ | J3-P02, P04, P06, P10 | Réalisé et vérifié |
| 6 | Données Silver | HDFS lot 20261118T113628Z-243a5fb5-r3 : store_sales et item ; donnees_produites/manifest.json  ; copies Windows : donnees_produites/export/silver/store_sales et silver/item ; donnees_produites/verification_export/manifeste_export.json et controle_export.md | J3-P06, P08, P10  ; J3-P13 | Réalisé et vérifié |
| 7 | Données Gold | HDFS lot 20261118T113628Z-243a5fb5-r3 : ventes_par_produit ; documentation/modele_silver_gold.md  ; copies Windows : donnees_produites/export/gold/ventes_par_produit ; donnees_produites/verification_export/manifeste_export.json et controle_export.md | J3-P07, P10  ; J3-P13 | Réalisé et vérifié |
| 8 | Données Parquet | 3 répertoires HDFS ; preuves/parquet/J3-P08-parquet.json  ; copies Windows : donnees_produites/export/silver/ et gold/ ; donnees_produites/verification_export/manifeste_export.json et controle_export.md | J3-P08, P10  ; J3-P13 | Réalisé et vérifié |
| 9 | Rapport qualité | documentation/rapport_qualite.md ; registre_qualite.csv | J3-P09, P10 | Réalisé et vérifié |
| 10 | README | README.md ; scripts/reproduire.ps1 | J3-P11 | Réalisé et vérifié |
| 11 | Preuves | preuves/index.md ; journaux, JSON et captures authentiques | J3-P01 à P11 | Réalisé et vérifié |

## Dix étapes (section 4)

| Étape TP | Réalisation et fichier | Preuve | Statut |
|---|---|---|---|
| 4.4 Environnement | configuration/environnement.md ; test lecture/transformation/écriture/relecture | P01-P02 | Réalisé et vérifié |
| 4.5 Sources | Deux fichiers initiaux complets ; dictionnaire ordinal vérifié | P03-P04 | Réalisé et vérifié |
| 4.6 Exploration | Notebook exécuté, 5 cellules de code sans erreur | P04, P10 | Réalisé et vérifié |
| 4.7 Nettoyage | Règles préalables et impact mesuré ; 2 575 trims | P06 | Réalisé et vérifié |
| 4.8 Transformations | Typage, normalisation, jointure et agrégation | P05-P07 | Réalisé et vérifié |
| 4.9 Silver | Deux sorties HDFS relues | P06, P08, P10 | Réalisé et vérifié |
| 4.10 Gold | Agrégat produit, 17 820 lignes | P07, P10 | Réalisé et vérifié |
| 4.11 Parquet | 3 écritures/relectures ; comparaison argumentée | P08 | Réalisé et vérifié |
| 4.12 Qualité | 73 contrôles, anomalies et limites | P09-P10 | Réalisé et vérifié |
| 4.13 Organisation | Paramètres, fonctions, scripts, procédure et journaux | P11 | Réalisé et vérifié |

## Tests section 8

| Section | Vérifications réalisées | Preuves | Statut |
|---|---|---|---|
| 8.1 Lecture | Accessibilité, formats, schémas et volumes | P02-P04 | Réalisé et vérifié |
| 8.2 Transformation | Règles écrites, types, exécution, jointure et grain | P05-P07 | Réalisé et vérifié |
| 8.3 Zones | Silver/Gold produits, chemins et provenance | P06-P08, P10 | Réalisé et vérifié |
| 8.4 Parquet | Écriture, lecture, schémas et nombres de lignes | P08, P10 | Réalisé et vérifié |
| 8.5 Qualité | Nulls, doublons, clés, anomalies et limites | P04, P09-P10 | Réalisé et vérifié |

## Questions, rapport et limites

Dix questions traitées dans documentation/questions_recul.md, suivant exactement la section 11. Le DAT Markdown et le PDF réunissent les résultats, sans remplacer les scripts ni les fichiers Parquet HDFS. Les éventuelles captures complémentaires d'oral ne conditionnent pas les onze livrables : les preuves existantes comprennent des captures authentiques et les journaux d'exécution.

La couverture est celle du socle obligatoire uniquement. Les essais interrompus sont documentés et exclus du lot valide. La qualité n'est pas déclarée parfaite. Les fonctionnalités UC-05 et avancées sont exclues à la demande de l'utilisateur, sans être comptées comme des exigences obligatoires non réalisées.

## Finalisation corrective

Les onze livrables restent réalisés et vérifiés. Les trois jeux HDFS du lot final disposent désormais de copies Windows complètes, comparées par SHA-256 et relues avec le vrai Spark. Les tests ciblés de reproduction sont distingués de l’exécution intégrale réelle, qui n’a pas été rejouée. Détails : verification/audit_reproduction.md et donnees_produites/verification_export/controle_export.md. Le dossier A_REMETTRE_J3 contient les fichiers nécessaires à l’évaluation autonome des résultats.
