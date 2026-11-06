import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType
from pymongo import MongoClient, UpdateOne

load_dotenv()

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "air-quality")
MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
DB_NAME = os.getenv("MONGODB_DATABASE", "air_quality_db")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION", "measurements")
CHECKPOINT = os.getenv("SPARK_CHECKPOINT_DIR", "file:///D:/AirQualityMonitoring/checkpoints/air-quality")

if not MONGODB_URI:
    raise SystemExit("MONGODB_URI is missing from .env")

schema = StructType([
    StructField("measurement_id", StringType()),
    StructField("location_id", LongType()),
    StructField("location_name", StringType()),
    StructField("country", StringType()),
    StructField("latitude", DoubleType()),
    StructField("longitude", DoubleType()),
    StructField("sensor_id", LongType()),
    StructField("parameter", StringType()),
    StructField("value", DoubleType()),
    StructField("unit", StringType()),
    StructField("datetime_utc", StringType()),
    StructField("source", StringType()),
    StructField("ingested_at", StringType()),
])

def write_to_mongodb(batch_df, batch_id):
    rows = batch_df.toJSON().collect()
    if not rows:
        print(f"Batch {batch_id}: no records")
        return
    import json
    docs = [json.loads(row) for row in rows]
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    collection = client[DB_NAME][COLLECTION_NAME]
    operations = [
        UpdateOne({"measurement_id": doc["measurement_id"]},
                  {"$setOnInsert": doc}, upsert=True)
        for doc in docs if doc.get("measurement_id")
    ]
    if operations:
        result = collection.bulk_write(operations, ordered=False)
        print(f"Batch {batch_id}: received={len(docs)}, inserted={result.upserted_count}, existing={result.matched_count}")
    client.close()

spark = (
    SparkSession.builder
    .appName("AirQualityKafkaSpark")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

stream = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", BOOTSTRAP)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "latest")
    .option("failOnDataLoss", "false")
    .load()
)

parsed = (
    stream.select(from_json(col("value").cast("string"), schema).alias("data"))
    .select("data.*")
    .filter(col("measurement_id").isNotNull())
)

query = (
    parsed.writeStream
    .foreachBatch(write_to_mongodb)
    .option("checkpointLocation", CHECKPOINT)
    .start()
)

print(f"Spark is consuming Kafka topic '{TOPIC}' and writing to MongoDB.")
query.awaitTermination()
