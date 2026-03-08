from fastapi import FastAPI, HTTPException
import polars as pl
import os

# Import our previous modules
from processor import process_sensor_data
from database import save_to_postgres, DB_URI

app = FastAPI(
    title="Smart Home Sensor API",
    description="MVP for importing, processing, and serving sensor data."
)

DATA_FILE = "../data/sensor_readings.csv"

@app.post("/api/v1/pipeline/run", summary="Run the ETL Pipeline")
def run_pipeline():
    """Reads the CSV, processes data (adds quality flags), and saves to PostgreSQL."""
    if not os.path.exists(DATA_FILE):
        raise HTTPException(status_code=404, detail="Demo data file not found. Run generator.py first.")
    
    try:
        # 1. Process
        df = process_sensor_data(DATA_FILE)
        # 2. Persist
        save_to_postgres(df, table_name="sensor_data")
        
        return {
            "status": "success",
            "message": "Pipeline executed successfully.",
            "rows_processed": df.height
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/data/raw", summary="Get stored raw data")
def get_raw_data(limit: int = 100):
    """Retrieves the stored data from PostgreSQL."""
    query = f"SELECT * FROM sensor_data LIMIT {limit}"
    try:
        # Polars can read directly from the database!
        df = pl.read_database_uri(query, DB_URI, engine="adbc")
        # Convert DataFrame to a list of dictionaries for the JSON response
        return df.to_dicts()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error. Did you run the pipeline first?")

@app.get("/api/v1/data/derived", summary="Get insights and aggregations")
def get_derived_data():
    """Retrieves aggregated insights and counts of data quality issues."""
    query = "SELECT * FROM sensor_data"
    try:
        df = pl.read_database_uri(query, DB_URI, engine="adbc")
        
        # Calculate derived insights using Polars
        total_records = df.height
        valid_records = df.filter(pl.col("is_valid")).height
        error_counts = df.group_by("error_reason").len().drop_nulls().to_dicts()

        # Extract the actual rows that contain errors
        # The tilde (~) operator in Polars means "NOT"
        error_rows = df.filter(~pl.col("is_valid")).to_dicts()
        
        # Calculate average values for valid data only
        valid_df = df.filter(pl.col("is_valid"))
        averages = valid_df.group_by("sensor_type").agg(
            pl.col("value").mean().round(2).alias("average_value")
        ).to_dicts()

        return {
            "total_records": total_records,
            "valid_records": valid_records,
            "data_quality_issues": error_counts,
            "insights": averages,
            "error_records": error_rows
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))