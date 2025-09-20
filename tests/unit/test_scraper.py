"""Unit tests for scraper module"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from portfolio_tracker.scraper import CardMarketScraper


class TestCardMarketScraper(unittest.TestCase):
    """Test cases for CardMarketScraper"""
    
    def setUp(self):
        """Set up test scraper"""
        self.scraper = CardMarketScraper()
    
    def test_extract_number(self):
        """Test number extraction from HTML"""
        html_text = '<dt>Available items</dt><dd class="col-6 col-xl-7">1,234</dd>'
        pattern = r'Available items</dt><dd[^>]*>(\d+,?\d*)</dd>'
        
        result = self.scraper._extract_number(html_text, pattern)
        self.assertEqual(result, 1234)
    
    def test_extract_number_no_match(self):
        """Test number extraction with no match"""
        html_text = '<dt>Other field</dt><dd>Some text</dd>'
        pattern = r'Available items</dt><dd[^>]*>(\d+)</dd>'
        
        result = self.scraper._extract_number(html_text, pattern)
        self.assertIsNone(result)
    
    def test_extract_price_european_format(self):
        """Test price extraction with European format (comma as decimal)"""
        html_text = '<dt>From</dt><dd class="col-6 col-xl-7">127,50 €</dd>'
        pattern = r'From</dt><dd[^>]*>([\d,]+\.?\d*)\s*€</dd>'
        
        result = self.scraper._extract_price(html_text, pattern)
        self.assertEqual(result, 127.50)
    
    def test_extract_price_thousands_separator(self):
        """Test price extraction with thousands separator"""
        html_text = '<dt>Price</dt><dd>1,234.56 €</dd>'
        pattern = r'Price</dt><dd[^>]*>([\d,]+\.?\d*)\s*€</dd>'
        
        result = self.scraper._extract_price(html_text, pattern)
        self.assertEqual(result, 1234.56)
    
    def test_extract_price_no_match(self):
        """Test price extraction with no match"""
        html_text = '<dt>Other field</dt><dd>Some text</dd>'
        pattern = r'Price</dt><dd[^>]*>([\d,]+\.?\d*)\s*€</dd>'
        
        result = self.scraper._extract_price(html_text, pattern)
        self.assertIsNone(result)
    
    def test_extract_seller_prices(self):
        """Test seller prices extraction"""
        html_text = '''
        <div>12,50 €</div>
        <div>13,00 €</div>
        <div>11,75 €</div>
        <div>5,00 €</div>  <!-- Too low, should be filtered -->
        <div>15000,00 €</div>  <!-- Too high, should be filtered -->
        <div>12,50 €</div>  <!-- Duplicate, should be removed -->
        '''
        
        result = self.scraper._extract_seller_prices(html_text)
        expected = [11.75, 12.50, 13.00]  # Sorted, filtered, deduplicated
        self.assertEqual(result, expected)
    
    def test_extract_seller_prices_empty(self):
        """Test seller prices extraction with no valid prices"""
        html_text = '<div>No prices here</div>'
        
        result = self.scraper._extract_seller_prices(html_text)
        self.assertEqual(result, [])
    
    @patch('portfolio_tracker.scraper.async_playwright')
    async def test_scrape_item_price_success(self, mock_playwright):
        """Test successful item price scraping"""
        # Mock playwright components
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
        
        # Mock page content with sample HTML
        sample_html = '''
        <dt>Available items</dt><dd>100</dd>
        <dt>From</dt><dd>12,50 €</dd>
        <dt>Price Trend</dt><dd><span>11,00 €</span></dd>
        <div>12,50 €</div>
        <div>13,00 €</div>
        '''
        mock_page.content.return_value = sample_html
        
        # Test scraping
        result = await self.scraper.scrape_item_price('https://example.com/magic/card')
        
        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['available_items'], 100)
        self.assertEqual(result['from_price'], 12.50)
        self.assertEqual(result['price_trend'], 11.00)
        self.assertIsInstance(result['seller_prices'], list)
        self.assertEqual(result['seller_count'], len(result['seller_prices']))
    
    @patch('portfolio_tracker.scraper.async_playwright')
    async def test_scrape_item_price_http_error(self, mock_playwright):
        """Test scraping with HTTP error"""
        # Mock playwright components
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
        mock_response.status = 404
        
        # Test scraping
        result = await self.scraper.scrape_item_price('https://example.com/magic/card')
        
        # Verify error result
        self.assertEqual(result['status'], 'error')
        self.assertIn('HTTP 404', result['error'])
    
    @patch('portfolio_tracker.scraper.async_playwright')
    async def test_scrape_item_price_exception(self, mock_playwright):
        """Test scraping with exception"""
        # Mock playwright to raise exception
        mock_playwright.side_effect = Exception("Network error")
        
        # Test scraping
        result = await self.scraper.scrape_item_price('https://example.com/magic/card')
        
        # Verify error result
        self.assertEqual(result['status'], 'error')
        self.assertIn('Network error', result['error'])


class AsyncTestCase(unittest.TestCase):
    """Base class for async test cases"""
    
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def async_test(self, coro):
        return self.loop.run_until_complete(coro)


class TestCardMarketScraperAsync(AsyncTestCase):
    """Async test cases for CardMarketScraper"""
    
    def setUp(self):
        super().setUp()
        self.scraper = CardMarketScraper()
    
    def test_scrape_item_price_success_async(self):
        """Test successful scraping (async version)"""
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
            result = self.async_test(
                self.scraper.scrape_item_price('https://example.com/magic/card')
            )
            
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['available_items'], 50)


if __name__ == '__main__':
    unittest.main()