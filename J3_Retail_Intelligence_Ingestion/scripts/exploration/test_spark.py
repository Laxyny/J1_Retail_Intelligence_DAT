import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from uc06 import session, save, parquet_checked, F

spark = session('UC06-validation-environnement')
print('Python', sys.version, 'Spark', spark.version)
print('Java', spark._jvm.java.lang.System.getProperty('java.version'))
print('Hadoop client Spark', spark._jvm.org.apache.hadoop.util.VersionInfo.getVersion())
source = 'hdfs://hdfs:9000/retail-lake/raw/tpcxbb/initial/reason.dat'
df = spark.read.option('sep','|').schema('reason_sk long, reason_id string, description string').csv(source)
df.printSchema()
df.show(3, truncate=60)
result = df.withColumn('description', F.trim('description'))
back, evidence = parquet_checked(spark, result,
    'hdfs://hdfs:9000/retail-lake/quality/j3/smoke-'+uuid.uuid4().hex[:12])
assert back.count() == 35
evidence.update(spark=spark.version, python=sys.version,
                java=spark._jvm.java.lang.System.getProperty('java.version'),
                hadoop_client=spark._jvm.org.apache.hadoop.util.VersionInfo.getVersion(), source=source)
save('preuves/controles/J3-P02-session-spark.json',evidence)
print('VALIDATION SPARK REUSSIE', evidence)
spark.stop()
