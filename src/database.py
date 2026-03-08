import polars as pl

# This matches the credentials in our docker-compose.yml
DB_URI = "postgresql://postgres:12345678@localhost:5432/smart_home"

def save_to_postgres(df: pl.DataFrame, table_name: str = "sensor_data"):
    """Saves the processed Polars DataFrame directly to PostgreSQL."""
    
    print(f"Connecting to PostgreSQL and saving data to table '{table_name}'...")
    
    try:
        # Polars handles the table creation and data insertion automatically!
        df.write_database(
            connection=DB_URI,
            table_name=table_name,
            if_table_exists="replace", # For the MVP, we replace the table each run
            engine="adbc"
        )
        print("Data successfully saved to PostgreSQL!")
    except Exception as e:
        print(f"Failed to save to database. Error: {e}")

if __name__ == "__main__":
    # A quick test to ensure it works
    # We import the processor we wrote earlier
    from processor import process_sensor_data
    
    df = process_sensor_data("../data/sensor_readings.csv")
    save_to_postgres(df)