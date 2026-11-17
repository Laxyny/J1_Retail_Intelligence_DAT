"""Vérifie le dossier final, les chiffres de référence et l'intégrité des sources."""
import json
import math
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from PIL import Image
from openpyxl import load_workbook
from pypdf import PdfReader

from donnees_annexes import csv_rows
from profiler import OUT, digest

ROOT = Path(__file__).resolve().parents[2]

def check_capture_images(pdf):
    verified=[]
    for index in range(1,7):
        page_number=38+index
        page=pdf.pages[page_number-1]
        name=f'P{index:02d}'
        png=ROOT/'preuves'/'captures'/f'{name}.png'
        assert name in page.extract_text()
        assert len(page.images)==1
        with Image.open(png) as original:
            embedded=page.images[0].image
            assert original.size==embedded.size
            assert original.convert('RGBA').tobytes()==embedded.convert('RGBA').tobytes()
            ops=page.get_contents().operations
            transforms=[ops[i-1] for i,(_,op) in enumerate(ops) if op==b'Do']
            (matrix,op),=transforms
            assert op==b'cm'
            width,b,c,height,x,y=map(float,matrix)
            assert b==c==0 and width>0 and height>0
            assert math.isclose(width/height,original.width/original.height,rel_tol=1e-5)
            assert x>=0 and y>=0
            assert x+width<=float(page.mediabox.width) and y+height<=float(page.mediabox.height)
        verified.append(dict(id=name,page=page_number,sha256=digest(png),image_complete=True))
    return verified

def check_capture_values(profile, keys, fks, diagnostic, measures):
    # Valeurs lues dans les PNG fournies, comparées aux sorties existantes.
    files=profile['fichiers']
    for lot,count,size in [('data',24,1_024_448_074),('data_refresh',12,9_545_513)]:
        rows=[r for r in files if r['lot']==lot]
        assert (len(rows),sum(r['octets'] for r in rows))==(count,size)

    columns=[r for r in csv_rows('02_colonnes.csv')
             if r['lot']=='data' and r['table']=='store_sales']
    assert len(columns)==23 and [int(r['position']) for r in columns]==list(range(1,24))
    assert columns[9]['colonne']=='ss_ticket_number' and columns[9]['type_ddl']=='bigint'
    assert columns[20]['colonne']=='ss_net_paid' and columns[20]['type_ddl']=='decimal(7,2)'
    blanks={5:238,6:295,7:448,9:158}
    assert all(r['pages_ddl']=='131-132' and int(r['echantillon_types'])==20000
               and int(r['echecs_echantillon'])==0
               and int(r['vides'])==blanks.get(int(r['position']),0) for r in columns)

    initial={r['table']:r for r in files if r['lot']=='data'}
    assert tuple(initial[t]['attendus'] for t in ('inventory','store_sales','web_clickstreams'))==(4,23,6)
    for table,counts in {'inventory':(23255100,5999,5999,0),'time_dim':(86400,50400,50400,0),
                         'web_clickstreams':(6770550,2853461,8956123,0)}.items():
        assert tuple(initial[table][k] for k in ('lignes','fin_pipe','vides_bruts','largeur_hors_ddl'))==counts

    repeated={(r['lot'],r['table']):tuple(int(r[c]) for c in ('valides','distinctes','repetitions','cle_vide_ou_invalide'))
              for r in keys if r['table'] in {'inventory','store_sales','web_sales'}}
    assert repeated=={
        ('data','inventory'):(23255100,23255100,0,0),('data_refresh','inventory'):(234900,234900,0,0),
        ('data','store_sales'):(667579,663443,4136,0),('data_refresh','store_sales'):(6632,6586,46,0),
        ('data','web_sales'):(668052,663976,4076,0),('data_refresh','web_sales'):(6879,6840,39,0),
    }
    assert all(valid-distinct==extra for valid,distinct,extra,_ in repeated.values())
    assert all(diagnostic[lot,table,'lignes_repetitions_exactes']==0
               for lot,table in repeated if table.endswith('_sales'))

    joined={(r['lot'],r['source'],r['champ']):tuple(int(r[c]) for c in
            ('references_valides','hors_initial','hors_referentiels_livres')) for r in fks}
    for table,field,expected in (
        ('inventory','inv_item_sk',(234900,2520,0)),('store_sales','ss_item_sk',(6632,56,0)),
        ('store_sales','ss_customer_sk',(6632,94,0)),('web_sales','ws_item_sk',(6879,66,0)),
        ('web_sales','ws_bill_customer_sk',(6879,127,0)),('web_sales','ws_ship_customer_sk',(6879,123,0))):
        assert joined['data_refresh',table,field]==expected
    assert joined['data','inventory','inv_item_sk']==(23255100,232380,0)

    for table,expected in [('store_returns',(426,19,0)),('web_returns',(400,29,2))]:
        assert tuple(diagnostic['data_refresh',table,code] for code in
                     ('lignes_retour','trouve_lot_comparable','plusieurs_lignes_vente'))==expected
    checks={r['champ']:r for r in measures if r['lot']=='data'}
    for field,expected in [('inv_quantity_on_hand',('23249101','5999','23125','11627790630')),
                           ('ss_net_paid',('667579','0','3954','1150529586.37')),
                           ('ws_net_paid',('668052','0','3938','1535374825.67'))]:
        assert tuple(checks[field][c] for c in ('valides','vides','zero','somme'))==expected

