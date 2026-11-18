$ErrorActionPreference = 'Stop'
$j3Root = Split-Path $PSScriptRoot -Parent
$requiredScripts = @('exploration/test_spark.py','exploration/inventorier.py','exploration/preparer_entrees.py','exploration/notebook.py','transformation/transformer.py','qualite/verifier.py')
foreach ($requiredScript in $requiredScripts) {
    if (-not (Test-Path -LiteralPath "$j3Root\scripts\$requiredScript" -PathType Leaf)) { throw "Script absent : $requiredScript" }
}
if (-not (Test-Path -LiteralPath "$j3Root\donnees_produites\manifest.json" -PathType Leaf)) { throw 'Manifeste des résultats absent' }
$configPath = Join-Path $j3Root 'configuration\parametres\execution.json'
if (Test-Path -LiteralPath $configPath) {
    $previousRun = (Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json).run_id
    if ($previousRun -notmatch '^\d{8}T\d{6}Z-[0-9a-f]{8}(?:-r\d+)?$') { throw 'Identifiant du lot précédent invalide' }
    $archive = Join-Path $j3Root "preuves\historique\$previousRun"
    if (Test-Path -LiteralPath $archive) { throw 'Archive déjà présente : consulter les sorties existantes avant reprise' }
}
& "$j3Root\configuration\preparer.ps1"
if (Test-Path -LiteralPath $configPath) {
    New-Item -ItemType Directory -Path $archive | Out-Null
    Copy-Item -LiteralPath "$j3Root\preuves\controles","$j3Root\preuves\parquet","$j3Root\preuves\executions","$j3Root\notebooks","$j3Root\configuration\parametres" -Destination $archive -Recurse
    Copy-Item -LiteralPath "$j3Root\donnees_produites\manifest.json" -Destination "$archive\manifest.json"
}
$steps = @(
    @('scripts/exploration/test_spark.py', @()),
    @('scripts/exploration/inventorier.py', @('--sources','/sources')),
    @('scripts/exploration/preparer_entrees.py', @()),
    @('scripts/exploration/notebook.py', @()),
    @('scripts/transformation/transformer.py', @()),
    @('scripts/qualite/verifier.py', @())
)
foreach ($step in $steps) {
    $scriptName = $step[0]
    $scriptArgs = $step[1]
    $logName = (Split-Path $scriptName -Leaf) + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log'
    docker exec retail-j3-spark /tmp/retail-j3-venv/bin/python "/work/$scriptName" @scriptArgs 2>&1 | Tee-Object -FilePath "$j3Root\preuves\executions\$logName"
    if ($LASTEXITCODE -ne 0) { throw "Échec de $scriptName : conserver le journal et analyser avant reprise" }
}
