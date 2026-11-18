"""Relecture autonome des copies locales, sans HDFS ni données Raw."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from pyspark.sql import SparkSession, functions as F


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--racine',type=Path,default=Path(__file__).resolve().parents[2])
    args=parser.parse_args()
    root=args.racine.resolve()
    evidence=json.loads((root/'donnees_produites/verification_export/manifeste_export.json').read_text(encoding='utf-8'))
    os.environ['PYSPARK_PYTHON']=sys.executable
    spark=(SparkSession.builder.master('local[2]').appName('UC06-copies-locales')
           .config('spark.ui.enabled','false').config('spark.hadoop.fs.defaultFS','file:///').getOrCreate())
    spark.sparkContext.setLogLevel('WARN')
    try:
        for name,expected in evidence['datasets'].items():
            path=root/expected['local_relative']
            files={str(p.relative_to(path)) for p in path.rglob('*') if p.is_file()}
            assert files==set(expected['files']),name
            for info in expected['files'].values():
                local=root/info['local_relative']
                with local.open('rb') as stream:
                    assert hashlib.file_digest(stream,'sha256').hexdigest()==info['sha256_windows'],local
                assert local.stat().st_size==info['bytes'],local
            df=spark.read.parquet(path.as_uri())
            assert df.schema.jsonValue()==expected['schema'],name
            count=df.count()
            assert count==expected['rows'],name
            if name.startswith('gold_'):
                totals=df.agg(F.sum('quantity_sold').alias('quantity'),F.sum('net_paid').alias('net_paid'),F.sum('sales_line_count').alias('rows')).first().asDict()
                assert totals['quantity']==33755474 and str(totals['net_paid'])=='1150529586.37' and totals['rows']==667579
                print('Totaux Gold',totals,flush=True)
            print(name,count,'lignes ; schéma et SHA-256 OK',flush=True)
        print('RELECTURE LOCALE RÉUSSIE ; aucun accès HDFS nécessaire',flush=True)
    finally:
        spark.stop()


if __name__=='__main__':
    main()