def check_workbook_rows(book, name, expected, value_at):
    observed={tuple(row[:value_at]):row[value_at:] for row in book[name].iter_rows(min_row=5,values_only=True)}
    for key,values in expected.items():
        assert observed[key][:len(values)]==values, (name,key)

def main():
    profile=json.loads((OUT/'01_profil.json').read_text(encoding='utf-8'))
    files=profile['fichiers']
    source=Path(profile['execution']['source'])
    rechecked=[]
    for r in files:
        path=source/r['fichier']
        assert path.stat().st_size==r['octets'] and digest(path)==r['sha256'], path
        rechecked.append(path)
    for r in profile['documents_pedagogiques']:
        path=source.parents[1]/r['nom']
        assert path.stat().st_size==r['octets'] and digest(path)==r['sha256'], path
        rechecked.append(path)
    assert len(rechecked)==39 and sum(x['octets'] for x in files)==1_033_993_587
    assert sum(r['lignes'] for r in files if r['extension']=='.dat')==34_229_250
    assert all(not r['largeur_hors_ddl'] for r in files if r['extension']=='.dat')

    fks=csv_rows('04_relations.csv')
    assert len(fks)==142 and all(int(r['hors_referentiels_livres'])==0 for r in fks)
    keys=csv_rows('03_cles.csv')
    measures=csv_rows('06_mesures.csv')
    assert len(keys)==42
    diagnostic={(r['lot'],r['table'],r['controle']):int(r['resultat']) for r in csv_rows('07_diagnostics.csv')}
    assert diagnostic['data','store_sales','ids_distincts']==89_100
    assert diagnostic['data_refresh','store_returns','trouve_lot_comparable']==19
    assert diagnostic['data_refresh','web_returns','trouve_lot_comparable']==29

    project_pdfs=list(ROOT.rglob('*.pdf'))
    path=ROOT/'DAT_Retail_Intelligence_J1.pdf'
    assert project_pdfs==[path], project_pdfs
    pdf=PdfReader(path)
    assert len(pdf.pages)==len(pdf.outline)==44
    assert all(len(p.extract_text().strip())>=100 for p in pdf.pages)
    assert 'Kevin GREGOIRE' in pdf.pages[0].extract_text()
    assert pdf.metadata.author == 'Kevin GREGOIRE'
    assert 'À compléter' not in ''.join(p.extract_text() for p in pdf.pages)
    assert all(len(pdf.pages[n-1].images)==1 for n in (7,25,27,28,30,31,35))
    report=pdf.pages[36].extract_text()
    assert all(f'{n:02d} ' in report for n in range(1,13))
    assert 'P09' in report and len(pdf.pages[37].get('/Annots'))>=8
    assert '39–44' in pdf.pages[2].extract_text()
    assert 'K12 reste suspendu' in pdf.pages[43].extract_text()
    links=[annotation.get_object().get('/Dest') for p in pdf.pages[:38] for annotation in p.get('/Annots',[])]
    linked_pages={dest[0].idnum for dest in links if dest}
    assert all(p.indirect_reference.idnum in linked_pages for p in pdf.pages[38:])
    captures=check_capture_images(pdf)
    check_capture_values(profile,keys,fks,diagnostic,measures)
    kpi_text=''.join(p.extract_text() for p in pdf.pages[7:13])
    assert all(f'K{n:02d}' in kpi_text for n in range(1,28))
    assert '60,50' in kpi_text and '57,16' in kpi_text

    execution=json.loads((OUT/'11_kpi_execution.json').read_text(encoding='utf-8'))
    values=csv_rows('11_kpi_valeurs.csv')
    controls=csv_rows('13_kpi_controles.csv')
    kpi_fields=csv_rows('12_kpi_champs.csv')
    assert execution['statut']=='succès' and execution['fichiers_sha256']==23
    assert len(values)==execution['valeurs']==87
    assert len(kpi_fields)==execution['champs']==86
    assert len(controls)==execution['controles']==1180
    assert not any(r['kpi']=='K12' for r in values)
    assert all(r['note'].startswith('Prix courant item') for r in values if r['kpi']=='K26')
    for row in values:
        result=Decimal(row['valeur'])
        if row['denominateur']:
            factor=100 if row['unite']=='%' else 1
            assert result==Decimal(row['numerateur'])/Decimal(row['denominateur'])*factor, row
        else:
            assert result==Decimal(row['numerateur']), row
    assert sum(int(r['valeur']) for r in controls if r['controle']=='perte_vs_formule_tpc')==77210
    assert all(int(r['valeur'])==0 for r in controls if r['controle']=='perte_vs_port_plus_deux_taxes')

    expected={
      'UC01_inventaire_sources': {'Inventaire':36,'Colonnes':522,'Audits':2},
      'UC01_dictionnaire_KPI': {'Règles de calcul':27,'Sources et limites':27,'Audit K01–K12':12,
                                'Résultats P09':87,'Questions':16},
      'UC01_qualification_donnees': {'Complétude':522,'Clés':42,'Relations':142,'Périodes':16,
                                     'Mesures':50,'Diagnostics':101},
      'UC02_matrice_architecture': {'Comparaison':8,'Composants':13,'Local et Azure':7},
    }
    for filename,sheets in expected.items():
        book=load_workbook(ROOT/'annexes'/f'{filename}.xlsx',data_only=True)
        assert book.sheetnames==list(sheets)
        for name,count in sheets.items():
            tab=book[name]
            assert tab.max_row-4==count and len(tab.tables)==1 and tab.freeze_panes=='A5'
            assert not any(cell.data_type=='e' for row in tab.iter_rows() for cell in row)
        if filename=='UC01_inventaire_sources':
            assert sum(row[4] for row in book['Inventaire'].iter_rows(min_row=5,values_only=True))==1_033_993_587
            assert [book['Audits'][f'K{n}'].value for n in (5,6)]==[1,0]
            rows=[r for r in book['Inventaire'].iter_rows(min_row=5,values_only=True)]
            assert [(sum(r[0]==lot for r in rows),sum(r[4] for r in rows if r[0]==lot))
                    for lot in ('data','data_refresh')]==[(24,1024448074),(12,9545513)]
            cols=[r for r in book['Colonnes'].iter_rows(min_row=5,values_only=True)
                  if r[0:2]==('data','store_sales')]
            assert len(cols)==23 and cols[9][2:5]==(10,'ss_ticket_number','bigint')
            assert cols[20][2:5]==(21,'ss_net_paid','decimal(7,2)')
        if filename=='UC01_qualification_donnees':
            assert book['Périodes']['D5'].is_date
            check_workbook_rows(book,'Clés',{(r['lot'],r['table'],r['cle']):
                tuple(int(r[c]) for c in ('valides','distinctes','repetitions','cle_vide_ou_invalide'))
                for r in keys},3)
            check_workbook_rows(book,'Relations',{(r['lot'],r['source'],r['champ'],r['cible'],r['cle_cible']):
                tuple(int(r[c]) for c in ('lignes','vides','type_invalide','references_valides',
                                          'hors_initial','hors_referentiels_livres'))
                for r in fks},5)
            check_workbook_rows(book,'Diagnostics',{k:(v,) for k,v in diagnostic.items()},3)
            check_workbook_rows(book,'Mesures',{(r['lot'],r['table'],r['champ']):
                tuple(int(r[c]) for c in ('valides','vides','invalides','negatifs','zero'))
                for r in measures},3)
            totals={r[:3]:r[-1] for r in book['Mesures'].iter_rows(min_row=5,values_only=True)}
            for r in measures:
                assert math.isclose(totals[r['lot'],r['table'],r['champ']],float(r['somme']),
                                    rel_tol=0,abs_tol=.001)
        if filename=='UC01_dictionnaire_KPI':
            rules={r[0]:r[-1] for r in book['Règles de calcul'].iter_rows(min_row=5,values_only=True)}
            assert 'suspendu' in rules['K12'] and 'descriptif' in rules['K16'] and 'diagnostic' in rules['K26']
            actual=book['Résultats P09'].iter_rows(min_row=5,values_only=True)
            for worksheet,proof in zip(actual,values,strict=True):
                assert worksheet[0]==proof['kpi'] and worksheet[2]==proof['lot']
                assert math.isclose(worksheet[7],float(proof['valeur']),rel_tol=1e-13)
    assert all(len(list((ROOT/'preuves'/'schemas').glob('*'+suffix)))==7
               for suffix in ('.mmd','.svg','.png'))
    result={
        'date':datetime.now().astimezone().isoformat(timespec='seconds'),'statut':'succès',
        'commande':'python -B preuves/scripts/verifier_livrables.py',
        'empreintes_sources_recontrolees':len(rechecked),
        'pages_pdf':len(pdf.pages),'elements_TP1':12,'figures_pdf':7,
        'classeurs':len(expected),'onglets':sum(map(len,expected.values())),
        'resultats_kpi_reconcilies':len(values),'controles_p09':len(controls),
        'captures_terminal':len(captures),'captures_verifiees':captures,
    }
    (OUT/'08_verification_finale.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
