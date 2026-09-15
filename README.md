# Ledger | Personal Finance

Ledger is a Streamlit dashboard for exploring personal bank statements. Upload a CSV or Excel statement to view spending and income summaries, category breakdowns, trends, transaction details, and downloadable filtered data.

## Features

- Upload CSV and XLSX bank statements
- Validate and normalize dates, amounts, transaction types, and statuses
- Automatically categorize common merchants
- Filter by date range, transaction type, category, and status
- View key metrics, spending charts, income charts, and monthly trends
- Download the filtered transactions as CSV

## Requirements

- Python 3.12 or newer
- Dependencies listed in `pyproject.toml`

## Setup

Create and activate a virtual environment, then install the project dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## Run the dashboard

```powershell
streamlit run main.py
```

Streamlit will open the dashboard in your browser. Use the file uploader in the sidebar to load a statement.

## Statement format

Uploaded files must include these columns:

| Column | Description |
| --- | --- |
| `Date` | Transaction date, such as `15-Jan-25` or another recognizable date format |
| `Details` | Merchant or transaction description |
| `Amount` | Transaction amount; commas and currency symbols are supported |
| `Debit/Credit` | Must be `Debit` or `Credit` |

The optional `Status` column is used for status filtering. When it is not supplied, transactions are marked as `Recorded`.

`sample_bank_statement.csv` contains example data that can be uploaded to try the dashboard.

## Project structure

```text
main.py                    Streamlit application
sample_bank_statement.csv  Example statement for testing
categories.json             Category configuration data
pyproject.toml              Project metadata and dependencies
```

## Notes

This dashboard processes uploaded files locally in the running Streamlit session. Review your bank's export format and remove sensitive information before sharing statement files.
