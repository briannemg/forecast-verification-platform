"""Project-wide configuration settings.

This module stores paths and API settings used throughout the project.
"""

from pathlib import Path

# Root project directory
BASE_DIR = Path(__file__).resolve().parents[1]

# Data storage folders
DATA_DIR = BASE_DIR / "data"

# SQLite database path
DATABASE_PATH = DATA_DIR / "weather_verification.db"

# Locations file path
LOCATIONS_FILE = BASE_DIR / "locations.csv"

# Open-Meteo Forecast URL
OPEN_METEO_HISTORICAL_FORECAST_URL = (
    "https://historical-forecast-api.open-meteo.com/v1/forecast"
)

# Open-Meteo Observations URL
OPEN_METEO_ARCHIVE_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)

# run_pipeline configs
DEFAULT_LOCATION_ID = None