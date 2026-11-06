# Air Quality Monitoring System

A Big Data application using the required **OpenAQ API → Python Producer → Kafka → Spark → MongoDB → Streamlit** pipeline.

## Important architecture note

Streamlit and MongoDB alone do not meet the activity requirement. Kafka must act as the message broker and Spark must process the stream. VS Code is the development environment, not a replacement for those services.

## Project files

- `producer.py` — reads current measurements from OpenAQ API v3 and publishes JSON events to Kafka.
- `spark_consumer.py` — consumes Kafka events with Spark Structured Streaming and upserts them into MongoDB.
- `app.py` — Streamlit live dashboard, history, analytics, CSV/Excel/PDF exports.
- `api_test.py` — checks OpenAQ API access.
- `.env.example` — configuration template.

## Requirements

- Windows 10/11
- Python 3.11
- Java 17 (required by this tested Spark/Kafka setup)
- Apache Kafka broker (KRaft mode)
- MongoDB Atlas database or a reachable MongoDB server
- OpenAQ API v3 key

## Setup in VS Code

1. Extract this project to `D:\AirQualityMonitoring`.
2. Open that folder in VS Code.
3. Open Terminal → New Terminal (PowerShell).
4. Create and activate the environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

5. Create your local configuration:

```powershell
Copy-Item .env.example .env
notepad .env
```

6. Add your OpenAQ API key and MongoDB connection string. Never upload `.env` to GitHub.

## OpenAQ API key

Create an OpenAQ account and obtain an API key from the OpenAQ platform. Add the key to `OPENAQ_API_KEY` in `.env`. API v3 requests use the `X-API-Key` header.

Test the key:

```powershell
python api_test.py
```

The sample coordinates are Metro Manila. Change `OPENAQ_LATITUDE`, `OPENAQ_LONGITUDE`, and `OPENAQ_RADIUS_METERS` in `.env` if you want another area. OpenAQ coverage depends on available stations and sensors; a location search may return no results.

## Kafka and Java

Install Java 17 and Apache Kafka separately. VS Code can run the commands, but it does not bundle the Kafka broker or Java runtime.

Set `JAVA_HOME` to your Java 17 installation and add `%JAVA_HOME%\bin` to PATH. Confirm:

```powershell
java -version
```

Set `KAFKA_HOME` to the extracted Kafka folder, for example `D:\kafka`. In a PowerShell terminal:

```powershell
$env:KAFKA_HOME = "D:\kafka"
& "$env:KAFKA_HOME\bin\windows\kafka-storage.bat" random-uuid
```

Copy the generated UUID, then format the storage directory (only for a fresh Kafka data directory):

```powershell
& "$env:KAFKA_HOME\bin\windows\kafka-storage.bat" format -t YOUR_GENERATED_UUID -c "$env:KAFKA_HOME\config\server.properties"
```

Start the broker in its own terminal:

```powershell
& "$env:KAFKA_HOME\bin\windows\kafka-server-start.bat" "$env:KAFKA_HOME\config\server.properties"
```

Keep that terminal open. Kafka 4.x uses KRaft and does not require ZooKeeper. If your Kafka distribution has a different folder layout, inspect its `bin` and `config` directories before running the commands.

## Run the application (four terminals)

All terminals should be opened in `D:\AirQualityMonitoring` and have `.venv` activated.

**Terminal 1 — Kafka broker:** use the Kafka start command above.

**Terminal 2 — OpenAQ producer:**

```powershell
python producer.py
```

**Terminal 3 — Spark consumer:**

```powershell
$env:JAVA_HOME = "YOUR_JAVA_17_FOLDER"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5 spark_consumer.py
```

Replace `YOUR_JAVA_17_FOLDER` with the actual Java installation directory. The first run downloads the Spark Kafka connector package. Keep this terminal open.

**Terminal 4 — Streamlit dashboard:**

```powershell
streamlit run app.py
```

Streamlit normally opens `http://localhost:8501`.

## Pipeline test order

1. Confirm `python api_test.py` returns HTTP 200 and at least one location.
2. Start Kafka and confirm the broker stays running.
3. Start `producer.py` and check its `sent N measurements` messages.
4. Start `spark_consumer.py` and check batch insert messages.
5. Open MongoDB Atlas and verify the `air_quality_db.measurements` collection.
6. Open Streamlit and inspect Live Dashboard, History, and Analytics.

## Notes

- OpenAQ returns measurements only where stations and sensors report data. The sample location is not guaranteed to have nearby active stations.
- The producer polls every 60 seconds by default. The dashboard refreshes every 15 seconds.
- “Live” means the dashboard refreshes frequently from the latest records stored in MongoDB; it does not guarantee a new sensor measurement every 15 seconds.
- Spark uses an idempotent MongoDB upsert keyed by `measurement_id` to reduce duplicate records.
- The PDF export includes up to the first 500 filtered records to keep reports manageable.
- Do not use the dashboard as an official safety alert or regulatory AQI service.

## Discussion outline

**API:** OpenAQ API v3 provides measurements reported by air quality monitoring stations. The application retrieves available pollutant readings and their location, value, unit, and timestamp.

**Pipeline:** The Python producer obtains measurements from OpenAQ and publishes events to Kafka. Spark Structured Streaming consumes and parses those events, then writes them to MongoDB. Streamlit reads the stored records and displays live readings, historical data, and analytics.

**Significance:** The dashboard makes environmental measurements easier to inspect over time. Historical records and aggregation help users compare locations and observe pollutant trends, supporting environmental awareness and data-informed decisions.
