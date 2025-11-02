#!/usr/bin/env python3
"""
Example script showing how to query bem data from MotherDuck.

This demonstrates various ways to analyze transformation data after
it has been loaded using the load_data.py script.
"""

import contextlib

import duckdb


def example_queries() -> None:
    """Run example queries on bem data in MotherDuck."""
    # Connect to MotherDuck
    conn = duckdb.connect("md:bem_data")

    # Example 1: Show all tables
    tables = conn.execute("SHOW TABLES").fetchall()
    for _table in tables:
        pass

    # Example 2: Count records in a table
    # Replace 'your_table_name' with an actual table from above
    table_name = tables[0][0] if tables else None

    if table_name:
        conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()

        # Example 3: Show table schema
        schema = conn.execute(f"DESCRIBE {table_name}").fetchall()
        for _col in schema:
            pass

        # Example 4: Sample records
        samples = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchall()
        [desc[0] for desc in conn.description]
        for _row in samples:
            pass

        # Example 5: Group by analysis (if function_name exists)
        try:
            agg = conn.execute(f"""
                SELECT function_name, COUNT(*) as count
                FROM {table_name}
                WHERE function_name IS NOT NULL
                GROUP BY function_name
                ORDER BY count DESC
            """).fetchall()

            if agg:
                for _row in agg:
                    pass
            else:
                pass
        except Exception:
            pass

        # Example 6: Recent transformations
        try:
            recent = conn.execute(f"""
                SELECT transformation_id, reference_id, created_at
                FROM {table_name}
                WHERE created_at IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 5
            """).fetchall()

            if recent:
                for _row in recent:
                    pass
            else:
                pass
        except Exception:
            pass

        # Example 7: Export to CSV (commented out by default)

        # Example 8: Export to Parquet (commented out by default)

    else:
        pass

    # Close connection
    conn.close()


if __name__ == "__main__":
    with contextlib.suppress(Exception):
        example_queries()
