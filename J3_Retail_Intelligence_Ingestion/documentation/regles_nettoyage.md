# Règles de nettoyage UC-06

Règles définies après exploration et avant lancement du traitement Silver/Gold. Périmètre : fichiers initiaux complets store_sales et item. Les résultats d'application sont enregistrés dans J3-P06-transformation.json.

| ID | Champs / constat et contrôle exhaustif | Décision et transformation | Justification et limite |
|---|---|---|---|
| R01 | Tous : ordre physique, 23 champs vente et 22 produit, sans en-tête | Schéma Annexe G, lecture de chaînes puis try_cast contrôlé. Arrêt si conversion non nulle impossible | Ne pas perdre silencieusement une valeur. Le manifeste du générateur local n'est pas livré |
| R02 | Montants : decimal(7,2), contrôles prix × quantité et net + taxe | Conserver les décimaux, SUM élargit la précision ; aucune conversion en flottant | Éviter les erreurs d'arrondi et le double comptage. Devise inconnue |
| R03 | ss_item_sk / i_item_sk, ticket, quantité et net payé : présence et domaine | Isoler les identifiants négatifs ou nuls et les mesures nécessaires nulles ; sauvegarder tout rejet avec motif | Zéro est une clé réelle du kit ; ne pas l'invalider. Une mesure signée n'est pas un rejet |
| R04 | Dates produit : chaînes ISO, contrôles try_cast et ordre début/fin | Convertir en date ; conserver les fins nulles ; arrêter si date non vide invalide ou fin antérieure au début | Aucune date de fin inventée. Les *_date_sk de vente restent des références numériques |
| R05 | Textes produit : comparaison valeur / trim | Retirer seulement les espaces périphériques ; compter les lignes modifiées | Ne pas modifier la casse, les libellés internes ou les catégories sans règle métier |
| R06 | Nulls facultatifs ventes et produits, y compris fins produit absentes | Conserver NULL ; aucune imputation | Absence ne signifie pas zéro. Les taux sont mesurés par colonne |
| R07 | Ventes : 0 doublon exact, 4 136 répétitions au-delà du premier couple ticket-produit | Conserver toutes les lignes ; aucune déduplication | Le couple candidat n'identifie pas une ligne unique. Aucune clé de ligne native démontrée |
| R08 | 495 971 lignes avec résultat financier négatif | Conserver les valeurs signées, mesurer leur nombre | La négativité ne prouve pas une erreur. Ne pas transformer le résultat du kit en rentabilité réelle |
| R09 | Dimension : unicité i_item_sk ; ventes : références sans correspondance | Vérifier avant jointure ; arrêt si clé produit dupliquée ; jointure gauche, conserver les non rapprochés et mesurer | Empêcher la multiplication des ventes ; pas de rapprochement sur un libellé |
| R10 | Lots initial / refresh distincts | Ne traiter que l'initial ; conserver l'inventaire du refresh séparément | L'initial couvre toutes les références de vente retenues. Aucune sémantique de fusion supposée |

Les conversions de représentation ne sont pas présentées comme des corrections métier. Le bilan distingue lignes acceptées, lignes dont un texte est corrigé et lignes mises à l'écart. Une anomalie nouvelle bloquante laisse les sources intactes et ne produit aucun résultat déclaré valide.
