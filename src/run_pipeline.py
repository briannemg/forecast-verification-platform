"""Command-line runner for forecast verification pipeline."""

import argparse

from src.config import DEFAULT_LOCATION_ID
from src.database import initialize_database
from src.load_data import load_locations
from src.plots import generate_plots
from src.verification import run_verification

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Run the forecast verification pipeline."
    )
    
    parser.add_argument(
        "--location",
        default=DEFAULT_LOCATION_ID,
        help=(
            "Optional location_id to process. "
            "If omitted, all configuration locations are processed."
        ),
    )
    
    return parser.parse_args()

def run_pipeline(location_id: str | None = None) -> None:
    """Run the full forecast verification workflow.

    Parameters
    ----------
    location_id : str or None, optional
        Specific location_id to process. If None, all configured
        locations are processed.
        
    Returns
    -------
    None
    """
    print("\nInitializing database...")
    initialize_database()
    
    print("Loading forecast and observation data...")
    load_locations(location_id)
    
    print("Running forecast verification...")
    run_verification(location_id)
    
    print("Generating plots...")
    generate_plots(location_id)
    
    print("\nPipeline complete.")
    
def main() -> None:
    """Parse command-line arguments and run pipeline."""
    args = parse_args()
    run_pipeline(args.location)
    
    
if __name__ == "__main__":
    main()