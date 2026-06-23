"""Forecast verification engine for historical forecast evaluation.

This module matches archived forecast data with corresponding historical
weather records by valid time and calculates basic forecast performance
metrics.

The verification workflow includes:

- Matching forecast and observed values by location and valid time
- Calculating forecast error for each hourly record
- Computing aggregate verification statistics
- Storing normalized verification results for analysis

Supported verification metrics currently include forecast bias, mean
absolute error (MAE), and root mean square error (RMSE).
"""

import pandas as pd

from src.config import LOCATIONS_FILE
from src.database import get_connection

def calculate_temperature_verification(location_id: str) -> pd.DataFrame:
    """Calculate temperature forecast errors for one location.

    Parameters
    ----------
    location_id : str
        Configured location identifier.

    Returns
    -------
    pd.DataFrame
        Matched forecast and observation records with error calculations.
    """
    with get_connection() as connection:
        forecasts = pd.read_sql_query(
            """
            SELECT location_id, valid_time, temperature_f
            FROM forecasts
            WHERE location_id = ?
            """,
            connection,
            params=(location_id,),
        )
        
        observations = pd.read_sql_query(
            """
            SELECT location_id, valid_time, temperature_f
            FROM observations
            WHERE location_id = ?
            """,
            connection,
            params=(location_id,),
        )
        
    forecasts["valid_time"] = pd.to_datetime(forecasts["valid_time"])
    observations["valid_time"] = pd.to_datetime(observations["valid_time"])
    
    matched = forecasts.merge(
        observations,
        on=["location_id", "valid_time"],
        suffixes=("_forecast", "_observed"),
    )
    
    matched = matched.dropna(
        subset=["temperature_f_forecast", "temperature_f_observed"]
    )
    
    matched["error_f"] = (
        matched["temperature_f_forecast"] - matched["temperature_f_observed"]
    )
    matched["absolute_error_f"] = matched["error_f"].abs()
    matched["squared_error_f"] = matched["error_f"] ** 2
    
    return matched

def save_verification_results(location_id: str, results: pd.DataFrame) -> None:
    """Save verification results to the database.

    Parameters
    ----------
    location_id : str
        Configured location identifier.
    results : pd.DataFrame
        Verification results returned by calculate_temperature_verification.
        
    Returns
    -------
    None
    """
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM verification_results WHERE location_id = ?",
            (location_id,),
        )
        
        for _, row in results.iterrows():
            connection.execute(
                """
                INSERT INTO verification_results
                (location_id, valid_time, forecast_temperature_f,
                observed_temperature_f, error_f, absolute_error_f,
                squared_error_f)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    location_id,
                    row["valid_time"].isoformat(),
                    row["temperature_f_forecast"],
                    row["temperature_f_observed"],
                    row["error_f"],
                    row["absolute_error_f"],
                    row["squared_error_f"],
                ),
            )
            
def summarize_verification(results: pd.DataFrame) -> None:
    """Print summary verification metrics.

    Parameters
    ----------
    results : pd.DataFrame
        Verification results with forecast and observed temperatures.
        
    Returns
    -------
    None
    """
    if results.empty:
        print("No matched forecast/observation pairs found.")
        return
    
    bias = results["error_f"].mean()
    mae = results["absolute_error_f"].mean()
    rmse = (results["squared_error_f"].mean()) ** 0.5
    
    print(f"Matched pairs: {len(results)}")
    print(f"Bias: {bias:.2f} °F")
    print(f"MAE:  {mae:.2f} °F")
    print(f"RMSE: {rmse:.2f} °F")
    
def run_verification(location_id: str | None = None) -> None:
    """Run verification for one location or all configured locations.
    
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
        
    for current_location_id in locations["location_id"]:
        results = calculate_temperature_verification(current_location_id)
        save_verification_results(current_location_id, results)
        summarize_verification(results)
    
def main() -> None:
    """Run forecast verification for all configured locations."""
    run_verification()
    
    
if __name__ == "__main__":
    main()