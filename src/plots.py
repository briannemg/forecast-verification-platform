"""Visualizion utilities for forecast verification analysis."""

import matplotlib.pyplot as plt
import pandas as pd

from src.database import get_connection

def load_verification_data(location_id: str) -> pd.DataFrame:
    """Load verification results from the database.

    Parameters
    ----------
    location_id : str
        Configured location identifier.

    Returns
    -------
    pd.DataFrame
        Verification results dataframe.
    """
    with get_connection() as connection:
        data = pd.read_sql_query(
            """
            SELECT *
            FROM verification_results
            WHERE location_id = ?
            ORDER BY valid_time
            """,
            connection,
            params=(location_id,),
        )
        
    data["valid_time"] = pd.to_datetime(data["valid_time"])
    
    return data

def plot_forecast_vs_observed(location_id: str) -> None:
    """Plot forecast and observed temperatures."""
    data = load_verification_data(location_id)
    
    plt.figure(figsize=(12, 6))
    
    plt.plot(
        data["valid_time"],
        data["forecast_temperature_f"],
        label="Forecast",
    )
    
    plt.plot(
        data["valid_time"],
        data["observed_temperature_f"],
        label="Observed",
    )
    
    plt.xlabel("Date")
    plt.ylabel("Temperature (°F)")
    plt.title("Forecast vs Observed Temperature")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    plt.savefig(
        f"dashboard/{location_id}_forecast_vs_observed.png",
        dpi=150,
    )
    
    plt.close()
    
def plot_error_timeseries(location_id: str) -> None:
    """Plot forecast error over time."""
    data = load_verification_data(location_id)
    
    plt.figure(figsize=(12, 6))
    
    plt.plot(
        data["valid_time"],
        data["error_f"],
    )
    
    plt.axhline(0)
    
    plt.xlabel("Date")
    plt.ylabel("Forecast Error (°F)")
    plt.title("Forecast Error Over Time")
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    plt.savefig(
        f"dashboard/{location_id}_error_timeseries.png",
        dpi=150
    )
    
    plt.close()
    
def plot_metrics(location_id: str) -> None:
    """Plot summary verification metrics."""
    data = load_verification_data(location_id)
    
    bias = data["error_f"].mean()
    mae = data["absolute_error_f"].mean()
    rmse = (data["squared_error_f"].mean()) ** 0.5
    
    metrics = ["Bias", "MAE", "RMSE"]
    values = [bias, mae, rmse]
    
    plt.figure(figsize=(8, 5))
    
    plt.bar(metrics, values)
    
    plt.ylabel("Temperature Error (°F)")
    plt.title("Verification Metrics Summary")
    
    plt.tight_layout()
    
    plt.savefig(
        f"dashboard/{location_id}_metrics.png",
        dpi=150,
    )
    
    plt.close()
    
    
    
if __name__ == "__main__":
    LOCATION_ID = "central_kansas_test"
    
    plot_forecast_vs_observed(LOCATION_ID)
    plot_error_timeseries(LOCATION_ID)
    plot_metrics(LOCATION_ID)