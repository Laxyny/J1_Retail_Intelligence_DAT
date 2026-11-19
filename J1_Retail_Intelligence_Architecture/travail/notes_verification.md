# Notes de vérification · 16 novembre 2026

## Références examinées

- **TP1.pdf**. Scénario, statuts de certitude, UC-01 et UC-02, critères d’évaluation, liste §8.1 p. 22. Le TP1 guide la couverture. La remise a été consolidée selon le brief.
- **projet_fil_rouge.pdf**. Chapitres 1–6 et 8. Le DAT prépare le stockage et l’ingestion, la transformation et la déclinaison Azure par étapes.
- **Cours 1 .pdf**. Diapositives 9–35 et 39–52. BI, grain, qualité, ELT, zones, Parquet et positionnement des composants.
- **TPCx-BB 1.7.0**. Annexe B pour l’interprétation et annexe G pour l’ordre physique de lecture. La version du générateur local reste inconnue. L’empreinte du PDF de référence est dans `00_schema_execution.json`.

## Exécutions locales

| Preuve | Commande équivalente depuis la racine du DAT | Horodatage / statut conservé | Portée |
| --- | --- | --- | --- |
| P01–P03 · ordres DDL | `python -B preuves/scripts/schema_tpc.py` | `00_schema_execution.json`, succès | 23 listes de colonnes extraites et pages associées |
| P01–P03 · profil | `python -B preuves/scripts/profiler.py` | `01_profil.json` et `01_execution.log`, succès | 36 fichiers ; lecture physique exhaustive, typage général et doublons échantillonnés |
| P04–P06 · relationnel | `python -B preuves/scripts/relations.py` | `03_execution.json` et `03_execution.log`, succès | 42 clés candidates et 142 relations par lot, mesures et rapprochements exhaustifs sélectionnés |
| P01–P06 · commandes de capture | `.\preuves\scripts\Afficher-Preuve.ps1 -Id P01` à P06 | `09_affichage_preuves.log`, succès | Données agrégées ou masquées, sorties textuelles |
| Remise | `python -B preuves/scripts/verifier_livrables.py` | `08_verification_finale.json` | Empreintes source, nombre de pages, figures, annexes et résultats critiques |

## Contrôles prioritaires

Le couple transaction–produit n’est pas unique. Le contrôle exhaustif trouve zéro ligne strictement identique au-delà de la première dans chaque fichier de vente ou de retour. Dans les clics, le contrôle d’échantillon trouve une répétition exacte dans le refresh, et la règle d’identité d’un événement est inconnue.

Les 142 comparaisons de références rendent zéro orphelin sur les champs valides une fois les référentiels livrés réunis. La comparaison au seul initial remonte 232 380 références produit du stock initial à résoudre. Les nullités restent visibles. L’échec de couverture des retours rafraîchis concerne un autre contrôle, à savoir le lien métier vers une vente candidate.

Les occurrences de quantités de stock vides sont comptées indépendamment des zéros. Pour les ventes, les sommes de contrôle utilisent des nombres décimaux. Les types généraux ont été inspectés sur un échantillon de tête. Les chiffres de ventes et retours sont des observations de données synthétiques.

## Relecture des livrables

Le PDF est rendu en A4. Ses 35 pages ont été inspectées en planches, avec lecture agrandie de la couverture, des tableaux de définition et des figures remaniées. Les 15 onglets ont été exportés avec des tables filtrables, des en-têtes figés et des nombres typés, puis contrôlés après réouverture avec openpyxl. Les résultats ne nécessitent pas de recalcul Excel.

Les commandes PowerShell P01 à P06 ont été testées. Les PNG P07–P08 proviennent des exports des schémas d’architecture.

## Version 1.1 · Audit et recalcul P09

Le script `preuves/scripts/auditer_kpi.py` a été exécuté sur les deux lots. Il a relu 23 fichiers et vérifié leurs empreintes de référence. Les mesures monétaires ont été lues en centimes. Les 87 lignes de résultats gardent le périmètre, le numérateur et le dénominateur des ratios. Le typage des 86 champs mesurés et les 1 180 contrôles sont exportés séparément. Le journal et le JSON d’exécution conservent l’horodatage, la durée et la commande.

- **Ventes.** Les identités de net payé, taxes, remises et résultat du kit se réconcilient sans écart sur les quatre fichiers. Les montants négatifs de résultat sont conservés.
- **Retours.** 77 210 lignes divergent de la formule de perte publiée dans l’annexe B.2. Les 77 215 lignes vérifient la relation « port retour + deux fois la taxe ». K16 restitue la somme du champ livré à titre descriptif. L’usage métier attend la validation de la formule. K12 reste suspendu.
- **Logistique.** Le 12 décembre 2005, les deux lots de stock contiennent des triplets disjoints. La simulation couvre 90 000 triplets, avec 89 975 quantités connues et 100 zéros. Les délais web ont été calculés à la ligne et la multiplicité des dates d’expédition a été contrôlée.
- **Prix concurrents.** La comparaison à la médiane sur 3 924 produits est conservée comme diagnostic. La couverture des offres varie selon la convention de fin de validité.

Les 38 pages du PDF ont été rendues pour contrôle visuel. Le sommaire, la grille TP1, les sept figures et les montants de la version actualisée ont été vérifiés. Le classeur KPI contient les décisions pour K01–K12, les définitions révisées, les choix de jointure, les 16 questions et les résultats P09. Le classeur d’architecture a été réexporté pour corriger le renvoi de page.

## Version 1.2 · Intégration des captures

Les PNG fournis ont été relus et rapprochés des sorties P01 à P06 déjà enregistrées. Les valeurs des clés, des relations et des contrôles de retours ont été comparées aux extraits du classeur de qualification. En P04, `repetitions` désigne l’écart entre lignes à clé valide et clés distinctes. En P06, deux des 29 retours web avec une vente candidate ont plusieurs correspondances. Les trois statuts sensibles du dictionnaire ont été vérifiés à la réouverture.

Les captures occupent les pages 39 à 44. Les pages P01, P03, P04 et P05 sont en paysage. P02 et P06 sont en portrait. Le contrôle final documente les empreintes, l’égalité des pixels avec les PNG, le respect du cadrage et les liens internes. Les écarts techniques déjà consignés dans le registre restent applicables.
