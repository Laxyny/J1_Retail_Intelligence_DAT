$ErrorActionPreference = 'Stop'
$j3Root = Split-Path $PSScriptRoot -Parent
$projectRoot = Split-Path $j3Root -Parent
$sourceRoot = Join-Path $projectRoot '01. Architecture DataLake, DataWarehouse, Lakehous\retail_project\retail_project'
if (-not (Test-Path -LiteralPath "$sourceRoot\data\store_sales\store_sales.dat")) { throw 'Sources absentes' }
foreach ($relativeSource in @('data\item\item.dat','data_refresh\item\item.dat')) {
    if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot $relativeSource) -PathType Leaf)) { throw "Source absente : $relativeSource" }
}
docker inspect retail-j2-hdfs-1 *> $null
if ($LASTEXITCODE -ne 0) { throw 'Conteneur HDFS J2 absent : ne pas recréer ses volumes' }
$hdfsState = docker inspect retail-j2-hdfs-1 --format '{{.State.Running}}'
if ($hdfsState -ne 'true') { docker start retail-j2-hdfs-1; if ($LASTEXITCODE) { throw 'Démarrage J2 impossible : vérifier les montages sans recréer les volumes' } }
$processes = docker exec retail-j2-hdfs-1 jps
if ($LASTEXITCODE) { throw 'Diagnostic des démons HDFS impossible' }
if (-not ($processes -match 'NameNode')) { docker exec retail-j2-hdfs-1 hdfs --daemon start namenode }
if ($LASTEXITCODE) { throw 'Démarrage NameNode impossible' }
if (-not ($processes -match 'DataNode')) { docker exec retail-j2-hdfs-1 hdfs --daemon start datanode }
if ($LASTEXITCODE) { throw 'Démarrage DataNode impossible' }
docker inspect retail-j3-spark *> $null
if ($LASTEXITCODE -ne 0) {
    docker run -d --name retail-j3-spark --network retail-j2_default --memory 4g --cpus 4 -v "${j3Root}:/work" -v "${sourceRoot}:/sources:ro" --entrypoint /bin/bash retail-j2-hadoop:3.5.0 -c 'exec sleep infinity'
    if ($LASTEXITCODE) { throw 'Création Spark impossible' }
} else {
    docker start retail-j3-spark
    if ($LASTEXITCODE) { throw 'Démarrage Spark impossible' }
}
docker exec retail-j3-spark test -x /tmp/retail-j3-venv/bin/python
if ($LASTEXITCODE -ne 0) {
    docker exec retail-j3-spark bash /work/configuration/installer-python.sh
    if ($LASTEXITCODE) { throw 'Installation isolée impossible' }
}
docker exec retail-j2-hdfs-1 hdfs dfsadmin -safemode get
if ($LASTEXITCODE) { throw 'HDFS inaccessible' }
docker exec retail-j2-hdfs-1 hdfs dfs -ls /retail-lake/raw/tpcxbb/initial/reason.dat
if ($LASTEXITCODE) { throw 'Fichier de test HDFS absent' }
docker exec retail-j3-spark /tmp/retail-j3-venv/bin/python -c 'import pyspark, nbclient, nbformat, ipykernel, nbconvert; print(pyspark.__version__)'
if ($LASTEXITCODE) { throw 'PySpark indisponible' }
