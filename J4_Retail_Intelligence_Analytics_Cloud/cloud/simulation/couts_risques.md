# Coûts, quotas et risques - étude uniquement

Aucun coût Azure réel n'a été engagé par le Jour 4. Aucun tarif chiffré actuel n'est inventé.
Le calculateur officiel a été consulté, sans établir de devis ni créer d'abonnement [A9].

| Poste | Unités à estimer | Paramètres / prévention proposés |
| --- | --- | --- |
| Stockage et opérations | Gio-mois, lectures/écritures/listages | Volume de toutes les copies, classe d'accès, redondance et rétention ; éviter les doublons inutiles. |
| Spark | Durée du calcul et ressources instanciées | Taille/nombre de nœuds, démarrage, relances, cache et durée de session ; auto-pause selon disponibilité. |
| Pipelines | Exécutions, activités, déplacement | Fréquence, runtime d'intégration, reprises et volume transféré. |
| SQL | Données traitées en serverless ou capacité dédiée | Projection/filtrage, fréquence des requêtes ; aucun pool dédié nécessaire pour cette étude. |
| Transferts et réseau | Gio sortants, régions, endpoints | Colocaliser les ressources et vérifier les règles tarifaires exactes. |
| Journaux | Volume ingéré, rétention | Conserver les preuves utiles, minimiser les attributs sensibles et fixer une rétention. |
| Persistance | Stockage, disques, réseau ou calcul non arrêté | Inventaire de fin de session ; la fermeture d'un navigateur n'arrête pas un calcul. |

Méthode : établir la volumétrie, le nombre de sessions/requêtes et la durée ; choisir région, monnaie, offres et redondance ;
saisir ces hypothèses dans le calculateur ; enregistrer la date et le devis puis appliquer une marge pour reprises et journaux.
Vérifier quotas de calcul, limites de débit et capacité avant tout essai. Une définition de Spark Pool seule n'instancie pas
nécessairement le calcul : les travaux Spark déclenchent les instances consommées [A7]. Les budgets et alertes complètent la surveillance.
Les principaux risques sont les sessions actives, scans SQL répétés, sorties de données, droits trop larges et secrets diffusés.
Rien de ces garde-fous n'est présenté comme configuré sur Azure dans ce parcours B.
