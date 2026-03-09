import os
import polars as pl
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
port = os.getenv("DB_PORT")

DB_URI = f"postgresql://{user}:{password}@localhost:{port}/smart_home"

#Save processed data to db
def save_to_postgres(df: pl.DataFrame, table_name: str = "sensor_data"):
    """Saves the processed Polars DataFrame directly to PostgreSQL."""
    
    print(f"Connecting to PostgreSQL and saving data to table '{table_name}'...")
    
    try:
        # Polars handles the table creation and data insertion automatically
        df.write_database(
            connection=DB_URI,
            table_name=table_name,
            if_table_exists="replace", # we replace the table each run
            engine="adbc"
        )
        print("Data successfully saved to PostgreSQL!")
    except Exception as e:
        print(f"Failed to save to database. Error: {e}")

if __name__ == "__main__":

    from processor import process_sensor_data
    
    df = process_sensor_data("../data/sensor_readings.csv")
    save_to_postgres(df)