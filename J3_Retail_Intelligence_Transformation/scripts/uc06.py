"""Fonctions communes UC-06 : schémas, lecture, exploration et sorties sûres."""
import json
import os
import sys
from pathlib import Path
from pyspark.sql import SparkSession, functions as F, types as T

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = json.loads((ROOT / 'configuration/parametres/schemas.json').read_text())


def save(path, value):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding='utf-8')


def session(name):
    os.environ['PYSPARK_PYTHON'] = sys.executable
    spark = (SparkSession.builder.master('local[2]').appName(name)
             .config('spark.driver.memory', '1536m')
             .config('spark.sql.shuffle.partitions', '4')
             .config('spark.ui.enabled', 'false')
             .config('spark.sql.ansi.enabled', 'true')
             .config('spark.sql.session.timeZone', 'UTC')
             .config('spark.hadoop.fs.defaultFS', 'hdfs://hdfs:9000')
             .config('spark.hadoop.dfs.replication', '1')
             .config('spark.hadoop.dfs.client.use.datanode.hostname', 'true')
             .getOrCreate())
    spark.sparkContext.setLogLevel('WARN')
    return spark


def read_source(spark, table, path):
    columns = SCHEMAS[table]['columns']
    schema = T.StructType([T.StructField(n, T.StringType(), True) for n, _ in columns])
    raw = (spark.read.schema(schema).option('sep', '|').option('header', False)
           .option('encoding', 'UTF-8').option('mode', 'FAILFAST').csv(path))
    converted = raw.select(*[F.expr(f'try_cast(`{n}` as {t})').alias(n) for n, t in columns])
    failures = raw.agg(*[F.sum(F.when(F.col(n).isNotNull() &
                        (F.expr(f'try_cast(`{n}` as {t})').isNull() |
                         (~F.col(n).rlike(r'^[+-]?\d{1,5}(\.\d{1,2})?$') if t.startswith('decimal')
                          else F.lit(False))), 1).otherwise(0)).alias(n)
                        for n, t in columns]).first().asDict()
    assert not any(failures.values()), ('Conversion invalide : arrêt sans suppression', failures)
    return converted, failures


def profile(df, table):
    numeric = [f.name for f in df.schema if isinstance(f.dataType, T.NumericType)]
    text = [f.name for f in df.schema if isinstance(f.dataType, T.StringType)]
    metrics = df.agg(F.count('*').alias('rows'),
                     *[F.sum(F.col(n).isNull().cast('long')).alias(n) for n in df.columns]).first().asDict()
    n = metrics.pop('rows')
    extrema = df.agg(*[f(F.col(c)).alias(c+'_'+label) for c in numeric
                       for f, label in [(F.min, 'min'), (F.max, 'max')]]).first().asDict()
    key = 'ss_item_sk' if table == 'store_sales' else 'i_item_sk'
    result = {'rows': n, 'nulls': metrics, 'numeric': numeric, 'text': text,
              'temporal': ['i_rec_start_date', 'i_rec_end_date'] if table == 'item' else [],
              'extrema': extrema, 'distinct_product_keys': df.select(key).distinct().count(),
              'exact_repeated_rows': n-df.distinct().count(),
              'schema': df.schema.jsonValue(), 'scope': 'exhaustif'}
    if table == 'store_sales':
        result['ticket_item_repetitions'] = n-df.select('ss_ticket_number', key).distinct().count()
        result['signed_values'] = df.agg(*[F.sum((F.col(c)<0).cast('long')).alias(c)
                                              for c in ['ss_quantity','ss_net_paid','ss_net_profit']]).first().asDict()
        result['coherence'] = df.agg(
            F.sum((F.col('ss_net_paid_inc_tax') != F.col('ss_net_paid')+F.col('ss_ext_tax')).cast('long')).alias('net_plus_tax_mismatch'),
            F.sum((F.col('ss_ext_sales_price') != F.col('ss_sales_price')*F.col('ss_quantity')).cast('long')).alias('price_quantity_mismatch')).first().asDict()
    else:
        result['domains'] = {c: [r[0] for r in df.select(c).distinct().orderBy(c).collect()]
                             for c in ['i_category', 'i_units', 'i_container']}
        result['date_errors'] = df.agg(*[F.sum((F.col(c).isNotNull() & F.expr(f'try_cast({c} as date)').isNull()).cast('long')).alias(c)
                                        for c in ['i_rec_start_date', 'i_rec_end_date']]).first().asDict()
    return result


def normalize_item(df):
    return df.select(*[(F.trim(F.col(f.name)).alias(f.name) if isinstance(f.dataType, T.StringType)
                        else F.col(f.name)) for f in df.schema]).withColumn(
        'i_rec_start_date', F.to_date('i_rec_start_date', 'yyyy-MM-dd')).withColumn(
        'i_rec_end_date', F.to_date('i_rec_end_date', 'yyyy-MM-dd'))


def parquet_checked(spark, df, path):
    assert path.startswith(('hdfs://hdfs:9000/retail-lake/silver/j3/',
                            'hdfs://hdfs:9000/retail-lake/gold/j3/',
                            'hdfs://hdfs:9000/retail-lake/quality/j3/')), path
    print('PARQUET écriture', path, flush=True)
    before = df.count()
    df.write.mode('errorifexists').option('compression', 'snappy').parquet(path)
    back = spark.read.parquet(path)
    same_types = df.dtypes == back.dtypes
    after = back.count()
    # Deux sommes de fragments SHA-256 contrôlent toutes les lignes, avec un risque théorique de collision.
    def fingerprint(frame):
        hashed = frame.select(F.sha2(F.to_json(F.struct(*frame.columns), {'ignoreNullFields':'false'}),256).alias('hash'))
        return hashed.agg(*[F.sum(F.conv(F.substring('hash',start,15),16,10).cast('decimal(38,0)')).alias('sum'+str(start))
                            for start in [1,50]]).first().asDict()
    fingerprints = {'before':fingerprint(df),'after':fingerprint(back)}
    assert before == after and same_types and fingerprints['before'] == fingerprints['after']
    fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(spark._jsc.hadoopConfiguration())
    content = fs.getContentSummary(spark._jvm.org.apache.hadoop.fs.Path(path))
    return back, {'path': path, 'rows_before': before, 'rows_after': after,
                  'same_names_types': same_types, 'fingerprints': fingerprints,
                  'schema_before': df.schema.jsonValue(), 'schema_after': back.schema.jsonValue(),
                  'bytes': content.getLength(), 'files': content.getFileCount(), 'compression': 'snappy'}
