"""Data ingestion pipeline for the forecast verification platform.

This module retrieves historical forecast data and corresponding
historical weather observations from the Open-Meteo API and loads
normalized records into the project SQLite database.

The ingestion workflow includes:

- Reading configured analysis locations
- Retrieving archived forecast temperature data
- Retrieving historical observed weather data
- Loading normalized forecast records into the forecasts table
- Loading normalized observed weather records into the observations table
- Preparing matched datasets for downstream verification analysis

The resulting database serves as the foundation for forecast skill
evaluation, including bias, mean absolute error (MAE), root mean
square error (RMSE), and future visualization workflows.
"""

from datetime import datetime, timezone

import pandas as pd

from src.config import LOCATIONS_FILE
from src.database import get_connection
from src.open_meteo_api import get_historical_forecast, get_historical_weather

START_DATE = "2026-06-01"
END_DATE = "2026-06-15"

def load_location(row: pd.Series) -> None:
    """Load historical forecast and observed weather data for one location.

    Parameters
    ----------
    row : pd.Series
        Location configuration row from locations.csv
        
    Returns
    -------
    None
    """
    retrieved_at = datetime.now(timezone.utc).isoformat()
    
    location_id = row["location_id"]
    latitude = row["latitude"]
    longitude = row["longitude"]
    
    forecast_data = get_historical_forecast(
        latitude=latitude,
        longitude=longitude,
        start_date=START_DATE,
        end_date=END_DATE,
    )
    
    observed_data = get_historical_weather(
        latitude=latitude,
        longitude=longitude,
        start_date=START_DATE,
        end_date=END_DATE,
    )
    
    forecast_df = pd.DataFrame(
        {
            "valid_time": forecast_data["hourly"]["time"],
            "temperature_f": forecast_data["hourly"]["temperature_2m"],
        }
    )
    
    observed_df = pd.DataFrame(
        {
            "valid_time": observed_data["hourly"]["time"],
            "temperature_f": observed_data["hourly"]["temperature_2m"],
        }
    )
    
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO locations
            (location_id, name, latitude, longitude, timezone)
            VALUES (?, ?, ?, ?, ?)
            """,
            (location_id, row["name"], latitude, longitude, row["timezone"]),
        )
        
        for _, forecast in forecast_df.iterrows():
            connection.execute(
                """
                INSERT INTO forecasts
                (location_id, valid_time, temperature_f, retrieved_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    location_id,
                    forecast["valid_time"],
                    forecast["temperature_f"],
                    retrieved_at,
                ),
            )
            
        for _, observation in observed_df.iterrows():
            connection.execute(
                """
                INSERT INTO observations
                (location_id, valid_time, temperature_f, retrieved_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    location_id,
                    observation["valid_time"],
                    observation["temperature_f"],
                    retrieved_at,
                ),
            )
            
    print(f"Loaded location: {location_id}")
    print(f"Forecast rows: {len(forecast_df)}")
    print(f"Observed rows: {len(observed_df)}")
    
def load_locations(location_id: str | None = None) -> None:
    """Load historical forecast and observed weather data.
    
    Parameters
    ----------
    location_id : str or None, optional
        Specific location_id to process. If None, all configured locations
        are processed.
        
    Returns
    -------
    None
    """
    locations = pd.read_csv(LOCATIONS_FILE)
    
    if location_id is not None:
        locations = locations[locations["location_id"] == location_id]
        
        for _, row in locations.iterrows():
            load_location(row)
            
def main() -> None:
    """Load forecast and observation data for all configured locations."""
    load_locations()
            
            
if __name__ == "__main__":
   main()