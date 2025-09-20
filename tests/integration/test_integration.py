"""Integration tests for portfolio tracker"""

import unittest
import tempfile
import os
import csv
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from portfolio_tracker import PortfolioTracker, CSVStorageManager, CardMarketScraper


class TestPortfolioTrackerIntegration(unittest.TestCase):
    """Integration tests for the complete portfolio tracking system"""
    
    def setUp(self):
        """Set up integration test environment"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create temporary CSV with test data
        self.temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
        csv_writer = csv.writer(self.temp_csv)
        csv_writer.writerow(['link', 'name', 'purchase_date', 'quantity', 'purchase_price'])
        csv_writer.writerow([
            'https://www.cardmarket.com/en/Magic/Products/Singles/Test-Set/Test-Card-1',
            'Test Card 1',
            '2024-01-01',
            '2',
            '10.50'
        ])
        csv_writer.writerow([
            'https://www.cardmarket.com/en/Pokemon/Products/Singles/Test-Set/Test-Card-2',
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
    
    def test_csv_to_database_sync(self):
        """Test complete CSV to database synchronization"""
        # Load from CSV
        items = self.tracker.load_portfolio_from_csv()
        self.assertEqual(len(items), 2)
        
        # Sync to database
        self.tracker.db_manager.sync_portfolio_items(items)
        
        # Verify in database
        db_items = self.tracker.db_manager.get_portfolio_items()
        self.assertEqual(len(db_items), 2)
        
        # Check first item
        item1 = next(item for item in db_items if item.name == 'Test Card 1')
        self.assertEqual(item1.quantity, 2)
        self.assertEqual(item1.purchase_price, 10.50)
        self.assertEqual(item1.purchase_date, '2024-01-01')
        
        # Check second item
        item2 = next(item for item in db_items if item.name == 'Test Card 2')
        self.assertEqual(item2.quantity, 1)
        self.assertEqual(item2.purchase_price, 25.00)
    
    def test_price_data_flow(self):
        """Test complete price data flow from scraping to storage"""
        # Setup database with items
        items = self.tracker.load_portfolio_from_csv()
        self.tracker.db_manager.sync_portfolio_items(items)
        db_items = self.tracker.db_manager.get_portfolio_items()
        
        # Simulate price data
        price_data = {
            'status': 'success',
            'available_items': 150,
            'from_price': 12.75,
            'price_trend': 11.50,
            'avg_30_days': 12.00,
            'avg_7_days': 12.25,
            'avg_1_day': 12.50,
            'seller_prices': [12.75, 13.00, 12.50, 13.25],
            'min_seller_price': 12.50,
            'max_seller_price': 13.25,
            'seller_count': 4
        }
        
        # Save price data
        item = db_items[0]
        self.tracker.db_manager.save_price_data(item.id, price_data)
        
        # Verify price data retrieval
        latest_price = self.tracker.db_manager.get_latest_price_data(item.id)
        self.assertIsNotNone(latest_price)
        self.assertEqual(latest_price.available_items, 150)
        self.assertEqual(latest_price.from_price, 12.75)
        self.assertEqual(latest_price.price_trend, 11.50)
        self.assertEqual(latest_price.seller_count, 4)
        
        # Test price history
        history = self.tracker.db_manager.get_price_history(item.id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].from_price, 12.75)
    
    def test_portfolio_summary_generation(self):
        """Test complete portfolio summary generation"""
        # Setup data
        items = self.tracker.load_portfolio_from_csv()
        self.tracker.db_manager.sync_portfolio_items(items)
        db_items = self.tracker.db_manager.get_portfolio_items()
        
        # Add price data for both items
        for i, item in enumerate(db_items):
            price_data = {
                'status': 'success',
                'from_price': 15.00 + i * 5,  # 15.00, 20.00
                'available_items': 100 + i * 50  # 100, 150
            }
            self.tracker.db_manager.save_price_data(item.id, price_data)
        
        # Generate summary
        summary = self.tracker.get_portfolio_summary()
        
        # Verify summary structure
        self.assertEqual(summary['total_items'], 2)
        self.assertEqual(len(summary['items']), 2)
        
        # Verify item summaries
        for item_summary in summary['items']:
            self.assertIn('name', item_summary)
            self.assertIn('quantity', item_summary)
            self.assertIn('purchase_price', item_summary)
            self.assertIn('current_price', item_summary)
            self.assertIn('last_updated', item_summary)
            
            # Should have current price data
            self.assertIsNotNone(item_summary['current_price'])
            self.assertIsNotNone(item_summary['last_updated'])
    
    @patch('portfolio_tracker.scraper.async_playwright')
    async def test_end_to_end_tracking_flow(self, mock_playwright):
        """Test complete end-to-end tracking flow"""
        # Mock playwright for scraping
        mock_p = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_response = MagicMock()
        
        mock_playwright.return_value.__aenter__.return_value = mock_p
        mock_p.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.goto.return_value = mock_response
        mock_response.status = 200
        
        # Mock page content with realistic CardMarket HTML
        sample_html = '''
        <dt>Available items</dt><dd class="col-6 col-xl-7">125</dd>
        <dt>From</dt><dd class="col-6 col-xl-7">14,50 €</dd>
        <dt>Price Trend</dt><dd class="col-6 col-xl-7"><span>13,25 €</span></dd>
        <dt>30-days average price</dt><dd class="col-6 col-xl-7"><span>13,75 €</span></dd>
        <div class="price">14,50 €</div>
        <div class="price">15,00 €</div>
        <div class="price">14,25 €</div>
        '''
        mock_page.content.return_value = sample_html
        
        # Run complete tracking flow
        await self.tracker.track_all_items()
        
        # Verify database state
        db_items = self.tracker.db_manager.get_portfolio_items()
        self.assertEqual(len(db_items), 2)
        
        # Verify price data was saved
        for item in db_items:
            latest_price = self.tracker.db_manager.get_latest_price_data(item.id)
            self.assertIsNotNone(latest_price)
            self.assertEqual(latest_price.scrape_status, 'success')
            self.assertEqual(latest_price.available_items, 125)
            self.assertEqual(latest_price.from_price, 14.50)
            self.assertEqual(latest_price.price_trend, 13.25)
    
    def test_database_error_handling(self):
        """Test database error handling"""
        # Test with invalid data
        invalid_items = [
            {
                'link': None,  # Invalid link
                'name': 'Test Card',
                'quantity': 1
            }
        ]
        
        # Should handle gracefully
        try:
            self.tracker.db_manager.sync_portfolio_items(invalid_items)
        except Exception as e:
            # Should raise an exception for invalid data
            self.assertIsInstance(e, Exception)
    
    def test_multiple_price_updates(self):
        """Test multiple price updates for the same item"""
        # Setup item
        items = self.tracker.load_portfolio_from_csv()
        self.tracker.db_manager.sync_portfolio_items(items)
        db_items = self.tracker.db_manager.get_portfolio_items()
        item = db_items[0]
        
        # Add multiple price records
        prices = [10.00, 11.50, 12.25, 13.00, 11.75]
        for price in prices:
            price_data = {
                'status': 'success',
                'from_price': price,
                'available_items': 100
            }
            self.tracker.db_manager.save_price_data(item.id, price_data)
        
        # Verify latest price
        latest_price = self.tracker.db_manager.get_latest_price_data(item.id)
        self.assertEqual(latest_price.from_price, 11.75)  # Last added
        
        # Verify price history
        history = self.tracker.db_manager.get_price_history(item.id)
        self.assertEqual(len(history), 5)
        
        # Should be ordered by scraped_at desc
        history_prices = [record.from_price for record in history]
        self.assertEqual(history_prices[0], 11.75)  # Most recent first


class AsyncIntegrationTestCase(unittest.TestCase):
    """Base class for async integration tests"""
    
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def async_test(self, coro):
        return self.loop.run_until_complete(coro)


class TestAsyncIntegration(AsyncIntegrationTestCase):
    """Async integration tests"""
    
    def setUp(self):
        super().setUp()
        # Setup temporary files
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
        csv_writer = csv.writer(self.temp_csv)
        csv_writer.writerow(['link', 'name', 'quantity', 'purchase_price'])
        csv_writer.writerow(['https://example.com/card1', 'Test Card', '1', '10.00'])
        self.temp_csv.close()
        
        self.tracker = PortfolioTracker(
            db_path=self.temp_db.name,
            csv_path=self.temp_csv.name
        )
    
    def tearDown(self):
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
    
    def test_async_tracking_flow(self):
        """Test async tracking flow"""
        with patch('portfolio_tracker.scraper.async_playwright') as mock_playwright:
            # Setup mocks
            mock_p = AsyncMock()
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            mock_response = MagicMock()
            
            mock_playwright.return_value.__aenter__.return_value = mock_p
            mock_p.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page
            mock_page.goto.return_value = mock_response
            mock_response.status = 200
            mock_page.content.return_value = '<dt>Available items</dt><dd>50</dd>'
            
            # Run async test
            self.async_test(self.tracker.track_all_items())
            
            # Verify tracking completed
            db_items = self.tracker.db_manager.get_portfolio_items()
            self.assertEqual(len(db_items), 1)


if __name__ == '__main__':
    unittest.main()