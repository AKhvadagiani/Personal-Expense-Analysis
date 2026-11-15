# Personal-Expense-Analysis

Parse the first PDF in `expenses/sparkasse` and print the dataframe head:

```powershell
uv sync
uv run python sparkasse_parser.py
```

With an activated environment, use `python sparkasse_parser.py`. An optional
PDF path selects a different statement. Both the root script and
`parsers/sparkasse_parser.py` can be run directly. The parser currently supports
Hamburger Sparkasse EUR statements. Amounts retain their signs (negative debits,
positive credits); locations are missing where the statement provides none.

# Run Duckdb UI:
# uv run python -c "import duckdb; con = duckdb.connect('data/database/expenses.duckdb'); con.execute('CALL start_ui()'); input('Press Enter to stop the UI...'); con.close()"

# Run Prefect UI:
# uv run prefect server start
