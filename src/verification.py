"""Forecast verification calculations.

This module matches forecast temperatures with observed temperatures
at the selected observation station and calculates basic verification
metrics.
"""

import pandas as pd

from src.database import get_connection


def calculate_temperature_verification(location_id: str) -> pd.DataFrame:
    """Calculate temperature forecast errors for one location.

    Forecasts are matched to observations by UTC valid hour. Multiple
    observations within the same hour are averaged before matching.

    For the initial portfolio snapshot, this function allows
    lead_time_hours >= -1 so the current-hour forecast can be verified
    when the forecast was retrieved slightly after the valid hour began.
    True positive-lead verification requires repeated forecast ingestion
    over time.

    Parameters
    ----------
    location_id : str
        Configured location identifier.

    Returns
    -------
    pd.DataFrame
        Matched forecast/observation records with error calculations.
    """
    with get_connection() as connection:
        forecasts = pd.read_sql_query(
            """
            SELECT location_id, valid_time, lead_time_hours, temperature_f
            FROM forecasts
            WHERE location_id = ?
            """,
            connection,
            params=(location_id,),
        )

        station = pd.read_sql_query(
            """
            SELECT station_id
            FROM location_stations
            WHERE location_id = ?
            ORDER BY selected_at DESC
            LIMIT 1
            """,
            connection,
            params=(location_id,),
        )

        if station.empty:
            raise ValueError(f"No station found for location_id: {location_id}")

        station_id = station.iloc[0]["station_id"]

        observations = pd.read_sql_query(
            """
            SELECT station_id, valid_time, temperature_f
            FROM observations
            WHERE station_id = ?
            """,
            connection,
            params=(station_id,),
        )

        forecasts["valid_time"] = pd.to_datetime(
            forecasts["valid_time"], utc=True
        ).dt.floor("h")

        observations["valid_time"] = pd.to_datetime(
            observations["valid_time"], utc=True
        ).dt.floor("h")

        observations = (
            observations.dropna(subset=["temperature_f"])
            .groupby(["station_id", "valid_time"], as_index=False)
            .agg({"temperature_f": "mean"})
        )

        forecasts = forecasts.dropna(subset=["temperature_f"])

        latest_observation_time = observations["valid_time"].max()

        forecasts = forecasts[
            (forecasts["lead_time_hours"] >= -1)
            & (forecasts["valid_time"] <= latest_observation_time)
        ]

        forecasts = forecasts.drop_duplicates(
            subset=["location_id", "valid_time", "lead_time_hours"],
            keep="last",
        )

        matched = forecasts.merge(
            observations,
            on="valid_time",
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
        matched["station_id"] = station_id

        return matched


def save_verification_results(location_id: str, results: pd.DataFrame) -> None:
    """Save temperature verification results to the database.

    Parameters
    ----------
    location_id : str
        Configured station identifier.
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
                (location_id, station_id, valid_time, lead_time_hours,
                forecast_temperature_f, observed_temperature_f, error_f,
                absolute_error_f, squared_error_f)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    location_id,
                    row["station_id"],
                    row["valid_time"].isoformat(),
                    row["lead_time_hours"],
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
    results : pandas.DataFrame
        Verification results with forecast and observed temperatures.

    Returns
    -------
    None
    """
    if results.empty:
        print("No matched forecast/observation pairs found.")
        print(
            "This can happen immediately after ingesting new forecasts because "
            "valid future forecasts do not have matching observations yet."
        )
        print(
            "Run the ingestion pipeline again later after forecast valid times "
            "have occurred and observations are available."
        )
        return

    bias = results["error_f"].mean()
    mae = results["absolute_error_f"].mean()
    rmse = (results["squared_error_f"].mean()) ** 0.5

    print(f"Matched pairs: {len(results)}")
    print(f"Bias: {bias:.2f} °F")
    print(f"MAE:  {mae:.2f} °F")
    print(f"RMSE: {rmse:.2f} °F")


def main(location_id: str = "central_kansas_test") -> None:
    """Run temperature verification workflow for one location."""
    results = calculate_temperature_verification(location_id)
    save_verification_results(location_id, results)
    summarize_verification(results)


if __name__ == "__main__":
    main()
