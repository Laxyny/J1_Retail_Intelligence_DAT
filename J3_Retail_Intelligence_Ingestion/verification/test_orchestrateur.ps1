# Tests du pilotage uniquement : aucun Docker réel ni traitement Spark lancé.
$ErrorActionPreference = 'Stop'
$j3Root = Split-Path $PSScriptRoot -Parent
$testRoot = Join-Path $PSScriptRoot ('correction_20261118\tests-' + [guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $testRoot | Out-Null
$lot = '20261118T113628Z-243a5fb5-r3'
$global:uc06Calls = @()
$global:uc06FailAt = -1
function global:docker {
    $global:uc06Calls += ,@($args)
    $global:LASTEXITCODE = if ($global:uc06Calls.Count -eq $global:uc06FailAt) { 7 } else { 0 }
    Write-Output ('DOCKER SIMULE : ' + ($args -join ' '))
}
function New-Fixture([string]$Name) {
    $fixture = Join-Path $testRoot $Name
    foreach ($relative in @('configuration\parametres','donnees_produites','scripts\exploration','scripts\transformation','scripts\qualite','preuves\controles','preuves\parquet','preuves\executions','notebooks')) {
        New-Item -ItemType Directory -Path (Join-Path $fixture $relative) -Force | Out-Null
    }
    Copy-Item -LiteralPath "$j3Root\scripts\reproduire.ps1" -Destination "$fixture\scripts\reproduire.ps1"
    Set-Content "$fixture\configuration\preparer.ps1" '$global:LASTEXITCODE = 0' -Encoding utf8
    Set-Content "$fixture\configuration\parametres\execution.json" ('{"run_id":"' + $lot + '"}') -Encoding utf8
    Set-Content "$fixture\donnees_produites\manifest.json" '{"fixture":true}' -Encoding utf8
    foreach ($relative in @('exploration/test_spark.py','exploration/inventorier.py','exploration/preparer_entrees.py','exploration/notebook.py','transformation/transformer.py','qualite/verifier.py')) {
        Set-Content "$fixture\scripts\$relative" '# Fixture non exécutée' -Encoding utf8
    }
    Set-Content "$fixture\preuves\controles\original.json" '{"preuve":"fixture"}' -Encoding utf8
    Set-Content "$fixture\notebooks\original.ipynb" '{"fixture":true}' -Encoding utf8
    return $fixture
}
function Assert-True([bool]$Value,[string]$Message) { if (-not $Value) { throw $Message } }
$results = @()
try {
    $f = New-Fixture 'succes'
    $global:uc06Calls = @()
    & "$f\scripts\reproduire.ps1"
    $expected = @('test_spark.py','inventorier.py','preparer_entrees.py','notebook.py','transformer.py','verifier.py')
    $observed = @($global:uc06Calls | ForEach-Object { Split-Path $_[3] -Leaf })
    Assert-True (($observed -join ',') -eq ($expected -join ',')) 'Ordre incorrect'
    Assert-True (($global:uc06Calls[1] -join ' ') -match '--sources /sources') 'Paramètres inventaire absents'
    Assert-True ((Get-FileHash "$f\donnees_produites\manifest.json").Hash -eq (Get-FileHash "$f\preuves\historique\$lot\manifest.json").Hash) 'Manifeste non archivé'
    Assert-True (Test-Path "$f\preuves\historique\$lot\controles\original.json") 'Preuve non archivée'
    Assert-True (@(Get-ChildItem "$f\preuves\executions" -Filter '*.log').Count -eq 6) 'Journaux incomplets'
    $results += @{test='Ordre, paramètres, archivage, journaux';status='OK';docker='simulé'}

    $f = New-Fixture 'echec-etape'
    $global:uc06Calls = @(); $global:uc06FailAt = 3
    $message = ''
    try { & "$f\scripts\reproduire.ps1" } catch { $message = $_.Exception.Message }
    Assert-True ($message -match 'Échec de scripts/exploration/preparer_entrees.py') 'Erreur non propagée'
    Assert-True ($global:uc06Calls.Count -eq 3) 'Le script poursuit après échec'
    $results += @{test='Arrêt après code 7 simulé';status='OK';docker='simulé'}
    $global:uc06FailAt = -1

    $f = New-Fixture 'archive-existante'
    New-Item -ItemType Directory -Path "$f\preuves\historique\$lot" | Out-Null
    Set-Content "$f\preuves\historique\$lot\conserver.txt" 'archive intacte'
    $global:uc06Calls = @(); $message = ''
    try { & "$f\scripts\reproduire.ps1" } catch { $message = $_.Exception.Message }
    Assert-True ($message -match 'Archive déjà présente') 'Archive existante non refusée'
    Assert-True ($global:uc06Calls.Count -eq 0) 'Docker appelé malgré archive existante'
    Assert-True ((Get-Content "$f\preuves\historique\$lot\conserver.txt") -eq 'archive intacte') 'Archive altérée'
    $results += @{test='Archive existante préservée';status='OK';docker='aucun appel'}

    $f = New-Fixture 'identifiant-invalide'
    Set-Content "$f\configuration\parametres\execution.json" '{"run_id":"../hors_projet"}'
    $global:uc06Calls = @(); $message = ''
    try { & "$f\scripts\reproduire.ps1" } catch { $message = $_.Exception.Message }
    Assert-True ($message -match 'Identifiant du lot précédent invalide') 'Identifiant invalide accepté'
    Assert-True ($global:uc06Calls.Count -eq 0) 'Docker appelé malgré identifiant invalide'
    $results += @{test='Identifiant de lot contrôlé';status='OK';docker='aucun appel'}

    $f = New-Fixture 'script-manquant'
    Move-Item -LiteralPath "$f\scripts\qualite\verifier.py" -Destination "$f\scripts\qualite\verifier.py.fixture-conservee"
    $global:uc06Calls = @(); $message = ''
    try { & "$f\scripts\reproduire.ps1" } catch { $message = $_.Exception.Message }
    Assert-True ($message -match 'Script absent') 'Script manquant accepté'
    Assert-True ($global:uc06Calls.Count -eq 0) 'Docker appelé malgré script manquant'
    $results += @{test='Chemins requis vérifiés avant action';status='OK';docker='aucun appel'}
    $results | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $testRoot 'resultats.json') -Encoding utf8
    $results | ConvertTo-Json -Depth 4
} finally {
    Remove-Item Function:\docker
}
