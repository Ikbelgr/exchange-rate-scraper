# Exchange Rate Scraper

This script automatically scrapes exchange rates from Western Union for:
- EUR to TND (Tunisian Dinar)
- EUR to MAD (Moroccan Dirham)

The rates are collected daily and stored in a CSV file.

## Requirements

- Python 3.7 or higher
- Google Chrome browser installed
- Internet connection

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python exchange_rate_scraper.py
```

The script will:
1. Run immediately to get current rates
2. Schedule daily runs at 12:00 PM
3. Save results to `exchange_rates.csv`

## Output

The script creates a CSV file (`exchange_rates.csv`) with the following columns:
- datetime: When the rate was collected
- currency_pair: The currency pair (EUR-TND or EUR-MAD)
- rate: The exchange rate

## Notes

- The script runs in headless mode (no browser window visible)
- Rates are collected once per day at 12:00 PM
- Make sure you have a stable internet connection
- The script needs to keep running to maintain the schedule 