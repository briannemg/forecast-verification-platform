"""Functions for interacting with the National Weather Service API.

This module handles API communication with the National Weather Service
to retrieve forecast metadata, available observation station, and
identify the nearest station for a given geographic location.
"""

import math
import requests

from src.config import HEADERS, NWS_BASE_URL

def get_json(url: str) -> dict:
    """Send GET requests and return the JSON response.

    Parameters
    ----------
    url : str
        API endpoint to request.

    Returns
    -------
    dict
        Parsed JSON response from the API.
        
    Raises
    ------
    requests.HTTPError
        Raised if the API request returns an unsuccessful status code.
    """
    
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    
    return response.json()


def get_point_metadata(latitude: float, longitude: float) -> dict:
    """Retrieve metadata for a geographic point.
    
    This endpoint tells us:
    - forecast URL
    - observation station URL
    - forecast office/grid information

    Parameters
    ----------
    latitude : float
        Latitude coordinate of requested location.
    longitude : float
        Longitude coordinate of requested location.

    Returns
    -------
    dict
        JSON metadata response containing forecast and station URLs.
    """
    
    url = f"{NWS_BASE_URL}/points/{latitude},{longitude}"
    
    return get_json(url)


def get_observation_stations(latitude: float, longitude: float) -> list:
    """Retrieve available observation stations for a location.
    
    Uses the point metadata endpoint to retrieve a list of observation
    stations associated with the requested location.

    Parameters
    ----------
    latitude : float
        Latitude coordinate of requested location.
    longitude : float
        Longitude coordinate of requested location.

    Returns
    -------
    list
        List of station metadata dictionaries returned by the API.
    """
    
    metadata = get_point_metadata(latitude, longitude)
    
    station_url = metadata["properties"]["observationStations"]
    
    stations = get_json(station_url)
    
    return stations["features"]


def get_hourly_forecast(latitude: float, longitude: float) -> list:
    """Retrive hourly forecast data for a location.
    
    Uses the point metadata endpoint to identify the appropriate
    forecast endpoint and retrieves hourly forecast periods.

    Parameters
    ----------
    latitude : float
        Latitude coordinate of requested location.
    longitude : float
        Longitude coordinate of requested location.

    Returns
    -------
    list
        List of hourly forecast period dictionaries.
    """
    
    metadata = get_point_metadata(latitude, longitude)
    
    forecast_url = metadata["properties"]["forecastHourly"]
    
    forecast = get_json(forecast_url)
    
    return forecast["properties"]["periods"]


def haversine_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """Calculate distance between two geographic coordinates.
    
    Uses the Haversine formula to calculate great-circle distance
    between two latitude/longitude points on Earth.

    Parameters
    ----------
    lat1 : float
        Latitude of the first point.
    lon1 : float
        Longitude of the first point.
    lat2 : float
        Latitude of the second point.
    lon2 : float
        Longitude of the second point.

    Returns
    -------
    float
        Distance between points in kilometers.
    """
    
    radius = 6371.0
    
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return radius * c


def select_nearest_station(latitude: float, longitude: float) -> dict:
    """Find the nearest available observation station.
    
    Retrieves all observation stations associated with a requested
    location, calculates the distance to each station, and returns
    the nearest available station.

    Parameters
    ----------
    latitude : float
        Latitude coordinate of requested location.
    longitude : float
        Longitude coordinate of requested location.

    Returns
    -------
    dict
        Dictionary containing metadata for the nearest station.
        
        Keys include:
        - station_id
        - name
        - distance_km
        - latitude
        - longitude
    """
    
    stations = get_observation_stations(latitude, longitude)
    
    station_distances = []
    for station in stations:
        props = station["properties"]
        
        # GeoJSON coordinate order is [longitude, latitude]
        station_lon, station_lat = station["geometry"]["coordinates"][:2]
        
        distance = haversine_km(
            latitude,
            longitude,
            station_lat,
            station_lon
        )
        
        station_distances.append(
            {
                "station_id": props["stationIdentifier"],
                "name": props["name"],
                "distance_km": distance,
                "latitude": station_lat,
                "longitude": station_lon,
            }
        )
        
    nearest_station = min(
        station_distances,
        key=lambda x: x["distance_km"]
    )
    
    return nearest_station


def get_station_observations(
    station_id: str,
    limit: int = 100
) -> list:
    """Retrieve recent weather observations for a station.
    
    Queries the National Weather Service station observations endpoint
    and returns recent weather observations for a specific station.

    Parameters
    ----------
    station_id : str
        Station identifier (example: KDEN).
    limit : int, optional
        Maximum number of observations to retrieve.
        Default is 100.

    Returns
    -------
    list
        List of observation dictionaries returned by the API.
    """
    
    url = (
        f"{NWS_BASE_URL}/stations/"
        f"{station_id}/observations?limit={limit}"
    )
    
    observations = get_json(url)
    
    return observations["features"]