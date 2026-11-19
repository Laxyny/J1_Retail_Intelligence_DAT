# Affiche les preuves du run local dans un terminal Windows. Lecture seule.
param(
    [Parameter(Mandatory)]
    [ValidateSet('P01','P02','P03','P04','P05','P06')]
    [string]$Id
)
$ErrorActionPreference = 'Stop'
$results = Join-Path $PSScriptRoot '..\resultats'
function Read-Result([string]$Name) {
    Import-Csv -LiteralPath (Join-Path $results $Name) -Delimiter ';' -Encoding UTF8
}
$profil = Get-Content -LiteralPath (Join-Path $results '01_profil.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$control = Get-Content -LiteralPath (Join-Path $results '03_execution.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$origin = if ($Id -in 'P01','P02','P03') { $profil.execution } else { $control }
Write-Host "$Id | Retail Intelligence Platform | traitement du $($origin.fin) | $($origin.statut)" -ForegroundColor Cyan
switch ($Id) {
    'P01' {
        $source = Get-Item -LiteralPath $profil.execution.source
        foreach ($lot in 'data','data_refresh') {
            $folder = Join-Path $source.FullName $lot
            $files = Get-ChildItem -LiteralPath $folder -Recurse -File
            $octets = ($files | Measure-Object -Property Length -Sum).Sum
            Write-Host "$lot | $($files.Count) fichiers | $octets octets"
            $dirs = (Get-ChildItem -LiteralPath $folder -Directory).Name -join ', '
            Write-Host "  $dirs"
        }
    }
    'P02' {
        Read-Result '02_colonnes.csv' |
            Where-Object { $_.lot -eq 'data' -and $_.table -eq 'store_sales' } |
            Select-Object position,colonne,type_ddl,pages_ddl,vides,echantillon_types,echecs_echantillon |
            Format-Table -AutoSize
    }
    'P03' {
        foreach ($name in 'data/inventory/inventory.dat','data/store_sales/store_sales.dat','data/web_clickstreams/web_clickstreams.dat') {
            Write-Host $name
            $preview = $profil.apercus_masques_3_premieres_lignes.PSObject.Properties[$name].Value[0]
            Write-Host "  ligne $($preview.ligne), $($preview.champs) champs : $($preview.structure)"
        }
        $profil.fichiers | Where-Object { $_.lot -eq 'data' -and $_.table -in 'inventory','time_dim','web_clickstreams' } |
            Select-Object table,lignes,fin_pipe,vides_bruts,largeur_hors_ddl | Format-Table -AutoSize
    }
    'P04' {
        Read-Result '03_cles.csv' | Where-Object { $_.table -in 'store_sales','web_sales','inventory' } |
            Select-Object lot,table,cle,valides,distinctes,repetitions,cle_vide_ou_invalide | Format-Table -AutoSize
    }
    'P05' {
        Read-Result '04_relations.csv' | Where-Object {
            ($_.source -eq 'inventory' -and $_.cible -eq 'item') -or
            ($_.lot -eq 'data_refresh' -and $_.source -in 'store_sales','web_sales' -and $_.champ -match '(item_sk|customer_sk)$')
        } | Select-Object lot,source,champ,cible,references_valides,hors_initial,hors_referentiels_livres |
            Format-Table -AutoSize
    }
    'P06' {
        Read-Result '07_diagnostics.csv' | Where-Object {
            $_.lot -eq 'data_refresh' -and $_.table -in 'store_returns','web_returns' -and
            $_.controle -in 'lignes_retour','trouve_lot_comparable','plusieurs_lignes_vente'
        } | Format-Table -AutoSize
        Read-Result '06_mesures.csv' | Where-Object {
            $_.lot -eq 'data' -and $_.champ -in 'inv_quantity_on_hand','ss_net_paid','ws_net_paid'
        } | Select-Object lot,table,champ,valides,vides,zero,somme | Format-Table -AutoSize
    }
}
