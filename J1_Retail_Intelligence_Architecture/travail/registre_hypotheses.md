# Registre des hypothèses et points à confirmer

Statuts issus du TP1 §4.2. Les observations renvoient aux preuves exécutées le 16 novembre 2026. Les rôles indiqués sont proposés pour organiser les validations.

| ID | Statut | Sujet | Preuve ou source | Responsable pressenti | Décision de clôture |
| --- | --- | --- | --- | --- | --- |
| H01 | Non disponible | Version, commande du générateur, facteur d’échelle, date de remise et adaptations | Inventaire P01 et absence de manifeste dans la distribution examinée | Formateur | Récupérer métadonnées ou consigner leur absence dans le catalogue |
| H02 | Déduit | Correspondance ordinale avec le DDL Hive | TPC v1.7.0 annexe G, P02, P05 | Équipe Data et formateur | Obtenir DDL/contrat exact et vérifier les écarts |
| H03 | À valider | Append, correction ou autre opération par table et couverture de snapshots | P04, P06, clés de retours et dates chevauchantes | Formateur et équipe Data | Fixer les opérations et identifier une clé d’événement si nécessaire |
| H04 | Non disponible | Devise et règles de clôture | TP1 et champs observés P02, P06 | Finance | Documenter devise, taxes, livraison, clôture et signe des retours |
| H05 | Vérifié | Couples transaction × article répétés et taux de retour non fiable en refresh | P04 et P06 | Commerce, finance et Data | Obtenir clé de ligne d’origine et définir fenêtre de maturité et retours multiples |
| H06 | Non disponible | Identifiants de session fiables et flux stock / mouvements magasin | P01–P03 | Web et logistique | Demander source événementielle ou maintenir les KPI non disponibles |
| H07 | Hypothèse | Dates de fin de version vides assimilables à une borne ouverte | P02 : 18 000 fins produit vides | Data et propriétaire référentiel | Valider sémantique et contrainte temporelle du référentiel |
| H08 | À valider | Compteur audit initial numCompetitors 89 099 pour 89 100 lignes | P01 | Formateur | Expliquer le champ et fixer une règle de rapprochement |
| H09 | Vérifié | Jeu synthétique | TP1 §3.3, fil rouge ch. 3 | Groupe | Utiliser les résultats pour démontrer les traitements |
| H10 | À valider | Plusieurs sites renseignés à l’intérieur d’un en-tête web | P06 | Commerce | Choisir l’attribution au site ou afficher des distincts non additifs |
| H11 | Hypothèse | Hôte Ubuntu pseudo-distribué et prise en charge des offsets stables du fichier | DAT p. 28 et 32 | Data | Mesurer les ressources et tester la reprise sur un lot |
| H12 | À valider | Région, quotas, prix, réseau et identités Azure | DAT p. 35–36 et Microsoft Learn | Responsable Azure | Confirmer les droits, dimensionner et valider le pilote au J4 |
| H13 | À valider | La perte de retour livrée suit le port retour plus deux fois la taxe, avec 77 210 divergences par rapport à la formule TPC | P09, DAT p. 10, TPCx-BB annexe B.2 | Finance et formateur | Garder la mesure descriptive et confirmer le calcul du générateur avant publication métier |
| H14 | À valider | Écart au prix concurrent sensible à la validité de l’offre et à la base de prix | P09, DAT p. 13 | Commerce et formateur | Fixer fenêtre de validité, devise, taxe et unité commerciale comparables |
| H15 | Non disponible | Date de livraison. Plusieurs dates d’expédition peuvent figurer sur une même commande | P09, DAT p. 11 | Logistique | Publier au grain ligne. Définir un délai par commande si ce besoin est confirmé. |
