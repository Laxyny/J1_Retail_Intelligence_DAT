# Simulation documentaire Azure - non exécutée

Toutes les étapes ci-dessous sont un scénario conditionnel pour un futur environnement autorisé.
Aucun appel Azure, aucune ressource, aucune facture ni pipeline ne résulte de ce dossier.

| Étape proposée | Ressource / action non exécutée | Contrôle à réaliser après autorisation |
| --- | --- | --- |
| 1. Cadrer | Abonnement autorisé, région proche des usages, quotas, groupe rg-retail-j4-etude | Vérifier habilitations, conformité de la région et plafond d'exposition financière. |
| 2. Préparer le stockage | Compte StorageV2 stretailj4demo2026 indicatif, HNS activé, conteneur privé retail-intelligence | Contrôler disponibilité du nom, HNS, accès anonyme désactivé et capacités compatibles. |
| 3. Préparer les chemins | Zones et lots décrits dans organisation.md | Lister zones, vérifier conventions et absence de collision de lots. |
| 4. Préparer les identités | Groupes Entra ; identités managées ingestion, calcul, restitution ; ACL et portées RBAC | Tester lecture, écriture et refus avec chaque identité ; vérifier ancêtres et masque. |
| 5. Déposer une preuve | Dépôt du seul kpi.csv agrégé J4, via Storage Explorer ou AzCopy avec identité Entra | Taille, SHA-256 après téléchargement, en-tête, lignes, présence et lecture ; ne pas confondre ETag et SHA-256. |
| 6. Déplacer les données du projet | Après accord, copies J3 Parquet vers Silver/Gold, DAT autorisés en Bronze ; ADF facultatif | Manifeste fichier par fichier et identifiant 20261118T113628Z-243a5fb5-r3 ; ne pas agréger plusieurs lots. |
| 7. Transformer si nécessaire | Notebook PySpark adapté aux URI abfss, Spark Pool Synapse facultatif | Tester types Decimal, dépendances, nombre de lignes et concordance des montants avec les références locales. |
| 8. Explorer / restituer | Synapse Studio ; requêtes SQL sur Gold ou exports agrégés | Vérifier types, grain, permissions et résultats ; confirmer le format supporté par le mode SQL choisi. |
| 9. Exploiter | Suivi des erreurs, journaux, budgets et alertes ; pause/arrêt du calcul selon le service | Vérifier consommation, ressources persistantes et restauration. Un budget est une alerte, pas une garantie d'arrêt de la facture. |

La première preuve de dépôt serait volontairement minime : kpi.csv ne contient que des agrégats et aucune donnée client.
Un lot complet demanderait un manifeste associant chaque fichier, sa provenance, son schéma et ses empreintes.
On conserverait les trois mesures : 667 579 lignes, 33 755 474 unités, 1 150 529 586,37 UM.
Ces valeurs sont des critères attendus pour le même périmètre, pas une preuve d'exécution Azure.

## Limites de la simulation

Noms, région, rétention et habilitations sont proposés. Aucune disponibilité de ressource, de quota, de réseau ni de rôle n'est validée.
Une matrice documentaire ne prouve pas l'efficacité des accès. Aucune comparaison de performance ou de coût observé Azure/local n'est possible.
Le document n'est pas un script de déploiement et ne doit pas être présenté comme un export du portail.
