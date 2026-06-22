"""Data ingestion pipeline for the weather verification platform.

This module retrieves forecast data and recent weather observations
from the National Weather Service API and loads normalized records
into the project SQLite database.

The ingestion workflow includes:

- Reading configured test locations
- Identifying nearest observation stations
- Retrieving hourly forecast data
- Retrieving recent station observations
- Storing normalized records for later verification analysis
"""

from datetime import datetime, timezone

import pandas as pd

from src.database import get_connection
from src.nws_api import (
    get_hourly_forecast,
    get_station_observations,
    select_nearest_station,
)

def celsius_to_fahrenheit(temperature_c: float | None) -> float | None:
    """Convert temperature from Celsius to Fahrenheit.

    Parameters
    ----------
    temperature_c : float or None
        Temperature value in degrees Celsius.

    Returns
    -------
    float or None
        Temperature converted to degrees Fahrenheit.
        Returns None if the input value is None.
    """
    if temperature_c is None:
        return None
    
    return temperature_c * 9 / 5 + 32

def load_location(row: pd.Series) -> None:
    """Load forecast and observation data for a single location.
    
    Retrieves forecast data and recent weather observations for a
    configured location, identifies the nearest observation station,
    and stores all retrieved data in the project database.
    
    Data written to the database includes:
    
    - Location metadata
    - Observation station metadata
    - Location-to-station mapping
    - Hourly forecast records
    - Recent station observation records
    
    Parameters
    ----------
    row : pandas.Series
        Row from the locations.csv configuration file containing:
        
        - location_id
        - name
        - latitude
        - longitude
        - timezone
        
    Returns
    -------
    None
    """
    retrieved_at = datetime.now(timezone.utc).isoformat()
    
    location_id = row["location_id"]
    latitude = row["latitude"]
    longitude = row["longitude"]
    
    # Retrieve forecast and observation data from NWS API
    station = select_nearest_station(latitude, longitude)
    forecasts = get_hourly_forecast(
        station["latitude"],
        station["longitude"],
    )
    observations = get_station_observations(station["station_id"])
    
    # Open database connection and store normalized records
    with get_connection() as connection:
        
        # Store location metadata
        connection.execute(
            """
            INSERT OR REPLACE INTO locations
            (location_id, name, latitude, longitude, timezone)
            VALUES (?, ?, ?, ?, ?)
            """,
            (location_id, row["name"], latitude, longitude, row["timezone"]),
        )
        
        # Store station metadata
        connection.execute(
            """
            INSERT OR REPLACE INTO stations
            (station_id, name, latitude, longitude)
            VALUES (?, ?, ?, ?)
            """,
            (
                station["station_id"],
                station["name"],
                station["latitude"],
                station["longitude"],
            ),
        )
        
        # Connect location and station data
        connection.execute(
            """
            INSERT OR REPLACE INTO location_stations
            (location_id, station_id, distance_km, selected_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                location_id,
                station["station_id"],
                station["distance_km"],
                retrieved_at,
            ),
        )
        
        # Store forecast records
        for period in forecasts:
            connection.execute(
                """
                INSERT INTO forecasts
                (location_id, generated_at, valid_time, lead_time_hours,
                temperature_f, wind_speed, wind_direction, short_forecast,
                detailed_forecast, retrieved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    location_id,
                    retrieved_at,
                    period["startTime"],
                    None,
                    period.get("temperature"),
                    period.get("windSpeed"),
                    period.get("windDirection"),
                    period.get("shortForecast"),
                    period.get("detailedForecast"),
                    retrieved_at,
                ),
            )
            
        # Store observation records
        for obs in observations:
            props = obs["properties"]
            temperature_c = props.get("temperature", {}).get("value")
            
            connection.execute(
                """
                INSERT INTO observations
                (station_id, valid_time, temperature_c, temperature_f,
                text_description, retrieved_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    station["station_id"],
                    props.get("timestamp"),
                    temperature_c,
                    celsius_to_fahrenheit(temperature_c),
                    props.get("textDescription"),
                    retrieved_at,
                ),
            )
            
    print(f"Loaded location: {location_id}")
    print(f"Nearest station: {station['station_id']} - {station['name']}")
    print(f"Distance: {station['distance_km']:.2f} km")
    
def main(location_id: str | None = None) -> None:
    """Load data for onfigured locations.
    
    Reads configured locations from locations.csv and executes the
    data ingestion pipeline for each location.
    
    If a specific location_id is provided, only that location is
    processed. Otherwise, all configured locations are loaded.
    
    Parameters
    ----------
    location_id : str or None, optional
        Identifier of a specific location to process.
        If None, all configured locations are processed.
        
    Returns
    -------
    None
    """
    locations = pd.read_csv("locations.csv")
    
    if location_id is not None:
        locations = locations[locations["location_id"] == location_id]
        
    for _, row in locations.iterrows():
        load_location(row)
        
        
if __name__ == "__main__":
    main("central_kansas_test")