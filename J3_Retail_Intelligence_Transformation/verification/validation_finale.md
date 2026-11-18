# Validation finale du rendu UC-06

18 novembre 2026 - Europe/Paris.

- Spark 3.5.7 a chargé un fichier HDFS, affiché son schéma, appliqué trim, écrit et relu un Parquet de 35 lignes. Le test a été relancé avec le code final.
- Les deux sources initiales complètes sont traitées. Le notebook final possède cinq cellules code exécutées et aucune sortie de type error. Son export HTML a été ouvert et inspecté dans un navigateur ; les aperçus de données restent limités à quelques colonnes lisibles.
- Les deux Silver et le Gold ont été écrits et relus. Trois comparaisons de noms/types, volumes et empreintes agrégées sont concluantes. Les 17 820 produits Gold se réconcilient avec le calcul Python indépendant.
- Le registre contient 73 contrôles : 64 OK, 8 observations de valeurs nulles, 1 anomalie documentée de clé candidate non unique ; zéro échec bloquant. Les trois jeux ont été relus une nouvelle fois par verifier.py.
- La relance du pipeline sur le même lot a réellement échoué avant écriture avec « Lot déjà présent », code 1 attendu. Le journal J3-P12 en conserve la preuve.
- Le script PowerShell preparer.ps1 a été exécuté avec succès dans l'environnement final. Les deux scripts PowerShell ont passé l'analyse syntaxique ; installer-python.sh a passé bash -n. Le wrapper reproduire.ps1 n'a pas été relancé intégralement pour éviter de recréer inutilement un deuxième lot complet ; chacune de ses étapes de traitement a été exécutée séparément. Son mécanisme d'archivage reste à exercer lors d'une future reproduction.
- Le PDF final comporte 17 pages. Toutes les pages ont été rendues par PDFium et examinées sur deux planches ; les pages de règles et de preuves ont aussi été contrôlées en pleine taille. Les accents, tableaux, marges, numéros de page et trois captures sont lisibles. Aucun texte de template ou caractère d'encodage incorrect n'est détecté.
- Les 158 fichiers de contenu existants (sources, pédagogie et livrables) sont inchangés par SHA-256. Le manifeste initial recense aussi 173 métadonnées Git ; seule une entrée de journal interne origin/HEAD a évolué pendant la session. Cette évolution est signalée séparément et n'a pas été annulée.
- Les deux dépôts reason.dat J2 ont toujours leur empreinte d'origine. L'état HDFS final indique un DataNode vivant, zéro bloc manquant, zéro bloc corrompu et zéro bloc sous-répliqué ; le mode sûr est désactivé.
- Les trois captures sont authentiques, enregistrées directement depuis le navigateur. Aucune capture manuelle indispensable n'est en attente. Le petit serveur HTTP local utilisé pour inspecter le notebook a été arrêté. HDFS et le conteneur Spark restent disponibles ; NiFi est resté arrêté.

Le registre suivi_exigences.md valide les onze livrables du socle obligatoire. Les limites d'interprétation et l'incident exceptAll restent exposés dans les documents, sans faire passer les essais interrompus pour des sorties valides.
