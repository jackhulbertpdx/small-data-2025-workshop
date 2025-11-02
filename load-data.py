#!/usr/bin/env python3
"""
Script to load transformation data from bem API into MotherDuck.

Usage:
    python load_data.py <function-name>

Environment Variables:
    BEM_API_KEY: bem API authentication key
    MOTHERDUCK_TOKEN: MotherDuck authentication token (optional if set globally)
"""

import json
import os
import sys
import tempfile
from typing import Any

import duckdb
import requests


class BemAPIClient:
    """Client for interacting with the bem API."""

    def __init__(self, api_key: str, base_url: str = "https://api.bem.ai") -> None:
        """
        Initialize the bem API client.

        Args:
            api_key: bem API key for authentication
            base_url: Base URL for the bem API

        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"x-api-key": api_key, "Accept": "application/json"})

    def list_transformations(self, function_names: list[str], limit: int = 100) -> list[dict[str, Any]]:
        """
        List transformations for given function names.

        Args:
            function_names: List of function names to filter by
            limit: Maximum number of transformations to fetch per page

        Returns:
            List of transformation objects

        """
        all_transformations = []
        starting_after = None

        while True:
            params = {
                "functionNames": ",".join(function_names),
                "limit": limit,
                "sortOrder": "desc",
            }

            if starting_after:
                params["startingAfter"] = starting_after

            response = self.session.get(f"{self.base_url}/v1-beta/transformations", params=params)
            response.raise_for_status()

            data = response.json()
            transformations = data.get("transformations", [])

            if not transformations:
                break

            all_transformations.extend(transformations)

            # Check if there are more pages
            if len(transformations) < limit:
                break

            # Use the last transformation ID for pagination
            starting_after = transformations[-1]["transformationID"]

        return all_transformations


def sanitize_table_name(name: str) -> str:
    """
    Sanitize a function name to be a valid DuckDB table name.

    Args:
        name: Original function name

    Returns:
        Sanitized table name

    """
    # Replace hyphens with underscores and remove other special characters
    sanitized = name.replace("-", "_").replace(".", "_")
    # Remove any characters that aren't alphanumeric or underscore
    sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
    return sanitized


def create_motherduck_table(
    conn: duckdb.DuckDBPyConnection, table_name: str, transformations: list[dict[str, Any]]
) -> None:
    """
    Create a table in MotherDuck and insert transformation data.

    Args:
        conn: DuckDB connection
        table_name: Name of the table to create
        transformations: List of transformation objects

    """
    if not transformations:
        return

    # Drop table if it exists
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    # Extract transformed content from each transformation
    records = []
    for transformation in transformations:
        transformed_content = transformation.get("transformedContent")
        if transformed_content:
            # Add metadata fields to each record
            record = {
                "reference_id": transformation.get("referenceID"),
                **transformed_content,  # Merge the transformed content
            }
            records.append(record)

    if not records:
        return

    # Convert records to JSON strings for insertion
    # DuckDB can read JSON directly from a file
    json_data = json.dumps(records)

    # Write JSON data to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_file.write(json_data)
        temp_file_path = temp_file.name

    try:
        # Create table from JSON file with explicit format specification
        conn.execute(
            f"""
            CREATE TABLE {table_name} AS
            SELECT * FROM read_json(?, format='array', records=true)
            """,
            [temp_file_path],
        )
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def load_data(function_name: str) -> None:
    """
    Main function to load data from bem to MotherDuck.

    Args:
        function_name: Name of the bem function to fetch transformations for

    """
    # Get API key from environment
    api_key = os.getenv("BEM_API_KEY")
    if not api_key:
        print("Error: BEM_API_KEY environment variable not set")
        sys.exit(1)

    # Set up bem API client
    bem_client = BemAPIClient(api_key)

    # Fetch transformations
    print(f"Fetching transformations for function: {function_name}")
    try:
        transformations = bem_client.list_transformations([function_name])
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error fetching transformations: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching transformations: {e}")
        sys.exit(1)

    if not transformations:
        print(f"No transformations found for function: {function_name}")
        sys.exit(0)

    print(f"Found {len(transformations)} transformations")

    # Set up MotherDuck connection
    print("Connecting to MotherDuck...")
    try:
        # Connect to MotherDuck (token should be set in MOTHERDUCK_TOKEN env var or configured globally)
        conn = duckdb.connect("md:bem_data")
        print("✓ Connected to MotherDuck database 'bem_data'")
    except Exception as e:
        print(f"Error connecting to MotherDuck: {e}")
        sys.exit(1)

    # Create table name from function name
    table_name = sanitize_table_name(function_name)

    # Create table and insert data
    print(f"Creating table '{table_name}' and loading data...")
    try:
        create_motherduck_table(conn, table_name, transformations)
    except Exception as e:
        print(f"Error creating table: {e}")
        conn.close()
        sys.exit(1)

    # Query and print results
    try:
        result = conn.execute(f"SELECT * FROM {table_name}").fetchall()
        columns = [desc[0] for desc in conn.description]

        print(f"\n✓ Successfully loaded {len(result)} records into table '{table_name}'")
        print(f"\nTable columns: {', '.join(columns)}")

        if result:
            print(f"\nFirst {min(10, len(result))} records:")
            print("-" * 80)

            # Print rows (limit to first 10 for readability)
            for i, row in enumerate(result[:10], 1):
                print(f"\nRecord {i}:")
                for col, val in zip(columns, row):
                    # Truncate long values for readability
                    val_str = str(val)
                    if len(val_str) > 100:
                        val_str = val_str[:100] + "..."
                    print(f"  {col}: {val_str}")

            if len(result) > 10:
                print(f"\n... and {len(result) - 10} more records")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"Error querying table: {e}")
        conn.close()
        sys.exit(1)

    # Close connection
    conn.close()


def main() -> None:
    """Parse command line arguments and run the load_data function."""
    if len(sys.argv) != 2:
        print("Usage: python load-data.py <function-name>")
        print("\nEnvironment Variables:")
        print("  BEM_API_KEY: bem API authentication key (required)")
        print("  MOTHERDUCK_TOKEN: MotherDuck authentication token (optional if configured globally)")
        sys.exit(1)

    function_name = sys.argv[1]
    load_data(function_name)


if __name__ == "__main__":
    main()
