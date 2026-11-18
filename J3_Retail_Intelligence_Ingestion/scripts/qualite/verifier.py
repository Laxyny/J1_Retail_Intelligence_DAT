"""Relecture autonome, contrôles persistés et protection des dépôts HDFS J2."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from decimal import Decimal
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uc06 import ROOT, session, save, F


def main():
    summary=json.loads((ROOT/'preuves/controles/J3-P06-transformation.json').read_text())
    spark=session('UC06-verification-independante')
    results={}
    for name,expected in summary['outputs'].items():
        df=spark.read.parquet(expected['path'])
        n=df.count()
        assert n==expected['rows_after']
        assert df.schema.jsonValue()==expected['schema_after']
        fs=spark._jvm.org.apache.hadoop.fs.FileSystem.get(spark._jsc.hadoopConfiguration())
        iterator=fs.listFiles(spark._jvm.org.apache.hadoop.fs.Path(expected['path']),True)
        files=[]
        while iterator.hasNext():
            entry=iterator.next()
            files.append(dict(path=str(entry.getPath()),bytes=entry.getLen(),replication=entry.getReplication()))
        assert any(f['path'].endswith('.parquet') and f['bytes']>0 for f in files)
        assert any(f['path'].endswith('_SUCCESS') for f in files)
        results[name]=dict(rows=n,schema=df.schema.jsonValue(),files=files)
    gold=spark.read.parquet(summary['outputs']['gold_ventes_par_produit']['path'])
    totals=gold.agg(F.sum('quantity_sold').alias('quantity'),F.sum('net_paid').alias('net_paid'),F.sum('sales_line_count').alias('rows')).first().asDict()
    assert totals['quantity']==summary['totals']['quantity']
    assert totals['net_paid']==Decimal(summary['totals']['net_paid'])
    assert totals['rows']==summary['totals']['rows']
    reason={}
    for path in ['/retail-lake/raw/tpcxbb/initial/reason.dat','/retail-lake/raw/nifi/reason.dat']:
        data=subprocess.check_output(['hdfs','dfs','-fs','hdfs://hdfs:9000','-cat',path])
        digest=hashlib.sha256(data).hexdigest()
        assert digest=='d5edc45cb1e76afde3b7c0718cdd5d5d45e5f1d720fb940b36db0cd4dcf6b091'
        reason[path]=digest
    notebook=json.loads((ROOT/'notebooks/UC06_exploration.ipynb').read_text())
    code=[c for c in notebook['cells'] if c['cell_type']=='code']
    assert all(c['execution_count'] is not None for c in code)
    assert not any(o['output_type']=='error' for c in code for o in c['outputs'])
    result=dict(status='OK',outputs=results,totals=totals,reason_j2_unchanged=reason,
                notebook_code_cells=len(code),notebook_errors=0,
                checks=len(summary['checks']),failed=sum(c['status']=='ECHEC' for c in summary['checks']))
    assert result['failed']==0
    save('preuves/controles/J3-P10-verification.json',result)
    save('donnees_produites/manifest.json',summary['outputs'])
    print(json.dumps(result,indent=2,default=str))
    spark.stop()


if __name__=='__main__':
    main()
