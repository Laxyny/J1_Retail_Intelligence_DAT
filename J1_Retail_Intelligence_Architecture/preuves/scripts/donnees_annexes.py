"""Assemble le contenu tabulaire des annexes depuis les preuves textuelles."""
import csv
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROOFS = ROOT/'preuves'/'resultats'

def csv_rows(name):
    with (PROOFS/name).open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream,delimiter=';'))

def number(value):
    if value in ('',None):
        return None
    if re.fullmatch(r'-?\d+',value):
        return int(value)
    if re.fullmatch(r'-?\d+\.\d+',value):
        return float(value)
    return value

def sheet(name, source, headers, rows, widths, decimals=None):
    return dict(name=name, source=source, headers=headers, rows=rows, widths=widths, decimals=decimals or {})

def select(rows, columns):
    return [[number(row[k]) for k in columns] for row in rows]

def main():
    profile=json.loads((PROOFS/'01_profil.json').read_text(encoding='utf-8'))
    catalogue=json.loads((ROOT/'travail'/'referentiel_dat.json').read_text(encoding='utf-8'))
    columns=csv_rows('02_colonnes.csv')
    keys=csv_rows('03_cles.csv')
    key_text={}
    for r in keys:
        key_text.setdefault((r['lot'],r['table']),[]).append(r['cle'])
    domains=dict(zip(
        'customer customer_address customer_demographics date_dim household_demographics income_band inventory item item_marketprices item_marketprices_audit product_reviews promotion reason ship_mode store store_returns store_sales time_dim warehouse web_clickstreams web_page web_returns web_sales web_site'.split(),
        ('Clients','Adresses','Démographie clients','Calendrier','Démographie foyers','Tranches de revenu','Stock entrepôt','Produits','Prix concurrents','Audit de génération','Avis','Promotions','Motifs de retour','Modes d’expédition','Magasins','Retours magasin','Ventes magasin','Heure','Entrepôts','Navigation','Pages web','Retours web','Ventes web','Sites web'),strict=True))
    inventory=[]
    for r in profile['fichiers']:
        notes = 'Largeur variable par section' if r['extension']=='.csv' else 'Sans en-tête, CRLF'
        if r['fin_pipe']:
            notes += ' ; dernier champ parfois vide'
        if r['table']=='web_clickstreams':
            notes += ' ; clé événement non vérifiée'
        inventory.append([r['lot'],r['fichier'],domains[r['table']],r['extension'],r['octets'],r['lignes'],
                          ', '.join(map(str,r['largeurs'])),r['format'],r['separateur'],r['encodage'],
                          r['vides_bruts'] if r['extension']=='.dat' else None,
                          'Oui' if r['homologue'] else 'Non',
                          ' / '.join(key_text.get((r['lot'],r['table']),[])),notes,r['sha256']])
    all_columns=select(columns,('lot','table','position','colonne','type_ddl','pages_ddl','lignes_conformes',
                               'vides','marqueurs_litteraux','echantillon_types','echecs_echantillon',
                               'min_entier_echantillon','max_entier_echantillon'))
    quality_rows=[[*r[:2],r[3],r[6],r[7],r[7]/r[6],r[9],r[10]] for r in all_columns]
    by_path={r['fichier']:r for r in profile['fichiers']}
    audits=[]
    for filename,audit in profile['audits'].items():
        count=by_path[filename.replace('_audit.csv','.dat')]['lignes']
        audits.append([filename,*map(number,audit['summary'].values()),count,
                       count-int(audit['summary']['numCompetitors'])])
    origin=date(1899,12,30)
    periods=[[r['lot'],r['table'],r['champ'],
              (date.fromisoformat(r['premiere'])-origin).days,
              (date.fromisoformat(r['derniere'])-origin).days,int(r['jours'])]
             for r in csv_rows('05_periodes.csv')]
    kpi_results=csv_rows('11_kpi_valeurs.csv')
    kpi_names={r[0]:r[1] for r in catalogue['kpis']}
    kpi_values=[[r['kpi'],kpi_names[r['kpi']],r['lot'],r['perimetre'],r['unite'],
                 number(r['numerateur']),number(r['denominateur']),number(r['valeur']),r['note']]
                for r in kpi_results]
    monetary_numerators={'K01','K04','K05','K08','K13','K14','K15','K16','K17','K18','K19','K20','K26','K27'}
    monetary_denominators={'K05','K08','K14','K27'}
    results_sheet=sheet('Résultats P09',
        '11_kpi_valeurs.csv · résultats par lot ; pour % la valeur est déjà multipliée par 100',
        ['ID','KPI','Lot','Périmètre','Unité','Numérateur','Dénominateur','Valeur','Note'],
        kpi_values,[57,245,145,284,159,151,151,151,349])
    results_sheet['rowFormats']=[{
        5:'#,##0.000' if r['kpi']=='K26' else '#,##0.00' if r['kpi'] in monetary_numerators else '#,##0',
        6:'#,##0.00' if r['kpi'] in monetary_denominators else '#,##0',
        7:'#,##0.0000' if r['denominateur'] else '#,##0.00' if r['kpi'] in monetary_numerators else '#,##0',
    } for r in kpi_results]
    xlsx={
      'UC01_inventaire_sources':[
        sheet('Inventaire','P01 · 01_profil.json et 03_cles.csv · mesures exhaustives',
              ['Lot','Chemin relatif','Domaine','Extension','Octets','Lignes physiques','Largeurs observées',
               'Format','Séparateur','Encodage','Cellules vides','Homologue','Clés candidates rapportées','Particularités','SHA-256'],
              inventory,[104,352,162,78,126,133,146,205,160,190,127,109,280,267,475]),
        sheet('Colonnes','P02 · 02_colonnes.csv · ordre DDL de l’annexe G et typage lexical échantillonné',
              ['Lot','Table','Position','Colonne DDL','Type DDL','Pages DDL','Lignes conformes','Cellules vides',
               'Marqueurs littéraux','Lignes échantillonnées','Échecs de type','Min entier échantillon','Max entier échantillon'],
              all_columns,[104,180,80,208,113,98,142,139,152,149,128,170,174]),
        sheet('Audits','P01 · 01_profil.json · résumé à huit champs, CSV à sections',
              ['Fichier','maxItems','realMaxItems','numCompetitors','minComPerITem','maxComPerItem','avgComPerItem',
               'itemsWithoutCompetitors','itemsNotHavingMinCompetitors','Lignes DAT prix','DAT moins compteur audit'],
              audits,
              [365,100,118,145,142,142,150,195,233,146,182],{6:'0.000000'}),
      ],
      'UC01_dictionnaire_KPI':[
        sheet('Règles de calcul','TP1 §5.1 et DAT p. 8–13 · preuves P02, P04–P06 et P09',
              ['ID','Domaine','KPI','Objectif','Formule','Unité','Grain','Statut'],
              [[r[0],catalogue['kpi_domains'][r[0]],*r[1:6],r[-1]] for r in catalogue['kpis']],
              [57,156,232,232,395,169,255,205]),
        sheet('Sources et limites','DAT p. 8–13 · relation, filtres et limites propres à chaque indicateur',
              ['ID','KPI','Sources et champs','Jointure ou regroupement','Axes','Fréquence','Filtres','Limites'],
              [[*r[:2],r[6],catalogue['kpi_relations'][r[0]],*r[7:11]] for r in catalogue['kpis']],
              [57,218,381,362,235,140,325,374]),
        sheet('Audit K01–K12','P02, P04–P06, P09 · audit du dictionnaire de la version 1.0',
              ['ID','KPI','Décision','Grain, formule et contrôle','Fiabilité et limite de publication'],
              [[row[0],kpi_names[row[0]],*row[1:]] for row in catalogue['kpi_audit']],[57,239,174,400,440]),
        results_sheet,
        sheet('Questions','TP1 §5.1 / DAT p. 5–6 · priorités et faisabilité proposées',
              ['ID','Utilisateur','Priorité','Question','Données nécessaires','KPI','Décision','Faisabilité'],
              catalogue['questions'],[60,174,118,322,235,112,255,281]),
      ],
      'UC01_qualification_donnees':[
        sheet('Complétude','P02 · 02_colonnes.csv · vides exhaustifs, typage par échantillon',
              ['Lot','Table','Colonne','Lignes conformes','Champs vides','Part vide','Échantillon','Échecs de type'],
              quality_rows,[104,183,220,145,135,100,124,133],{5:'0.00%'}),
        sheet('Clés','P04 · 03_cles.csv · contrôles exhaustifs, grain candidat',
              ['Lot','Table','Clé candidate','Lignes à clé valide','Clés distinctes','Répétitions','Vides ou invalides','Clé dans initial'],
              [list(map(number,r.values())) for r in keys],[104,182,334,160,137,115,143,150]),
        sheet('Relations','P05 · 04_relations.csv · couverture initiale et couverture après intégration des références livrées',
              ['Lot','Table source','Champ source','Table cible','Clé cible','Lignes','Vides','Type invalide',
               'Réf. valides','Hors initial','Hors réf. livrés'],
              [list(map(number,r.values())) for r in csv_rows('04_relations.csv')],[104,168,184,180,190,125,100,119,125,126,133]),
        sheet('Périodes','P06 · 05_periodes.csv · jours observés après résolution des dates',
              ['Lot','Table','Champ','Date min.','Date max.','Jours distincts'],
              periods,[114,186,204,126,126,164],{3:'yyyy-mm-dd',4:'yyyy-mm-dd'}),
        sheet('Mesures','P06 · 06_mesures.csv · sommes de rapprochement sur lignes physiques, montants dans l’unité du kit',
              ['Lot','Table','Champ','Valides','Vides','Invalides','Négatifs','Zéros','Min.','Max.','Somme'],
              [list(map(number,r.values())) for r in csv_rows('06_mesures.csv')],[102,174,202,117,98,101,105,101,103,112,158],
              {8:'#,##0.00',9:'#,##0.00',10:'#,##0.00'}),
        sheet('Diagnostics','P06 · 07_diagnostics.csv · en-têtes distincts et rapprochements des retours',
              ['Lot','Table','Contrôle','Résultat'],
              [list(map(number,r.values())) for r in csv_rows('07_diagnostics.csv')],[120,247,290,128]),
      ],
      'UC02_matrice_architecture':[
        sheet('Comparaison','TP1 §5.2 · cours diap. 39–50 · choix et limites dans le DAT p. 24',
              ['Critère','Data Warehouse','Data Lake','Data Lakehouse'],
              catalogue['compare'],[178,287,292,337]),
        sheet('Composants','TP1 §5.2 et cours diap. 49–52 · architecture cible, situation réelle J1 indiquée',
              ['Composant','Statut','Rôle','Condition ou limite'],
              catalogue['architecture'],[205,246,316,394]),
        sheet('Local et Azure','TP1 §5.2 · DAT D5–D10 (Microsoft Learn) · proposition à valider au Jour 4',
              ['Rôle','Cible locale','Cible Azure','Conditions de portabilité'],
              catalogue['azure'],[178,281,306,361]),
      ],
    }
    print(json.dumps(xlsx,ensure_ascii=False))

if __name__=='__main__':
    main()
