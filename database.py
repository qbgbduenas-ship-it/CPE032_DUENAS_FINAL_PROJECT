import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

mongo_uri = os.getenv("MONGODB_URI")
database_name = os.getenv("MONGODB_DATABASE", "air_quality_db")

if not mongo_uri:
    raise RuntimeError("MONGODB_URI is missing from .env")

client = MongoClient(mongo_uri, serverSelectionTimeoutMS=15000)
db = client[database_name]
measurements = db["measurements"]
aggregates = db["aggregates"]


def get_all_measurements():
    return list(
        measurements.find({}, {"_id": 0})
        .sort("measurement_time", -1)
    )


def get_latest_measurements(limit=100):
    return list(
        measurements.find({}, {"_id": 0})
        .sort("measurement_time", -1)
        .limit(limit)
    )


def get_aggregates():
    return list(
        aggregates.find({}, {"_id": 0})
        .sort("window_start", -1)
    )


def test_connection():
    client.admin.command("ping")
    print(f"Connected to MongoDB database '{database_name}'.")


if __name__ == "__main__":
    test_connection()
    client.close()
