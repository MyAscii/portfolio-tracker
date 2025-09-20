"""CSV-based storage management for portfolio tracking"""

import os
import csv
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class CSVStorageManager:
    """Manages CSV-based storage operations for portfolio tracking"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # CSV file paths
        self.portfolio_file = self.data_dir / "portfolio_items.csv"
        self.price_history_file = self.data_dir / "price_history.csv"
        
        # Initialize CSV files if they don't exist
        self._init_csv_files()
    
    def _init_csv_files(self):
        """Initialize CSV files with headers if they don't exist"""
        # Portfolio items CSV
        if not self.portfolio_file.exists():
            with open(self.portfolio_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'id', 'link', 'name', 'purchase_date', 'quantity', 
                    'purchase_price', 'created_at', 'updated_at'
                ])
        
        # Price history CSV
        if not self.price_history_file.exists():
            with open(self.price_history_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'item_id', 'item_name', 'available_items', 'from_price', 
                    'price_trend', 'avg_30_days', 'avg_7_days', 'avg_1_day',
                    'min_seller_price', 'max_seller_price', 'seller_count',
                    'seller_prices_json', 'scrape_status', 'error_message',
                    'scraped_at'
                ])
    
    def sync_portfolio_items(self, items: List[Dict[str, Any]]) -> None:
        """Sync portfolio items from CSV data to storage"""
        # Read existing items
        existing_items = {}
        if self.portfolio_file.exists():
            with open(self.portfolio_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_items[row['link']] = row
        
        # Update or add items
        updated_items = []
        next_id = len(existing_items) + 1
        
        for item_data in items:
            link = item_data['link']
            current_time = datetime.utcnow().isoformat()
            
            if link in existing_items:
                # Update existing item
                item = existing_items[link].copy()
                item.update({
                    'name': item_data['name'],
                    'purchase_date': item_data.get('purchase_date', ''),
                    'quantity': item_data.get('quantity', 1),
                    'purchase_price': item_data.get('purchase_price', ''),
                    'updated_at': current_time
                })
            else:
                # Create new item
                item = {
                    'id': next_id,
                    'link': link,
                    'name': item_data['name'],
                    'purchase_date': item_data.get('purchase_date', ''),
                    'quantity': item_data.get('quantity', 1),
                    'purchase_price': item_data.get('purchase_price', ''),
                    'created_at': current_time,
                    'updated_at': current_time
                }
                next_id += 1
            
            updated_items.append(item)
            existing_items[link] = item
        
        # Write back to CSV
        with open(self.portfolio_file, 'w', newline='', encoding='utf-8') as f:
            if updated_items:
                writer = csv.DictWriter(f, fieldnames=updated_items[0].keys())
                writer.writeheader()
                writer.writerows(existing_items.values())
    
    def get_portfolio_items(self) -> List[Dict[str, Any]]:
        """Get all portfolio items"""
        items = []
        if self.portfolio_file.exists():
            with open(self.portfolio_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                items = list(reader)
        return items
    
    def save_price_data(self, item_id: int, item_name: str, price_data: Dict[str, Any]) -> None:
        """Save price data for an item"""
        # Serialize seller prices to JSON
        seller_prices_json = json.dumps(price_data.get('seller_prices', []))
        
        price_record = {
            'item_id': item_id,
            'item_name': item_name,
            'available_items': price_data.get('available_items', ''),
            'from_price': price_data.get('from_price', ''),
            'price_trend': price_data.get('price_trend', ''),
            'avg_30_days': price_data.get('avg_30_days', ''),
            'avg_7_days': price_data.get('avg_7_days', ''),
            'avg_1_day': price_data.get('avg_1_day', ''),
            'min_seller_price': price_data.get('min_seller_price', ''),
            'max_seller_price': price_data.get('max_seller_price', ''),
            'seller_count': price_data.get('seller_count', 0),
            'seller_prices_json': seller_prices_json,
            'scrape_status': price_data.get('status', 'success'),
            'error_message': price_data.get('error', ''),
            'scraped_at': datetime.utcnow().isoformat()
        }
        
        # Append to price history CSV
        file_exists = self.price_history_file.exists()
        with open(self.price_history_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=price_record.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(price_record)
    
    def get_latest_price_data(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get latest price data for an item"""
        latest_record = None
        if self.price_history_file.exists():
            with open(self.price_history_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['item_id'] == str(item_id):
                        latest_record = row
        return latest_record
    
    def get_price_history(self, item_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get price history for an item"""
        records = []
        if self.price_history_file.exists():
            with open(self.price_history_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['item_id'] == str(item_id):
                        records.append(row)
        
        # Sort by scraped_at descending and limit
        records.sort(key=lambda x: x['scraped_at'], reverse=True)
        return records[:limit]
    
    def get_all_price_records(self) -> List[Dict[str, Any]]:
        """Get all price records for verification"""
        records = []
        if self.price_history_file.exists():
            with open(self.price_history_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                records = list(reader)
        
        # Sort by scraped_at descending
        records.sort(key=lambda x: x['scraped_at'], reverse=True)
        return records
    
    def get_recent_price_records(self, hours: int = 2) -> List[Dict[str, Any]]:
        """Get price records from the last N hours"""
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_records = []
        
        if self.price_history_file.exists():
            with open(self.price_history_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        scraped_time = datetime.fromisoformat(row['scraped_at'])
                        if scraped_time >= cutoff_time:
                            recent_records.append(row)
                    except (ValueError, KeyError):
                        continue
        
        return recent_records