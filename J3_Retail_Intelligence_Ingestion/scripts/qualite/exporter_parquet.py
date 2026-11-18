"""Exporte les Parquet HDFS existants ; aucune transformation ni écriture HDFS."""
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uc06 import ROOT, session, F

LOT='20261118T113628Z-243a5fb5-r3'
TARGETS={'silver_store_sales':'silver/store_sales', 'silver_item':'silver/item',
         'gold_ventes_par_produit':'gold/ventes_par_produit'}


def digest_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def hdfs_sha(uri):
    process=subprocess.Popen(['hdfs','dfs','-cat',uri],stdout=subprocess.PIPE)
    result=hashlib.file_digest(process.stdout,'sha256').hexdigest()
    process.stdout.close()
    assert process.wait()==0,uri
    return result


def main():
    expected=json.loads((ROOT/'donnees_produites/manifest.json').read_text(encoding='utf-8'))
    assert set(expected)==set(TARGETS)
    destination=ROOT/'donnees_produites/export'
    evidence=ROOT/'donnees_produites/verification_export'
    assert not destination.exists(),'Export existant : vérifier sa provenance et ne pas écraser'
    evidence.mkdir(exist_ok=True)
    assert not (evidence/'manifeste_export.json').exists(),'Preuve existante : ne pas écraser'
    stage=ROOT/'donnees_produites'/('.export-validation-'+uuid.uuid4().hex[:12])
    stage.mkdir()
    spark=session('UC06-export-validation-lecture-seule')
    fs=spark._jvm.org.apache.hadoop.fs.FileSystem.get(spark._jsc.hadoopConfiguration())
    def snapshot():
        result={}
        entries=fs.listFiles(spark._jvm.org.apache.hadoop.fs.Path('/retail-lake'),True)
        while entries.hasNext():
            entry=entries.next()
            uri=str(entry.getPath())
            checksum=fs.getFileChecksum(entry.getPath())
            result[uri]=dict(bytes=entry.getLen(),mtime=entry.getModificationTime(),
                             hadoop_checksum=str(checksum) if checksum else None)
        return result
    before=snapshot()
    (evidence/'hdfs_avant.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    datasets={}
    try:
        for key,relative in TARGETS.items():
            entry=expected[key]
            required='hdfs://hdfs:9000/retail-lake/'+relative.split('/')[0]+'/j3/'+LOT+'/'+relative.split('/')[1]
            assert entry['path']==required,(entry['path'],required)
            assert fs.isDirectory(spark._jvm.org.apache.hadoop.fs.Path(required)),required
            files={}
            iterator=fs.listFiles(spark._jvm.org.apache.hadoop.fs.Path(required),True)
            while iterator.hasNext():
                status=iterator.next()
                uri=str(status.getPath())
                name=uri[len(required)+1:]
                files[name]=dict(hdfs=uri,bytes=status.getLen(),sha256_hdfs=hdfs_sha(uri))
            assert len(files)==entry['files']
            assert sum(f['bytes'] for f in files.values())==entry['bytes']
            assert '_SUCCESS' in files and any(n.endswith('.parquet') for n in files)
            target=stage/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            subprocess.run(['hdfs','dfs','-get',required,str(target)],check=True)
            downloaded={str(p.relative_to(target)):p for p in target.rglob('*') if p.is_file()}
            assert set(downloaded)==set(files),(key,set(downloaded),set(files))
            for name,local in downloaded.items():
                info=files[name]
                info['local_relative']='donnees_produites/export/'+relative+'/'+name
                info['sha256_windows']=digest_file(local)
                assert local.stat().st_size==info['bytes']
                assert info['sha256_windows']==info['sha256_hdfs']
            frame=spark.read.parquet(target.as_uri())
            assert frame.schema.jsonValue()==entry['schema_after']
            rows=frame.count()
            assert rows==entry['rows_after']
            assert [r[0] for r in frame.select('_run_id').distinct().collect()]==[LOT]
            if key=='silver_store_sales':
                totals=frame.agg(F.sum('ss_quantity').alias('quantity'),F.sum('ss_net_paid').alias('net_paid')).first().asDict()
            elif key=='gold_ventes_par_produit':
                totals=frame.agg(F.sum('quantity_sold').alias('quantity'),F.sum('net_paid').alias('net_paid'),F.sum('sales_line_count').alias('sales_rows')).first().asDict()
            else:
                totals={}
            if totals:
                assert totals['quantity']==33755474 and str(totals['net_paid'])=='1150529586.37'
            if key.startswith('gold_'):
                assert totals['sales_rows']==667579
            datasets[key]=dict(hdfs=required,local_relative='donnees_produites/export/'+relative,
                               rows=rows,schema=frame.schema.jsonValue(),bytes=sum(x['bytes'] for x in files.values()),
                               parquet_files=sum(n.endswith('.parquet') for n in files),total_files=len(files),
                               files=files,totals=totals,status='OK')
            print(key,rows,'lignes ;',len(files),'fichiers ; intégrité SHA-256 OK',flush=True)
        after=snapshot()
        assert before==after,'Un fichier HDFS a changé durant la vérification'
        stage.rename(destination)
        result=dict(status='OK',lot=LOT,exported_at=datetime.now(timezone.utc).isoformat(),
                    export_method='hdfs dfs -get, sans -f ; publication du staging après validation',
                    datasets=datasets,hdfs_unchanged=True,hdfs_files_checked=len(before),
                    hdfs_comparison='chemins, tailles, dates de modification et checksums Hadoop ; SHA-256 complets des 9 fichiers exportés',
                    pipeline_reexecuted=False)
        with (evidence/'manifeste_export.json').open('x',encoding='utf-8') as stream:
            json.dump(result,stream,indent=2,ensure_ascii=False,default=str)
        sums=[f"{f['sha256_windows']}  {f['local_relative']}" for d in datasets.values() for f in d['files'].values()]
        (evidence/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')
        print('EXPORT VALIDÉ ET PUBLIÉ',destination,flush=True)
    finally:
        after=snapshot()
        (evidence/'hdfs_apres.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
        spark.stop()
        assert before==after,'Divergence HDFS : ne pas considérer l’export comme valide'


if __name__=='__main__':
    main()
