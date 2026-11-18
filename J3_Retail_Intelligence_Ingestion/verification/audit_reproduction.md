# Vérification ciblée de la reproduction - 18 novembre 2026

## Portée

Le pipeline complet n'a pas été relancé. Les six étapes ont déjà été exécutées individuellement lors du Jour 3. Cette vérification distingue analyse statique, tests isolés du pilotage et relectures réelles des données existantes.

## Analyse et corrections ciblées

| Point | Observation et décision | Vérification |
|---|---|---|
| Chemins | Racine déduite de PSScriptRoot ; /work et /sources concordent avec les montages Docker actuels. Ajout d'un contrôle préalable des six scripts et du manifeste | Présence sur disque et docker inspect ; test isolé d'un script manquant |
| Dépendances | Le test initial importait seulement pyspark. Les bibliothèques notebook sont aussi requises | Import réel pyspark, nbclient, nbformat, ipykernel et nbconvert réussi dans le venv |
| Conteneurs | retail-j2-hdfs-1 et retail-j3-spark actifs ; aucun besoin de redémarrage ou de création | docker ps et inspect réels ; NiFi laissé arrêté |
| Ordre | Test Spark, inventaire, nouveau Raw, notebook, transformation, relecture | Six appels observés dans cet ordre avec Docker simulé |
| Paramètres | --sources /sources transmis à l'inventaire ; python et scripts explicitement nommés | Assertions du test de pilotage |
| Erreurs | L'orchestrateur contrôlait déjà le code Docker après chaque étape. Des échecs intermédiaires de préparation HDFS pouvaient être masqués par un import final réussi | Ajout de contrôles de codes dans preparer.ps1 ; arrêt vérifié après un code 7 simulé dans l'étape 3 |
| Identifiant | Nouveau lot dans preparer_entrees.py : UTC + huit caractères UUID. Ancien identifiant désormais validé avant construction du chemin d'archive | Analyse du code ; test d'un identifiant ../hors_projet refusé avant appel Docker |
| Archives | Copie des contrôles, journaux, notebook et paramètres déjà prévue ; manifeste des résultats oublié | Ajout de manifest.json ; hash de la copie vérifié dans une fixture isolée |
| Résultats présents | Archive existante refusée ; errorifexists pour Silver/Gold ; -put sans -f pour Raw | Refus d'archive rejoué sur fixture ; preuve réelle initiale J3-P12 du refus du même lot conservée |
| README | Ancienne mention d'absence de copie Silver devenue obsolète | Mise à jour avec chemins d'export, lecture locale et limites exactes |

## Tests exécutés pendant la correction

- Cinq scénarios de pilotage ont réussi dans une arborescence de test distincte : ordre/paramètres/archives/journaux ; arrêt sur erreur ; archive existante préservée ; identifiant invalide refusé ; script absent refusé.
- Les appels Docker de ces scénarios sont **simulés**. Le journal de test l'indique explicitement. Les fichiers de fixture ne sont pas des données TPCx-BB et ne figurent pas parmi les résultats métier.
- Les deux scripts PowerShell modifiés ont passé l'analyse syntaxique. Les chemins et dépendances ont été inspectés sur l'environnement réel. Les modifications des branches d'erreur de preparer.ps1 n'ont pas été exercées sur les démons réels, afin de ne pas arrêter ni dérégler HDFS.
- Le vrai Spark a relu les copies locales des trois jeux, vérifié leurs schémas, comptages et totaux. Cette opération ne rejoue pas le pipeline.

Résultats détaillés : correction_20261118/test-orchestrateur.log et correction_20261118/tests-*/resultats.json. Les copies originales des fichiers modifiés sont conservées sous correction_20261118/originaux.

## Statut final

Analyse statique : effectuée. Tests isolés du pilotage : cinq réussites. Dépendances et montages réels : vérifiés. Relecture réelle des données locales : réussie. Exécution intégrale réelle de reproduire.ps1 : **non effectuée et non revendiquée**. Aucune nouvelle entrée Raw ni nouvelle sortie Silver/Gold n'a été produite.
