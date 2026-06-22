"""Project-wide configuration settings.

This module stores paths and API settings used throughout the project.
"""

from pathlib import Path

# Root project directory
BASE_DIR = Path(__file__).resolve().parents[1]

# Data storage folders
DATA_DIR = BASE_DIR / "data"

# SQLite database path
DATABASE_PATH = BASE_DIR / "weather_verification.db"

# National Weather Service API base URL
NWS_BASE_URL = "https://api.weather.gov"

# Required headers for API requests
HEADERS = {
    "User-Agent": "weather-verification-platform (github portfolio project)",
    "Accept": "application/geo+json",
}