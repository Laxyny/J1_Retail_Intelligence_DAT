# Contrôle de l'export Parquet

Lot final : 20261118T113628Z-243a5fb5-r3. Export des sorties existantes uniquement ; aucune transformation rejouée. Publication du dossier export après validation du staging.

| Jeu | Parquet | Tous fichiers | Octets | Lignes Spark locales | Intégrité |
|---|---|---|---|---|---|
| silver_store_sales | 2 | 3 | 34766704 | 667579 | OK |
| silver_item | 2 | 3 | 3571219 | 17820 | OK |
| gold_ventes_par_produit | 2 | 3 | 1307151 | 17820 | OK |

Total : six fichiers Parquet et trois marqueurs _SUCCESS, 39 645 074 octets. Les neuf noms, tailles et SHA-256 sont identiques entre HDFS et Windows. Les schémas complets relus correspondent exactement à schema_after du manifeste original. Les trois jeux portent le même _run_id final.

Contrôle métier de la copie Silver ventes et de Gold : quantité 33 755 474, net payé 1 150 529 586,37 UM. SUM(sales_line_count) Gold = 667 579. Une seconde relecture autonome a réellement utilisé file:/// avec Spark, sans dépendance à HDFS.

Les états hdfs_avant.json et hdfs_apres.json sont égaux pour les 23 fichiers présents sous /retail-lake : chemins, tailles, dates de modification et checksums Hadoop. Les SHA-256 complets portent sur les neuf fichiers exportés. Le fichier _SUCCESS vide possède le SHA-256 standard du contenu vide ; il n'est pas une ligne Parquet.

Preuves : manifeste_export.json (source HDFS, destination locale, schémas, compteurs et neuf SHA-256), SHA256SUMS.txt, hdfs_avant.json, hdfs_apres.json, relecture_locale.log et preuves/executions/J3-P13-export-parquet.log. Les sorties Raw, Silver et Gold existantes n'ont pas été réécrites. Aucun DAT brut ni volume Docker n'a été copié.

Limites : ces contrôles démontrent l'identité et l'exploitabilité des copies ; ils ne corrigent pas les limites métier du kit synthétique. Le contrôle global HDFS repose sur les checksums Hadoop et métadonnées, complété par SHA-256 pour les fichiers exportés ; il ne prétend pas recalculer un SHA-256 de chaque fichier du lac.
