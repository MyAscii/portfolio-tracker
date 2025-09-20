# Portfolio Tracker

A production-ready web scraping tool for tracking CardMarket portfolio prices with automated data collection and storage.

## Features

- 🔍 **Web Scraping**: Automated price tracking from CardMarket
- 💾 **CSV Storage**: Simple, portable data storage in CSV format
- 📊 **Price History**: Track hourly price trends over time
- 🧪 **Comprehensive Testing**: Unit and integration test coverage
- 🏗️ **Modular Architecture**: Clean separation of concerns
- ⚡ **Async Support**: Efficient concurrent processing

## Project Structure

```
portfolio/
├── src/
│   ├── portfolio_tracker/
│   │   ├── __init__.py
│   │   ├── csv_storage.py     # CSV data management
│   │   ├── scraper.py         # Web scraping logic
│   │   └── tracker.py         # Main orchestrator
│   ├── main.py                # Entry point
├── data/                      # CSV data files
│   ├── portfolio_items.csv    # Portfolio items
│   └── price_history.csv      # Price tracking data
├── tests/
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── run_tests.py           # Test runner
├── config/                    # Configuration files
├── portfolio.csv              # Portfolio items
├── requirements.txt           # Dependencies
└── setup.py                   # Package setup
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd portfolio
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

4. **Install the package** (optional):
   ```bash
   pip install -e .
   ```

## Usage

### Basic Usage

1. **Prepare your portfolio CSV**:
   Create a `portfolio.csv` file with your items:
   ```csv
   link,name,purchase_date,quantity,purchase_price
   https://www.cardmarket.com/en/Magic/Products/Singles/Set/Card-Name,Card Name,2024-01-01,2,10.50
   ```

2. **Run the tracker**:
   ```bash
   python src/main.py
   ```

3. **Verify results**:
   ```bash
   python src/verify_db.py
   ```

### Advanced Usage

```python
from portfolio_tracker import PortfolioTracker
import asyncio

async def main():
    tracker = PortfolioTracker(
        db_path="custom_portfolio.db",
        csv_path="custom_portfolio.csv"
    )
    
    # Track all items
    await tracker.track_all_items()
    
    # Get portfolio summary
    summary = tracker.get_portfolio_summary()
    print(f"Total items: {summary['total_items']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python tests/run_tests.py

# Run only unit tests
python tests/run_tests.py --unit

# Run only integration tests
python tests/run_tests.py --integration

# Using pytest directly
pytest tests/ -v
```

## Development

### Code Quality

The project includes development tools for code quality:

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Project Architecture

- **CSV Storage** (`csv_storage.py`): CSV data management and operations
- **Scraper** (`scraper.py`): Web scraping logic with Playwright
- **Tracker** (`tracker.py`): Main orchestration and business logic

## Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
# Scraping configuration
SCRAPE_DELAY_MIN=3
SCRAPE_DELAY_MAX=6
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# Data storage (CSV files stored in data/ directory)
# No additional configuration needed
```

### CSV Format

The portfolio CSV should include these columns:
- `link`: CardMarket product URL
- `name`: Item name
- `purchase_date`: Purchase date (YYYY-MM-DD)
- `quantity`: Number of items owned
- `purchase_price`: Price paid per item

## Data Format

### Portfolio Items CSV (`portfolio_items.csv`)
- ID, name, quantity, purchase_price
- Simple CSV format for easy editing and viewing

### Price History CSV (`price_history.csv`)
- Hourly price tracking data
- Columns: item_name, from_price, to_price, price_trend, scraped_at, scrape_status
- Timestamped records for trend analysis

## Error Handling

The system includes comprehensive error handling:
- Network timeouts and retries
- Invalid data validation
- CSV file integrity checks
- Graceful failure recovery

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and personal use only. Please respect CardMarket's terms of service and implement appropriate rate limiting.