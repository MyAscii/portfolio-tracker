"""Unit tests for tracker module"""

import unittest
import tempfile
import os
import csv
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from portfolio_tracker.tracker import PortfolioTracker


class TestPortfolioTracker(unittest.TestCase):
    """Test cases for PortfolioTracker"""
    
    def setUp(self):
        """Set up test tracker"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create temporary CSV
        self.temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
        csv_writer = csv.writer(self.temp_csv)
        csv_writer.writerow(['link', 'name', 'purchase_date', 'quantity', 'purchase_price'])
        csv_writer.writerow([
            'https://example.com/card1',
            'Test Card 1',
            '2024-01-01',
            '2',
            '10.50'
        ])
        csv_writer.writerow([
            'https://example.com/card2',
            'Test Card 2',
            '2024-01-02',
            '1',
            '25.00'
        ])
        self.temp_csv.close()
        
        self.tracker = PortfolioTracker(
            db_path=self.temp_db.name,
            csv_path=self.temp_csv.name
        )
    
    def tearDown(self):
        """Clean up temporary files"""
        # Close database connections
        if hasattr(self.tracker, 'db_manager') and self.tracker.db_manager:
            self.tracker.db_manager.close()
        
        # Clean up temporary files
        try:
            os.unlink(self.temp_db.name)
        except (PermissionError, FileNotFoundError):
            pass  # File may already be deleted or in use
        
        try:
            os.unlink(self.temp_csv.name)
        except (PermissionError, FileNotFoundError):
            pass  # File may already be deleted or in use
    
    def test_load_portfolio_from_csv(self):
        """Test loading portfolio from CSV"""
        items = self.tracker.load_portfolio_from_csv()
        
        self.assertEqual(len(items), 2)
        
        item1 = items[0]
        self.assertEqual(item1['name'], 'Test Card 1')
        self.assertEqual(item1['link'], 'https://example.com/card1')
        self.assertEqual(item1['quantity'], 2)
        self.assertEqual(item1['purchase_price'], 10.50)
        
        item2 = items[1]
        self.assertEqual(item2['name'], 'Test Card 2')
        self.assertEqual(item2['quantity'], 1)
        self.assertEqual(item2['purchase_price'], 25.00)
    
    def test_load_portfolio_from_csv_missing_file(self):
        """Test loading portfolio from non-existent CSV"""
        tracker = PortfolioTracker(csv_path='nonexistent.csv')
        items = tracker.load_portfolio_from_csv()
        
        self.assertEqual(len(items), 0)
    
    def test_load_portfolio_from_csv_invalid_data(self):
        """Test loading portfolio with invalid CSV data"""
        # Create CSV with invalid data
        temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
        csv_writer = csv.writer(temp_csv)
        csv_writer.writerow(['link', 'name', 'quantity', 'purchase_price'])
        csv_writer.writerow(['', 'Empty Link', '1', '10.00'])  # Empty link
        csv_writer.writerow(['https://example.com/card', '', '1', '10.00'])  # Empty name
        csv_writer.writerow(['https://example.com/valid', 'Valid Card', 'invalid', '10.00'])  # Invalid quantity
        temp_csv.close()
        
        try:
            tracker = PortfolioTracker(csv_path=temp_csv.name)
            items = tracker.load_portfolio_from_csv()
            
            # Should skip invalid entries
            self.assertEqual(len(items), 0)
        finally:
            os.unlink(temp_csv.name)
    
    @patch('portfolio_tracker.tracker.PortfolioTracker.load_portfolio_from_csv')
    @patch('portfolio_tracker.tracker.DatabaseManager')
    @patch('portfolio_tracker.tracker.CardMarketScraper')
    async def test_track_all_items(self, mock_scraper_class, mock_db_class, mock_load_csv):
        """Test tracking all items"""
        # Mock CSV loading
        mock_load_csv.return_value = [
            {
                'link': 'https://example.com/card1',
                'name': 'Test Card 1',
                'quantity': 1,
                'purchase_price': 10.00
            }
        ]
        
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        
        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.name = 'Test Card 1'
        mock_item.link = 'https://example.com/card1'
        mock_db.get_portfolio_items.return_value = [mock_item]
        
        # Mock scraper
        mock_scraper = AsyncMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.scrape_item_price.return_value = {
            'status': 'success',
            'from_price': 12.50,
            'available_items': 100
        }
        
        # Create tracker with mocked dependencies
        tracker = PortfolioTracker()
        tracker.db_manager = mock_db
        tracker.scraper = mock_scraper
        
        # Track items
        await tracker.track_all_items()
        
        # Verify calls
        mock_load_csv.assert_called_once()
        mock_db.sync_portfolio_items.assert_called_once()
        mock_db.get_portfolio_items.assert_called_once()
        mock_scraper.scrape_item_price.assert_called_once_with('https://example.com/card1')
        mock_db.save_price_data.assert_called_once()
    
    def test_get_portfolio_summary(self):
        """Test getting portfolio summary"""
        # Load items into database
        items = self.tracker.load_portfolio_from_csv()
        self.tracker.db_manager.sync_portfolio_items(items)
        
        # Add some price data
        db_items = self.tracker.db_manager.get_portfolio_items()
        for item in db_items:
            price_data = {
                'status': 'success',
                'from_price': 15.00,
                'available_items': 50
            }
            self.tracker.db_manager.save_price_data(item.id, price_data)
        
        # Get summary
        summary = self.tracker.get_portfolio_summary()
        
        self.assertEqual(summary['total_items'], 2)
        self.assertEqual(len(summary['items']), 2)
        
        item_summary = summary['items'][0]
        self.assertIn('name', item_summary)
        self.assertIn('quantity', item_summary)
        self.assertIn('purchase_price', item_summary)
        self.assertIn('current_price', item_summary)
        self.assertIn('last_updated', item_summary)
        
        # Should have current price from latest price data
        self.assertEqual(item_summary['current_price'], 15.00)


if __name__ == '__main__':
    unittest.main()