# Portfolio Tracker Setup Guide

## 🎯 Overview

This system automatically tracks CardMarket prices for your portfolio items every hour using GitHub Actions and stores the data in CSV files for easy access and portability.

## 📋 Features

- ✅ **Automated Tracking**: Runs every hour via GitHub Actions
- ✅ **Multi-Game Support**: Pokemon and Magic: The Gathering
- ✅ **Comprehensive Data**: Market stats, price trends, individual seller prices
- ✅ **CSV Storage**: Simple, portable data storage in CSV format
- ✅ **Error Handling**: Robust scraping with retry logic
- ✅ **Logging**: Detailed logs for monitoring
- ✅ **Hourly Data**: Track price changes every hour

## 🚀 Quick Start

### 1. Repository Setup

1. **Create a new GitHub repository**
2. **Upload your files**:
   ```bash
   git init
   git add .
   git commit -m "Initial portfolio tracker setup"
   git branch -M main
   git remote add origin https://github.com/yourusername/portfolio-tracker.git
   git push -u origin main
   ```

### 2. Portfolio Configuration

1. **Edit your `portfolio.csv`** with your items:
   ```csv
   link,name,purchase_date,quantity,purchase_price
   https://cardmarket.com/en/Pokemon/Products/Singles/...,Charizard VMAX,2024-01-01,1,50.00
   ```

2. **No database setup required** - data is stored in CSV files

### 3. GitHub Actions Setup (Optional Secrets)

Go to your repository → Settings → Secrets and variables → Actions

No secrets are required for basic functionality. The system works with CSV files stored in the repository.

Optional secrets for notifications:
```
DISCORD_WEBHOOK_URL=your_discord_webhook_url
SLACK_WEBHOOK_URL=your_slack_webhook_url
```

## 🔧 Local Development

### 1. Environment Setup
```bash
# Clone repository
git clone https://github.com/yourusername/portfolio-tracker.git
cd portfolio-tracker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Create Data Directory
```bash
# Create data directory for CSV files
mkdir data
```

### 3. Run Tracker
```bash
python src/main.py
```

## 📊 Data Format

### Portfolio Items Table
```sql
CREATE TABLE portfolio_items (
    id SERIAL PRIMARY KEY,
    link VARCHAR(500) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    purchase_date VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    purchase_price FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Price History Table
```sql
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES portfolio_items(id),
    available_items INTEGER,
    from_price FLOAT,
    price_trend FLOAT,
    avg_30_days FLOAT,
    avg_7_days FLOAT,
    avg_1_day FLOAT,
    min_seller_price FLOAT,
    max_seller_price FLOAT,
    seller_count INTEGER,
    seller_prices_json TEXT,
    scraped_at TIMESTAMP DEFAULT NOW(),
    scrape_status VARCHAR(20) DEFAULT 'success',
    error_message TEXT
);
```

## 🤖 GitHub Actions Workflow

The workflow runs:
- **Every hour** at minute 0
- **On push** to main branch (when portfolio.csv changes)
- **Manually** via workflow dispatch

### Workflow Steps:
1. 🐳 Start PostgreSQL service
2. 🐍 Set up Python environment
3. 📦 Install dependencies and Playwright
4. 🗄️ Initialize database
5. 🔍 Run portfolio tracker
6. 📋 Generate summary report
7. 📁 Upload logs as artifacts

## 📈 Monitoring

### View Tracking Results
1. Go to your repository → Actions
2. Click on latest "Portfolio Price Tracker" run
3. Check the summary for tracking results
4. Download logs if needed

### Database Queries
```sql
-- Latest prices for all items
SELECT 
    pi.name,
    ph.from_price,
    ph.price_trend,
    ph.scraped_at
FROM portfolio_items pi
JOIN price_history ph ON pi.id = ph.item_id
WHERE ph.scraped_at = (
    SELECT MAX(scraped_at) 
    FROM price_history ph2 
    WHERE ph2.item_id = pi.id
);

-- Price history for specific item
SELECT 
    from_price,
    price_trend,
    avg_30_days,
    scraped_at
FROM price_history ph
JOIN portfolio_items pi ON ph.item_id = pi.id
WHERE pi.name = 'Your Item Name'
ORDER BY scraped_at DESC;
```

## 🔧 Customization

### Adding New Items
1. Add row to `portfolio.csv`
2. Commit and push changes
3. GitHub Actions will automatically track the new item

### Changing Tracking Frequency
Edit `.github/workflows/portfolio-tracker.yml`:
```yaml
schedule:
  - cron: '0 */2 * * *'  # Every 2 hours
  - cron: '0 8,20 * * *'  # Twice daily at 8 AM and 8 PM
```

### Adding Notifications
Extend the workflow to send notifications:
```yaml
- name: Send Discord notification
  if: failure()
  run: |
    curl -X POST "${{ secrets.DISCORD_WEBHOOK_URL }}" \
    -H "Content-Type: application/json" \
    -d '{"content": "❌ Portfolio tracking failed!"}'
```

## 🐛 Troubleshooting

### Common Issues

1. **Scraping Failures**
   - Check if CardMarket changed their layout
   - Verify item URLs are still valid
   - Check GitHub Actions logs

2. **Database Connection Issues**
   - Verify PostgreSQL credentials in GitHub Secrets
   - Check database service status
   - Ensure database exists

3. **Playwright Issues**
   - Browser installation might fail
   - Check GitHub Actions runner compatibility
   - Try different browser (Firefox, WebKit)

### Debug Mode
Add to environment variables:
```bash
DEBUG=true
PLAYWRIGHT_DEBUG=true
```

## 📝 Next Steps

1. **Build Web UI** for viewing portfolio data
2. **Add Price Alerts** when items reach target prices
3. **Portfolio Analytics** with charts and trends
4. **Mobile App** for on-the-go tracking
5. **API Endpoints** for external integrations

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test locally
5. Submit pull request

## 📄 License

MIT License - feel free to use and modify!