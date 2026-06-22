"""Functions for retrieving historical weather data from Open-Meteo."""

import requests

from src.config import (
    OPEN_METEO_ARCHIVE_URL,
    OPEN_METEO_HISTORICAL_FORECAST_URL,
)

def get_json(url: str, params: dict) -> dict:
    """Send GET requests and return the JSON response.

    Parameters
    ----------
    url : str
        API endpoint to request.
    params : dict
        Query parameters to include in the API request.

    Returns
    -------
    dict
        Parsed JSON response from the API.

    Raises
    ------
    requests.HTTPError
        Raised if the API request returns an unsuccessful status code.
    """

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    return response.json()

def get_historical_forecast(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> dict:
    """Retrieve historical forecast temperature data.

    Parameters
    ----------
    latitude : float
        Latitude coordinate.
    longitude : float
        Longitude coordinate.
    start_date : str
        Start date in YYYY-MM-DD format.
    end_date : str
        End date in YYYY-MM-DD format.

    Returns
    -------
    dict
        Historical forecast API response.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m",
        "temperature_unit": "fahrenheit",
        "timezone": "UTC",
    }
    
    return get_json(OPEN_METEO_HISTORICAL_FORECAST_URL, params)

def get_historical_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> dict:
    """Retrieve historical observed/reanalysis temperature data.

    Parameters
    ----------
    latitude : float
        Latitude coordinate.
    longitude : float
        Longitude coordinate.
    start_date : str
        Start date in YYYY-MM-DD format.
    end_date : str
        End date in YYYY-MM-DD format.

    Returns
    -------
    dict
        Historical weather API response.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m",
        "temperature_unit": "fahrenheit",
        "timezone": "UTC",
    }
    
    return get_json(OPEN_METEO_ARCHIVE_URL, params)