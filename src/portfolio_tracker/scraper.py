"""Web scraper for CardMarket price data"""

import re
import asyncio
import random
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class CardMarketScraper:
    """Scraper for CardMarket website"""
    
    def __init__(self):
        self.base_url = "https://www.cardmarket.com"
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    async def scrape_item_price(self, item_url: str) -> Dict[str, Any]:
        """Scrape price data for a single item"""
        logger.info(f"[SCRAPE] Scraping: {item_url}")
        
        async with async_playwright() as p:
            try:
                # Launch browser with stealth settings
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu'
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=self.user_agent
                )
                
                page = await context.new_page()
                
                # Determine game type from URL
                game_type = "Magic" if "/Magic/" in item_url else "Pokemon"
                
                # Step 1: Visit homepage
                await page.goto(f'{self.base_url}/', wait_until='domcontentloaded')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(random.uniform(1, 2))
                
                # Step 2: Navigate to game section
                game_url = f'{self.base_url}/en/{game_type}'
                await page.goto(game_url, wait_until='domcontentloaded')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(random.uniform(1, 2))
                
                # Step 3: Navigate to product page
                response = await page.goto(item_url, wait_until='domcontentloaded')
                
                if response.status != 200:
                    return {"status": "error", "error": f"HTTP {response.status}"}
                
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(random.uniform(1, 2))
                
                # Extract data
                page_text = await page.content()
                
                # Extract market data using improved regex patterns
                available_items = self._extract_number(page_text, r'Available items</dt><dd[^>]*>(\d+)</dd>')
                from_price = self._extract_price(page_text, r'From</dt><dd[^>]*>([\d,]+\.?\d*)\s*€</dd>')
                price_trend = self._extract_price(page_text, r'Price Trend</dt><dd[^>]*><span>([\d,]+\.?\d*)\s*€</span></dd>')
                avg_30_days = self._extract_price(page_text, r'30-days average price</dt><dd[^>]*><span>([\d,]+\.?\d*)\s*€</span></dd>')
                avg_7_days = self._extract_price(page_text, r'7-days average price</dt><dd[^>]*><span>([\d,]+\.?\d*)\s*€</span></dd>')
                avg_1_day = self._extract_price(page_text, r'1-day average price</dt><dd[^>]*><span>([\d,]+\.?\d*)\s*€</span></dd>')
                
                # Extract individual seller prices
                seller_prices = self._extract_seller_prices(page_text)
                
                result = {
                    "status": "success",
                    "available_items": available_items,
                    "from_price": from_price,
                    "price_trend": price_trend,
                    "avg_30_days": avg_30_days,
                    "avg_7_days": avg_7_days,
                    "avg_1_day": avg_1_day,
                    "seller_prices": seller_prices,
                    "min_seller_price": min(seller_prices) if seller_prices else None,
                    "max_seller_price": max(seller_prices) if seller_prices else None,
                    "seller_count": len(seller_prices),
                    "scraped_at": datetime.utcnow()
                }
                
                await browser.close()
                logger.info(f"[SUCCESS] Successfully scraped: {item_url}")
                return result
                
            except Exception as e:
                logger.error(f"[ERROR] Error scraping {item_url}: {e}")
                return {"status": "error", "error": str(e)}
    
    def _extract_number(self, text: str, pattern: str) -> Optional[int]:
        """Extract number using regex pattern"""
        match = re.search(pattern, text)
        if match:
            return int(match.group(1).replace(',', ''))
        return None
    
    def _extract_price(self, text: str, pattern: str) -> Optional[float]:
        """Extract price using regex pattern"""
        match = re.search(pattern, text)
        if match:
            price_str = match.group(1)
            # Handle European format: 127,00 -> 127.00
            if ',' in price_str and '.' not in price_str:
                price_str = price_str.replace(',', '.')
            # Handle thousands separator: 1,234.56 -> 1234.56
            elif ',' in price_str and '.' in price_str:
                price_str = price_str.replace(',', '')
            return float(price_str)
        return None
    
    def _extract_seller_prices(self, text: str) -> List[float]:
        """Extract individual seller prices"""
        price_pattern = r'(\d+,?\d*\.?\d*)\s*€'
        matches = re.findall(price_pattern, text)
        
        prices = []
        for match in matches:
            try:
                price_str = match
                # Handle European format: 127,00 -> 127.00
                if ',' in price_str and '.' not in price_str:
                    price_str = price_str.replace(',', '.')
                # Handle thousands separator: 1,234.56 -> 1234.56
                elif ',' in price_str and '.' in price_str:
                    price_str = price_str.replace(',', '')
                
                price = float(price_str)
                if 10 <= price <= 10000:  # Reasonable price range
                    prices.append(price)
            except ValueError:
                continue
        
        # Remove duplicates and sort
        unique_prices = sorted(list(set(prices)))
        return unique_prices[:50]  # Limit to 50 prices