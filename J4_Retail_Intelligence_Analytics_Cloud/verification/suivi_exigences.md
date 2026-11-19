# Suivi des exigences - TP4 §13.1

Les onze intitulés ci-dessous sont ceux du TP4. J4-10 « Preuves Azure » est satisfait par la simulation admise au §9.2.

| Code | Livrable / exigence | Fichiers | Preuves | Vérification réalisée | Statut / limite |
| --- | --- | --- | --- | --- | --- |
| J4-01 | Inventaire analytique | documentation/inventaire_analytique.md ; documentation/schemas.md ; preuves/analyses/inventaire.json | J4-P02 | Schémas, grain, volumes et provenance relus | Vérifié ; Données synthétiques, lot J3 externe pour recalcul |
| J4-02 | Dictionnaire des KPI | documentation/dictionnaire_kpi.md ; analytics/outputs/kpi.csv ; analytics/outputs/transactions.json ; preuves/analyses/qualification_transactions.json | J4-P03 / J4-P17 | K01 à K04 qualifiés ; J4-L01 secondaire conservé | Vérifié ; Données synthétiques, lot J3 externe pour recalcul |
| J4-03 | Analyses statistiques | documentation/statistiques.md ; analytics/outputs/statistiques.csv ; analytics/outputs/qualite.json | J4-P04 | Cinq profils, couverture, sommes et médianes | Vérifié ; Données synthétiques, lot J3 externe pour recalcul |
| J4-04 | Analyses métier | documentation/analyses_metier.md ; analytics/outputs/top10_produits.csv ; analytics/outputs/ventes_par_magasin.csv ; analytics/outputs/ventes_par_categorie.csv | J4-P05 / J4-P18 | Produits et magasins conservés ; catégories ajoutées | Vérifié ; Données synthétiques, lot J3 externe pour recalcul |
| J4-05 | Visualisations | analytics/visualisations/top10_produits.png ; analytics/visualisations/ventes_par_magasin.png ; analytics/visualisations/ventes_par_categorie.png | J4-P06 / J4-P18 | Trois PNG lisibles, données de tracé contrôlées | Vérifié ; Données synthétiques, lot J3 externe pour recalcul |
| J4-06 | Synthèse décisionnelle | documentation/synthese_decisionnelle.md | J4-P07 | Deux constats avec limites et recommandations | Vérifié ; Données synthétiques, lot J3 externe pour recalcul |
| J4-07 | Architecture Azure | cloud/architecture/architecture_azure.md ; cloud/architecture/architecture_azure.png ; cloud/architecture/architecture_locale.png ; cloud/architecture/comparaison_services.md | J4-P10 | Cible et local distincts ; responsabilités et composants comparés | Vérifié ; Documentaire : aucun Azure déployé |
| J4-08 | Organisation ADLS Gen2 | cloud/adls_gen2/organisation.md | J4-P11 | Zones, chemins, HNS, conservation et traçabilité | Vérifié ; Documentaire : aucun Azure déployé |
| J4-09 | Sécurité | cloud/securite/matrice_acces.md | J4-P12 | Cinq profils, cinq zones, RBAC/ACL et limites locales | Vérifié ; Documentaire : aucun Azure déployé |
| J4-10 | Preuves Azure | cloud/simulation/scenario_non_execute.md ; cloud/simulation/couts_risques.md ; preuves/architecture/azure_ineligibilite_recadree.png | J4-P09 / J4-P13 | Simulation documentée autorisée en parcours B ; preuve de refus réelle | Vérifié ; Documentaire : aucun Azure déployé |
| J4-11 | README J4 | README.md | J4-P14 | Prérequis, paramètres, reproduction, arrêt et limites | Vérifié ; Données synthétiques, lot J3 externe pour recalcul |

Contrôle indépendant V2 : 73 vérifications réussies, plus les 45 contrôles Spark réexécutés. La validation documentaire ne revendique aucune exécution Azure.
Les PNG, pages PDF et HTML du notebook font également l’objet d’une inspection visuelle consignée dans verification/revue_visuelle.md.
