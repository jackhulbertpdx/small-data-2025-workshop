# bem to MotherDuck Integration

This script loads transformation data from the bem API into MotherDuck for analysis and querying.

## Prerequisites

1. **bem API Key**: You need an API key from bem.ai
2. **MotherDuck Account**: Sign up at [motherduck.com](https://motherduck.com)
3. **Python 3.7+**: Ensure Python is installed

## Installation

1. Install the required Python packages:

```bash
pip install -r requirements-motherduck.txt
```

Or install manually:

```bash
pip install duckdb>=0.9.0 requests>=2.31.0
```

## Authentication Setup

### bem API Key

Set your bem API key as an environment variable:

```bash
export BEM_API_KEY="your-api-key-here"
```

You can get your API key from the bem dashboard at Settings → API Keys.

### MotherDuck Token

Set your MotherDuck token as an environment variable:

```bash
export MOTHERDUCK_TOKEN="your-motherduck-token-here"
```

Alternatively, you can authenticate once using the DuckDB CLI:

```bash
duckdb
```

Then in the DuckDB prompt:
```sql
ATTACH 'md:';
```

This will open a browser for authentication, and the token will be stored locally.

## Usage

Run the script with a function name:

```bash
python load_data.py <function-name>
```

### Example

```bash
python load_data.py invoice-processor
```

## What the Script Does

1. **Connects to bem API**: Authenticates using your API key
2. **Fetches Transformations**: Retrieves all transformations for the specified function
3. **Connects to MotherDuck**: Establishes connection to your MotherDuck database
4. **Creates Table**: Creates a table named after the function (with sanitized name)
5. **Inserts Data**: Loads the `transformedContent` from each transformation
6. **Queries Data**: Runs a SELECT * query and displays results
7. **Closes Connection**: Cleans up and exits

## Table Structure

The created table includes:

- `transformation_id`: Unique ID for the transformation
- `reference_id`: Reference ID from the original transformation
- `created_at`: Timestamp when transformation was created
- `function_name`: Name of the function that created the transformation
- Additional fields from the `transformedContent` JSON object

## Database Location

The data is stored in the `bem_data` database in MotherDuck. You can query it later:

```python
import duckdb

conn = duckdb.connect("md:bem_data")
result = conn.execute("SELECT * FROM your_function_name").fetchall()
print(result)
conn.close()
```

Or using the DuckDB CLI:

```bash
duckdb md:bem_data
```

Then:
```sql
SHOW TABLES;
SELECT * FROM your_function_name LIMIT 10;
```

## Pagination

The script automatically handles pagination and will fetch all transformations for the specified function, regardless of how many exist.

## Error Handling

The script includes comprehensive error handling for:

- Missing environment variables
- API authentication failures
- Network errors
- MotherDuck connection issues
- Data insertion errors

## Example Output

```
Connecting to bem API...
Fetching transformations for function 'invoice-processor'...
✓ Fetched 150 transformations
Connecting to MotherDuck...
✓ Connected to MotherDuck
Creating table 'invoice_processor' in MotherDuck...
✓ Created table 'invoice_processor' with 150 records

Querying data from 'invoice_processor'...

================================================================================
Results from table 'invoice_processor' (150 rows):
================================================================================

transformation_id | reference_id | created_at | function_name | invoice_number | amount
------------------------------------------------------------------------------------
tr_2bxoJPNdSD4L... | ref_001 | 2024-01-15T10:30:00Z | invoice-processor | INV-001 | 1500.00
tr_3cxpKQOeTE5M... | ref_002 | 2024-01-15T10:31:00Z | invoice-processor | INV-002 | 2500.00
...

✓ Closing MotherDuck connection...
Done!
```

## Troubleshooting

### "BEM_API_KEY environment variable not set"

Make sure you've exported the API key:
```bash
export BEM_API_KEY="your-key"
```

### "Error connecting to MotherDuck"

Make sure you've set the MOTHERDUCK_TOKEN or authenticated via DuckDB CLI:
```bash
export MOTHERDUCK_TOKEN="your-token"
```

### "No transformations found"

Verify that:
- The function name is correct (check bem dashboard)
- The function has processed transformations
- Your API key has access to the function

## Advanced Usage

### Filtering Data in MotherDuck

After loading, you can use DuckDB's powerful SQL features:

```python
import duckdb

conn = duckdb.connect("md:bem_data")

# Filter by date
result = conn.execute("""
    SELECT * FROM invoice_processor
    WHERE created_at > '2024-01-01'
""").fetchall()

# Aggregate data
result = conn.execute("""
    SELECT function_name, COUNT(*) as count, AVG(amount) as avg_amount
    FROM invoice_processor
    GROUP BY function_name
""").fetchall()

conn.close()
```

### Exporting to Other Formats

DuckDB supports exporting to various formats:

```sql
-- Export to CSV
COPY (SELECT * FROM invoice_processor) TO 'output.csv' (HEADER, DELIMITER ',');

-- Export to Parquet
COPY (SELECT * FROM invoice_processor) TO 'output.parquet' (FORMAT PARQUET);
```

## Notes

- The script drops and recreates the table each time it runs
- Table names are sanitized (hyphens → underscores, special characters removed)
- Large transformations are paginated automatically
- The first 10 rows are displayed in the console output

## Support

For issues with:
- **bem API**: Check docs.bem.ai or contact bem support
- **MotherDuck**: Check motherduck.com/docs or contact MotherDuck support
- **This script**: Open an issue in the bem repository
