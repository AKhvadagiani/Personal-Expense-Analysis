# Personal-Expense-Analysis

# Run Duckdb UI:
# uv run python -c "import duckdb; con = duckdb.connect('data/database/expenses.duckdb'); con.execute('CALL start_ui()'); input('Press Enter to stop the UI...'); con.close()"

# Run Prefect UI:
# uv run prefect server start