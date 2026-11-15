# Personal-Expense-Analysis

Parse the first PDF in `expenses/sparkasse`, save its full dataframe to the
`sparkasse_tranasctions` table in `data/database/expenses.duckdb`, and print the dataframe head:

```powershell
uv sync
uv run python sparkasse_parser.py
```

With an activated environment, use `python sparkasse_parser.py`. An optional
PDF path selects a different statement. Both the root script and
`parsers/sparkasse_parser.py` can be run directly. The parser currently supports
Hamburger Sparkasse EUR statements. Amounts retain their signs (negative debits,
positive credits); locations are missing where the statement provides none.
Dates are stored as `DATE` and amounts as `DECIMAL(18, 2)`. Imports are atomic.
The `sparkasse_imports` table tracks PDF content hashes, so importing the same
PDF again skips it without duplicating transactions. Different PDFs append rows.

# Run Duckdb UI:
# uv run python -c "import duckdb; con = duckdb.connect('data/database/expenses.duckdb'); con.execute('CALL start_ui()'); input('Press Enter to stop the UI...'); con.close()"

# Run Prefect UI:
# uv run prefect server start


# Where are we at?

The python sparkasse_parser.py runs the parser and imports the first PDF in `expenses/sparkasse`.
if I run DuckDB UI, I can see the `sparkasse_transactions` table and the `sparkasse_imports` table.

What's next:
Prefect should pick up the pdf that is not already in the `sparkasse_imports` table, run the parser,
and import the transactions into the `sparkasse_transactions` table.

Prefect should process partitions one by one, if I have 10 new files, check N1, exists - skip, check N2, not exists - 
parse and add it to the database.