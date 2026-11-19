# Registre des preuves J4

| Identifiant | Description | Fichier(s) | Exigence TP4 | Statut |
| --- | --- | --- | --- | --- |
| J4-P01 | Versions, session et environnement existant | preuves/environnement/environnement.json ; requirements.lock.txt ; java.txt ; docker.txt | §1, §12.1 | Exécuté et contrôlé |
| J4-P02 | Lecture HDFS, schémas, volumes et fichiers | preuves/analyses/inventaire.json ; documentation/schemas.md | J4-01 | Exécuté et contrôlé |
| J4-P03 | Quatre KPI métier et volume technique secondaire | analytics/outputs/kpi.csv ; preuves/analyses/controles.csv | J4-02 | Exécuté et contrôlé en V2 |
| J4-P04 | Statistiques et absences | analytics/outputs/statistiques.csv ; qualite.json | J4-03 | Exécuté et contrôlé |
| J4-P05 | Agrégats produit et magasin | analytics/outputs/contributions_produits.csv ; ventes_par_magasin.csv | J4-04 | Exécuté et contrôlé |
| J4-P06 | Trois figures issues des petits agrégats | analytics/visualisations/*.png ; CSV associés | J4-05 | Exécuté et contrôlé en V2 |
| J4-P07 | Constats, recommandations et limites | documentation/synthese_decisionnelle.md | J4-06 | Étudié et contrôlé |
| J4-P08 | Notebook intégralement exécuté et export lisible | analytics/notebooks/TP4_Retail_Intelligence.ipynb ; .html ; preuves/analyses_execution.log | §9.1.4, §12.1 | Exécuté et contrôlé |
| J4-P09 | Refus Azure authentique recadré sans identifiants | preuves/architecture/azure_ineligibilite_recadree.png ; provenance_capture.md | Parcours B, J4-10 | Contrôlé |
| J4-P10 | Architectures réelle et cible, correspondance | cloud/architecture/*.svg, *.png et fichiers MD | J4-07 | Local démontré ; cible étudiée |
| J4-P11 | Organisation logique ADLS et HNS | cloud/adls_gen2/organisation.md | J4-08 | Étudié et contrôlé |
| J4-P12 | Matrice cible et mécanismes locaux observés | cloud/securite/matrice_acces.md ; preuves/environnement/hdfs_*.txt | J4-09 | Cible étudiée ; local observé |
| J4-P13 | Scénario Azure et postes de coûts | cloud/simulation/*.md | J4-10 | Simulé documentairement, non exécuté |
| J4-P14 | Reproduction et arrêt conservant les volumes | README.md | J4-11 | Contrôlé ; autre poste non testé |
| J4-P15 | Réconciliations et validation indépendante | preuves/analyses/validation.json ; verification/controle_final.json | §12 | Exécuté et contrôlé |
| J4-P16 | Préservation antérieure et intégrité de remise | preuves/environnement/protection_*.json ; hdfs_*.txt ; MANIFESTE_REMISE.json dans la remise ; verification/integrite_archive.json hors ZIP | Contraintes de conservation / remise | Contrôlé après constitution de la remise |
| J4-P17 | Qualification des tickets et calcul des paniers | preuves/analyses/qualification_transactions.json ; analytics/outputs/transactions.json ; repartition_lignes_par_ticket.csv ; preuves/provenance/J1_*.csv | K03 / K04 | Exécuté et contrôlé en V2 |
| J4-P18 | Contribution des neuf catégories | analytics/outputs/ventes_par_categorie.csv ; categories.json ; analytics/visualisations/ventes_par_categorie.png | J4-04 / J4-05 | Exécuté et contrôlé en V2 |
| J4-P19 | Sauvegarde et journal correctif | verification/correction_v2/sauvegarde.json ; journal_changements.md ; preservation.json | Protection et traçabilité | Contrôlé en V2 |

Les schémas sont des dessins documentaires, les graphiques des résultats Matplotlib et la seule capture Azure est celle de l'utilisateur.
Les journaux ne sont pas transformés en fausses captures de terminal. Les preuves Azure simulées ne prouvent aucun accès ni déploiement.
