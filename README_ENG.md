# Smart Home Sensor Data Pipeline (MVP)

This repository contains an end-to-end MVP for importing, processing, storing, and serving smart home sensor data via an API, developed as a technical assignment for FoodTracks.


## Architecture & Flow

1. **Import:** Synthetic demo data (CSV) is generated with intentional anomalies.
2. **Process:** Data is loaded and validated using **Polars** for high performance.
3. **Persist:** Cleaned data and quality flags are stored in **PostgreSQL**.
4. **API:** A **FastAPI** application serves both raw and derived data.

## Local Setup Instructions

### Prerequisites
- Python 3.10+ 
- PostgreSQL installed locally

### Installation

1. Clone/unzip the repository and navigate to the root directory.
2. Create and activate a Python virtual environment to keep dependencies isolated:
**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```
**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```
3. Install dependencies: 
```bash
pip install -r requirements.txt
```
4.  Ensure your local PostgreSQL server is running and has a database named `smart_home` created. (Update `DB_URI` in `src/database.py` if your local credentials differ).

### Running The Application End-to-End

1. Genarate Demo Data:
```bash
python src/generator.py
```
(Creates `data/sensor_readings.csv` with 500 records including stuck-at and outlier faults)

2. Start the API Server:
```bash
python -m uvicorn src.api:app --reload
```
3. Interact with the API:
Open your browser and navigate to the interactive Swagger UI:  **http://127.0.0.1:8000/docs**
- **Step 1:** Run the `POST /api/v1/pipeline/run` endpoint to trigger the ETL process and save data to Postgres.
- **Step 2:** Query `GET /api/v1/data/raw` or `GET /api/v1/data/derived`.

## Assumptions, Trade-offs & Decisions

Following the requirement for a pragmatic MVP, the following decisions were made:
- **Frameworks:**  `Polars` was chosen over Pandas for processing due to its speed, strict typing, and native Rust-based performance. `FastAPI` was chosen for the API because of its asynchronous capabilities.
- **Soft Filtering vs. Hard Deletion:** Invalid data is _not_ deleted. Instead, boolean flags (`is_valid`) and string categorizations (`error_reason`) are appended. This allows downstream systems to audit sensor failures without losing historical context.
- **Data Overwrite vs. Append:** The `generator.py` overwrites the CSV on each run to ensure a predictable, reproducible state for the reviewer testing the Data Quality detections.
- **Database Choice:** Native PostgreSQL was used over SQLite to demonstrate production-ready architecture, but Docker was omitted from the final setup to simplify local Windows testing.

## Data Quality Detections

Two specific data quality strategies were implemented in `src/processor.py`:
1. **Stuck-at Fault Detection (Temperature):** 
- _Logic:_ Calculates a rolling standard deviation over a window of 5 readings per sensor. If the standard deviation is exactly `0.0`, the sensor has frozen.
- _Why:_ Hardware/software crashes often result in sensors repeating their last known value indefinitely.
2. **Outlier Detection (CO2 & Temperature):**
-   _Logic:_ Flags physical impossibilities (e.g., CO2 > 5000 ppm, or Temperature > 50°C / < -10°C).
- _Why:_ Identifies sudden hardware spikes or unit-conversion errors without requiring complex machine learning.

## State of the Art Concept

If this MVP were to be scaled to a production environment processing millions of events, the following architectural upgrades would be required:
1. Bigger-than-RAM Processing
- **Streaming Data:** Instead of batch-processing a CSV, sensor data should be ingested via an event streaming platform like **Apache Kafka** or **AWS Kinesis**.
- **Processing Engine:** Polars is excellent, but for distributed processing across clusters, we would migrate to **Apache Spark** or use **Polars' Lazy API** (streaming mode) to process chunks sequentially without loading the entire dataset into memory.
2. Scaling & Ops
- **Containerization & Orchestration:** The API and Processing workers would be fully containerized via Docker and orchestrated using **Kubernetes (K8s)**, allowing horizontal pod autoscaling based on incoming traffic/data volume.
- **Database:** Move from a single PostgreSQL instance to a time-series optimized database like **TimescaleDB** or **InfluxDB**, which handle massive write payloads and time-window aggregations much better.
3. Security
- **API Security:** Implement OAuth2 / JWT authentication for the endpoints.
- **Data Transit:** All IoT data must be transmitted via MQTT over TLS (mTLS) to ensure devices are authenticated before pushing data into the pipeline.
4. Limitations & Next Steps
- Currently, the API triggers the pipeline synchronously. In production, this should be decoupled using a task queue like **Celery** or **Airflow** to prevent HTTP timeouts on large datasets.
- Add comprehensive Unit Testing (`pytest`) for the `processor.py` logic.