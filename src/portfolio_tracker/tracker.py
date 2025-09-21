"""Main portfolio tracker orchestrator"""

import csv
import asyncio
import random
import logging
from typing import List, Dict, Any
from pathlib import Path

from .csv_storage import CSVStorageManager
from .scraper import CardMarketScraper

logger = logging.getLogger(__name__)


class PortfolioTracker:
    """Main portfolio tracking orchestrator"""
    
    def __init__(self, data_dir: str = "data", csv_path: str = "portfolio.csv"):
        self.storage_manager = CSVStorageManager(data_dir)
        self.scraper = CardMarketScraper()
        self.csv_path = csv_path
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_portfolio_from_csv(self) -> List[Dict[str, Any]]:
        """Load portfolio items from CSV file"""
        portfolio_items = []
        csv_file = Path(self.csv_path)
        
        if not csv_file.exists():
            logger.error(f"[ERROR] Portfolio CSV file not found: {self.csv_path}")
            return portfolio_items
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Handle BOM in column names
                    link_value = row.get('Link', '') or row.get('\ufeffLink', '')
                    item = {
                        'link': link_value.strip(),
                        'name': row.get('Name', '').strip(),
                        'purchase_date': row.get('Date', '').strip(),
                        'quantity': int(row.get('Quantity', 1)),
                        'purchase_price': float(row.get('Price', 0)) if row.get('Price') else None
                    }
                    
                    if item['link'] and item['name']:
                        portfolio_items.append(item)
                        logger.info(f"[LOAD] Loaded: {item['name']}")
                    else:
                        logger.warning(f"[SKIP] Skipping item with missing link or name: {item}")
            
            logger.info(f"[SUCCESS] Loaded {len(portfolio_items)} items from CSV")
            
        except Exception as e:
            logger.error(f"[ERROR] Error loading CSV: {e}")
        
        return portfolio_items
    
    async def track_all_items(self):
        """Track prices for all items in portfolio"""
        logger.info("[START] Starting portfolio tracking...")
        
        # Load portfolio from CSV
        portfolio_items = self.load_portfolio_from_csv()
        if not portfolio_items:
            logger.error("[ERROR] No portfolio items found")
            return
        
        # Sync to CSV storage
        self.storage_manager.sync_portfolio_items(portfolio_items)
        logger.info("[SUCCESS] Portfolio synced to CSV storage")
        
        # Get items from CSV storage for tracking
        stored_items = self.storage_manager.get_portfolio_items()
        
        # Track each item
        for item in stored_items:
            try:
                logger.info(f"[TRACK] Tracking: {item['name']}")
                price_data = await self.scraper.scrape_with_fallback(item['link'])
                self.storage_manager.save_price_data(int(item['id']), item['name'], price_data)
                
                # Add delay between requests
                await asyncio.sleep(random.uniform(3, 6))
                
            except Exception as e:
                logger.error(f"[ERROR] Error tracking {item['name']}: {e}")
        
        logger.info("[COMPLETE] Portfolio tracking completed!")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary with latest prices"""
        items = self.storage_manager.get_portfolio_items()
        summary = {
            'total_items': len(items),
            'items': []
        }
        
        for item in items:
            latest_price = self.storage_manager.get_latest_price_data(int(item['id']))
            item_summary = {
                'name': item['name'],
                'quantity': item['quantity'],
                'purchase_price': item['purchase_price'],
                'current_price': latest_price['from_price'] if latest_price else None,
                'last_updated': latest_price['scraped_at'] if latest_price else None
            }
            summary['items'].append(item_summary)
        
        return summary