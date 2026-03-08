import csv
import random
from datetime import datetime, timedelta
import os

def generate_sensor_data(filepath, num_records=500):
    """Generates synthetic smart home sensor data with intentional faults."""
    
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    start_time = datetime(2026, 3, 1, 12, 0, 0)
    data = []
    
    # Normal baselines
    temp_baseline = 22.0
    co2_baseline = 400.0

    for i in range(num_records):
        timestamp = start_time + timedelta(minutes=i * 5) # Readings every 5 mins
        
        # 1. Temperature Sensor (with "stuck-at" fault)
        if 100 <= i <= 150:
            # INTENTIONAL FAULT: Sensor is stuck at 22.5 for 50 readings
            temp_value = 22.5
        else:
            # Normal fluctuation
            temp_value = temp_baseline + random.uniform(-1.0, 1.0)
            
        data.append({
            "timestamp": timestamp.isoformat(),
            "sensor_id": "temp_living_room_01",
            "sensor_type": "temperature",
            "value": round(temp_value, 2)
        })

        # 2. CO2 Sensor (with "outlier" fault)
        if i == 250:
            # INTENTIONAL FAULT: Massive outlier spike
            co2_value = 50000.0 
        else:
            # Normal fluctuation
            co2_value = co2_baseline + random.uniform(-50, 150)
            
        data.append({
            "timestamp": timestamp.isoformat(),
            "sensor_id": "co2_living_room_01",
            "sensor_type": "co2",
            "value": round(co2_value, 2)
        })

    # Write to CSV
    with open(filepath, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["timestamp", "sensor_id", "sensor_type", "value"])
        writer.writeheader()
        writer.writerows(data)
        
    print(f"Successfully generated {len(data)} sensor readings at {filepath}")

if __name__ == "__main__":
    # Generate the file in the data folder
    generate_sensor_data("../data/sensor_readings.csv")