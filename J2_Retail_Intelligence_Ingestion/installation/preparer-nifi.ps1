$ErrorActionPreference = 'Stop'
$narDir = Join-Path $env:LOCALAPPDATA 'RetailIngestionJ2/nar'
New-Item -Path $narDir -ItemType Directory -Force | Out-Null
$sha256 = [ordered]@{
    'nifi-hadoop-nar' = '1A9C5C32505F4F256BD7B9B3284AF761BF32C0D0D8225BA3DC536A07482522A5'
    'nifi-hadoop-libraries-nar' = 'C6496F21A24276070B1DB28BAC5DED004F21549E00FD143013524FF4E96449BE'
}
foreach ($artifact in $sha256.Keys) {
    $file = "$artifact-2.12.0.nar"
    $target = Join-Path $narDir $file
    $url = "https://repo.maven.apache.org/maven2/org/apache/nifi/$artifact/2.12.0/$file"
    if (!(Test-Path -LiteralPath $target)) {
        Invoke-WebRequest -Uri $url -OutFile $target
    }
    $actual = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if ($actual -ne $sha256[$artifact]) {
        throw "SHA-256 incorrect pour $target. Vérifier le cache avant de recommencer."
    }
    "$actual  $file"
}
