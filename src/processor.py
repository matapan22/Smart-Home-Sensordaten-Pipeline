import polars as pl
import os

def process_sensor_data(file_path: str) -> pl.DataFrame:
    """Reads, normalizes, and applies quality checks to sensor data."""
    
    # 1. Import DataFile
    print(f"Reading data from {file_path}...")
    df = pl.read_csv(file_path)
    
    # 2. Normalization: Convert timestamp strings to actual datetime objects
    df = df.with_columns(
        pl.col("timestamp").str.to_datetime()
    )
    
    # Ensure data is sorted chronologically per sensor for our window functions
    df = df.sort(["sensor_id", "timestamp"])
    
    # 3. Quality Check 1: Stuck-at fault
    # Calculate rolling standard deviation over 5 readings. If it's 0.0, the value is stuck.
    df = df.with_columns(
        pl.col("value")
        .rolling_std(window_size=5)
        .over("sensor_id")
        .fill_null(1.0) # Fill the first 4 rows with >0 so they aren't incorrectly flagged
        .alias("temp_rolling_std")
    )
    
    # 4. Apply the Quality Flags (Detection) 
    df = df.with_columns(
        is_stuck=(pl.col("temp_rolling_std") == 0.0),
        is_outlier=(
            ((pl.col("sensor_type") == "co2") & (pl.col("value") > 5000.0)) |
            ((pl.col("sensor_type") == "temperature") & ((pl.col("value") < -10.0) | (pl.col("value") > 50.0)))
        )
    )
    
    # 5. Create a final 'is_valid' flag and an 'error_reason'
    df = df.with_columns(
        is_valid=~(pl.col("is_stuck") | pl.col("is_outlier")),
        error_reason=pl.when(pl.col("is_outlier")).then(pl.lit("outlier_detected"))
                       .when(pl.col("is_stuck")).then(pl.lit("stuck_at_fault"))
                       .otherwise(pl.lit(None))
    ).drop("temp_rolling_std") # Clean up our temporary calculation column
    
    return df

if __name__ == "__main__":

    processed_data = process_sensor_data("../data/sensor_readings.csv")
    
    print("\n--- Processing Complete ---")
    print(f"Total records: {processed_data.height}")
    
    # Filter and show only the invalid data
    invalid_data = processed_data.filter(~pl.col("is_valid"))
    print(f"\nFound {invalid_data.height} records with data quality issues:")
    print(invalid_data)