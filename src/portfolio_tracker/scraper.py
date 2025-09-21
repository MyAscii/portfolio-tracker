"""Web scraper for CardMarket price data"""

import re
import asyncio
import random
import logging
import os
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class CardMarketScraper:
    """Scraper for CardMarket website"""
    
    def __init__(self):
        self.base_url = "https://www.cardmarket.com"
        self.user_agents = [
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            # Chrome on Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            # Safari on Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
            # Chrome on Linux
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Edge on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        ]
        self.is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        logger.info(f"[INIT] Running in GitHub Actions: {self.is_github_actions}")
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent"""
        return random.choice(self.user_agents)
    
    def _get_random_headers(self) -> Dict[str, str]:
        """Get randomized headers to mimic real browser behavior"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice([
                'en-US,en;q=0.9',
                'en-GB,en;q=0.9',
                'en-US,en;q=0.9,de;q=0.8',
                'en-US,en;q=0.9,fr;q=0.8'
            ]),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        return headers
    
    async def scrape_item_price(self, item_url: str) -> Dict[str, Any]:
        """Scrape price data for a single item"""
        logger.info(f"[SCRAPE] Scraping: {item_url}")
        logger.info(f"[DEBUG] GitHub Actions: {self.is_github_actions}")
        
        # Get random user agent and headers for this request
        user_agent = self._get_random_user_agent()
        headers = self._get_random_headers()
        logger.info(f"[DEBUG] Using User-Agent: {user_agent[:50]}...")
        
        async with async_playwright() as p:
            try:
                # Enhanced browser arguments for GitHub Actions with Cloudflare bypass
                browser_args = [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-default-apps',
                    '--disable-sync',
                    '--disable-translate',
                    '--hide-scrollbars',
                    '--mute-audio',
                    '--no-default-browser-check',
                    '--no-pings',
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-client-side-phishing-detection',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-hang-monitor',
                    '--disable-prompt-on-repost',
                    '--disable-web-resources',
                    '--enable-automation=false',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions-except',
                    '--disable-plugins-discovery',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-ipc-flooding-protection',
                    '--disable-domain-reliability',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                ]
                
                # Additional args for GitHub Actions (remove duplicates)
                if self.is_github_actions:
                    browser_args.extend([
                        '--disable-features=TranslateUI',
                        '--force-device-scale-factor=1'
                    ])
                    logger.info("[DEBUG] Added GitHub Actions specific browser args")
                
                browser = await p.chromium.launch(
                    headless=True,
                    args=browser_args
                )
                
                # Create context with randomized settings and stealth mode
                context = await browser.new_context(
                    viewport={
                        'width': random.randint(1200, 1920), 
                        'height': random.randint(800, 1080)
                    },
                    user_agent=user_agent,
                    extra_http_headers={
                        **headers,
                        # Override sec-ch-ua headers to mask headless detection with realistic values
                        'sec-ch-ua': '"Google Chrome";v="130", "Chromium";v="130", "Not?A_Brand";v="99"',
                        'sec-ch-ua-arch': '"x64"',
                        'sec-ch-ua-bitness': '"64"',
                        'sec-ch-ua-full-version': '"130.0.6723.70"',
                        'sec-ch-ua-full-version-list': '"Google Chrome";v="130.0.6723.70", "Chromium";v="130.0.6723.70", "Not?A_Brand";v="99.0.0.0"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-model': '""',
                        'sec-ch-ua-platform': '"Windows"',
                        'sec-ch-ua-platform-version': '"15.0.0"',
                        'sec-ch-ua-wow64': '?0',
                        # Additional realistic headers
                        'sec-ch-prefers-color-scheme': 'light',
                        'sec-ch-prefers-reduced-motion': 'no-preference',
                        'sec-ch-viewport-width': '1920',
                        'sec-ch-device-memory': '8',
                        'sec-ch-dpr': '1',
                        'viewport-width': '1920',
                        'dpr': '1',
                        # Browser hints
                        'save-data': 'off',
                        'downlink': '10',
                        'ect': '4g',
                        'rtt': '50'
                    },
                    java_script_enabled=True,
                    accept_downloads=False,
                    ignore_https_errors=True,
                    locale='en-US',
                    timezone_id='America/New_York',
                    geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                    permissions=['geolocation']
                )
                
                # Add comprehensive stealth mode scripts to mask automation
                 await context.add_init_script("""
                     // Remove webdriver property
                     Object.defineProperty(navigator, 'webdriver', {
                         get: () => undefined,
                     });
                     
                     // Remove automation indicators
                     delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                     delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                     delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                     
                     // Remove additional automation indicators
                     delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                     delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
                     delete window.cdc_adoQpoasnfa76pfcZLmcfl_Function;
                     delete window.cdc_adoQpoasnfa76pfcZLmcfl_String;
                     
                     // Mock chrome property with realistic values
                     window.chrome = {
                         runtime: {
                             onConnect: null,
                             onMessage: null
                         },
                         loadTimes: function() {
                             return {
                                 requestTime: Date.now() / 1000 - Math.random(),
                                 startLoadTime: Date.now() / 1000 - Math.random(),
                                 commitLoadTime: Date.now() / 1000 - Math.random(),
                                 finishDocumentLoadTime: Date.now() / 1000 - Math.random(),
                                 finishLoadTime: Date.now() / 1000 - Math.random(),
                                 firstPaintTime: Date.now() / 1000 - Math.random(),
                                 firstPaintAfterLoadTime: 0,
                                 navigationType: 'Other',
                                 wasFetchedViaSpdy: false,
                                 wasNpnNegotiated: false,
                                 npnNegotiatedProtocol: 'unknown',
                                 wasAlternateProtocolAvailable: false,
                                 connectionInfo: 'http/1.1'
                             };
                         },
                         csi: function() {
                             return {
                                 pageT: Date.now(),
                                 tran: 15
                             };
                         },
                         app: {
                             isInstalled: false,
                             InstallState: {
                                 DISABLED: 'disabled',
                                 INSTALLED: 'installed',
                                 NOT_INSTALLED: 'not_installed'
                             },
                             RunningState: {
                                 CANNOT_RUN: 'cannot_run',
                                 READY_TO_RUN: 'ready_to_run',
                                 RUNNING: 'running'
                             }
                         }
                     };
                     
                     // Mock realistic plugins
                     Object.defineProperty(navigator, 'plugins', {
                         get: () => ({
                             length: 3,
                             0: { 
                                 name: 'Chrome PDF Plugin',
                                 filename: 'internal-pdf-viewer',
                                 description: 'Portable Document Format'
                             },
                             1: { 
                                 name: 'Chrome PDF Viewer',
                                 filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                                 description: ''
                             },
                             2: { 
                                 name: 'Native Client',
                                 filename: 'internal-nacl-plugin',
                                 description: ''
                             }
                         }),
                     });
                     
                     // Mock languages
                     Object.defineProperty(navigator, 'languages', {
                         get: () => ['en-US', 'en'],
                     });
                     
                     // Mock hardware concurrency
                     Object.defineProperty(navigator, 'hardwareConcurrency', {
                         get: () => 4,
                     });
                     
                     // Mock device memory
                     Object.defineProperty(navigator, 'deviceMemory', {
                         get: () => 8,
                     });
                     
                     // Mock connection
                     Object.defineProperty(navigator, 'connection', {
                         get: () => ({
                             effectiveType: '4g',
                             rtt: 50,
                             downlink: 10
                         }),
                     });
                     
                     // Override permissions
                     const originalQuery = window.navigator.permissions.query;
                     window.navigator.permissions.query = (parameters) => (
                         parameters.name === 'notifications' ?
                             Promise.resolve({ state: Notification.permission }) :
                             originalQuery(parameters)
                     );
                     
                     // Mock screen properties
                     Object.defineProperty(screen, 'colorDepth', {
                         get: () => 24,
                     });
                     
                     Object.defineProperty(screen, 'pixelDepth', {
                         get: () => 24,
                     });
                     
                     // Mock realistic screen resolution
                     Object.defineProperty(screen, 'availWidth', {
                         get: () => 1920,
                     });
                     
                     Object.defineProperty(screen, 'availHeight', {
                         get: () => 1040,
                     });
                     
                     // Hide automation from iframe detection
                     Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                         get: function() {
                             return window;
                         }
                     });
                     
                     // Mock Date.prototype.getTimezoneOffset
                     const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
                     Date.prototype.getTimezoneOffset = function() {
                         return 300; // EST timezone
                     };
                     
                     // Override toString methods to hide proxy
                     Function.prototype.toString = new Proxy(Function.prototype.toString, {
                         apply: function(target, thisArg, argumentsList) {
                             if (thisArg === navigator.webdriver) {
                                 return 'function webdriver() { [native code] }';
                             }
                             return target.apply(thisArg, argumentsList);
                         }
                     });
                     
                     // Mock battery API
                     Object.defineProperty(navigator, 'getBattery', {
                         get: () => () => Promise.resolve({
                             charging: true,
                             chargingTime: 0,
                             dischargingTime: Infinity,
                             level: 1
                         }),
                     });
                     
                     // Mock media devices
                     Object.defineProperty(navigator, 'mediaDevices', {
                         get: () => ({
                             enumerateDevices: () => Promise.resolve([
                                 { deviceId: 'default', kind: 'audioinput', label: 'Default - Microphone' },
                                 { deviceId: 'default', kind: 'audiooutput', label: 'Default - Speaker' }
                             ])
                         }),
                     });
                 """)
                
                page = await context.new_page()
                
                # Add request interception for debugging
                async def handle_response(response):
                    if response.url == item_url:
                        logger.info(f"[DEBUG] Response status: {response.status}")
                        logger.info(f"[DEBUG] Response headers: {dict(response.headers)}")
                        if response.status == 403:
                            logger.error(f"[DEBUG] 403 Forbidden for {response.url}")
                            logger.error(f"[DEBUG] Request headers: {dict(response.request.headers)}")
                
                page.on('response', handle_response)
                
                # Determine game type from URL
                game_type = "Magic" if "/Magic/" in item_url else "Pokemon"
                logger.info(f"[DEBUG] Detected game type: {game_type}")
                
                # Step 1: Visit homepage with enhanced delays for GitHub Actions
                logger.info(f"[DEBUG] Step 1: Visiting homepage")
                homepage_response = await page.goto(f'{self.base_url}/', wait_until='domcontentloaded')
                logger.info(f"[DEBUG] Homepage response: {homepage_response.status}")
                await page.wait_for_load_state('networkidle')
                
                # Longer delays for GitHub Actions
                delay = random.uniform(2, 4) if self.is_github_actions else random.uniform(1, 2)
                await asyncio.sleep(delay)
                
                # Step 2: Navigate to game section
                game_url = f'{self.base_url}/en/{game_type}'
                logger.info(f"[DEBUG] Step 2: Visiting game section: {game_url}")
                game_response = await page.goto(game_url, wait_until='domcontentloaded')
                logger.info(f"[DEBUG] Game section response: {game_response.status}")
                await page.wait_for_load_state('networkidle')
                
                delay = random.uniform(2, 4) if self.is_github_actions else random.uniform(1, 2)
                await asyncio.sleep(delay)
                
                # Step 3: Navigate to product page with Cloudflare handling
                logger.info(f"[DEBUG] Step 3: Visiting product page: {item_url}")
                response = await page.goto(item_url, wait_until='domcontentloaded', timeout=30000)
                logger.info(f"[DEBUG] Product page response: {response.status}")
                
                # Handle Cloudflare challenges
                if response.status == 403 or 'cf-mitigated' in dict(response.headers):
                    logger.info("[DEBUG] Detected Cloudflare challenge, waiting for resolution...")
                    
                    # Wait for potential challenge resolution
                    try:
                        await page.wait_for_load_state("networkidle", timeout=15000)
                        await asyncio.sleep(3)  # Additional wait for JS execution
                        
                        # Check if we're still on a challenge page
                        page_content = await page.content()
                        if any(indicator in page_content.lower() for indicator in [
                            'checking your browser', 'cloudflare', 'ddos protection', 
                            'security check', 'please wait', 'ray id', 'challenge'
                        ]):
                            logger.info("[DEBUG] Still on challenge page, waiting longer...")
                            await asyncio.sleep(5)
                            
                            # Try to reload the page
                            logger.info("[DEBUG] Attempting page reload after challenge...")
                            response = await page.reload(wait_until="domcontentloaded", timeout=30000)
                            await page.wait_for_load_state("networkidle", timeout=10000)
                            
                    except Exception as e:
                        logger.warning(f"[DEBUG] Challenge handling failed: {e}")
                
                if response.status != 200:
                    error_msg = f"HTTP {response.status}"
                    logger.error(f"[ERROR] Non-200 response: {error_msg}")
                    
                    # Try to get more details about the error
                    try:
                        page_content = await page.content()
                        if "403" in page_content or "Forbidden" in page_content:
                            logger.error(f"[DEBUG] Page contains 403/Forbidden content")
                        if "blocked" in page_content.lower() or "bot" in page_content.lower():
                            logger.error(f"[DEBUG] Page indicates bot detection")
                    except Exception as content_error:
                        logger.error(f"[DEBUG] Could not read page content: {content_error}")
                    
                    return {"status": "error", "error": error_msg}
                
                await page.wait_for_load_state('networkidle')
                delay = random.uniform(2, 4) if self.is_github_actions else random.uniform(1, 2)
                await asyncio.sleep(delay)
                
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
                error_msg = str(e)
                logger.error(f"[ERROR] Error scraping {item_url}: {error_msg}")
                
                # Enhanced error logging for debugging
                if "403" in error_msg or "Forbidden" in error_msg:
                    logger.error(f"[DEBUG] 403 Forbidden error detected")
                    logger.error(f"[DEBUG] User agent used: {user_agent}")
                    logger.error(f"[DEBUG] GitHub Actions: {self.is_github_actions}")
                elif "timeout" in error_msg.lower():
                    logger.error(f"[DEBUG] Timeout error - may need longer delays")
                elif "connection" in error_msg.lower():
                    logger.error(f"[DEBUG] Connection error - network issue")
                
                return {"status": "error", "error": error_msg}
            
            finally:
                try:
                    await browser.close()
                    logger.info(f"[DEBUG] Browser closed successfully")
                except Exception as close_error:
                     logger.warning(f"[DEBUG] Error closing browser: {close_error}")
    
    async def _fallback_http_scrape(self, item_url: str) -> Dict[str, Any]:
        """Fallback HTTP-based scraping when browser method fails"""
        logger.info(f"[FALLBACK] Attempting HTTP fallback for: {item_url}")
        
        user_agent = self._get_random_user_agent()
        headers = self._get_random_headers()
        headers['User-Agent'] = user_agent
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Add random delay
                await asyncio.sleep(random.uniform(1, 3))
                
                async with session.get(item_url, headers=headers) as response:
                    logger.info(f"[FALLBACK] HTTP response status: {response.status}")
                    
                    if response.status == 403:
                        logger.error(f"[FALLBACK] HTTP 403 - also blocked via direct HTTP")
                        return {"status": "error", "error": "HTTP 403"}
                    elif response.status != 200:
                        return {"status": "error", "error": f"HTTP {response.status}"}
                    
                    content = await response.text()
                    logger.info(f"[FALLBACK] Retrieved {len(content)} characters")
                    
                    # Try to extract basic data from HTML
                    available_items = self._extract_number(content, r'Available items</dt><dd[^>]*>(\d+)</dd>')
                    from_price = self._extract_price(content, r'From</dt><dd[^>]*>([\d,]+\.?\d*)\s*€</dd>')
                    
                    if available_items is not None or from_price is not None:
                        logger.info(f"[FALLBACK] Successfully extracted some data")
                        return {
                            "status": "success",
                            "available_items": available_items,
                            "from_price": from_price,
                            "price_trend": None,
                            "avg_30_days": None,
                            "avg_7_days": None,
                            "avg_1_day": None,
                            "seller_prices": [],
                            "min_seller_price": None,
                            "max_seller_price": None,
                            "seller_count": 0,
                            "scraped_at": datetime.utcnow(),
                            "method": "http_fallback"
                        }
                    else:
                        logger.warning(f"[FALLBACK] Could not extract data from HTTP response")
                        return {"status": "error", "error": "No data extracted"}
                        
        except Exception as e:
            logger.error(f"[FALLBACK] HTTP fallback failed: {e}")
            return {"status": "error", "error": f"Fallback failed: {str(e)}"}
    
    async def scrape_with_fallback(self, item_url: str) -> Dict[str, Any]:
        """Main scraping method with fallback support"""
        # Try browser-based scraping first
        result = await self.scrape_item_price(item_url)
        
        # If browser method fails with 403, try HTTP fallback
        if result.get("status") == "error" and "403" in str(result.get("error", "")):
            logger.info(f"[FALLBACK] Browser method failed with 403, trying HTTP fallback")
            fallback_result = await self._fallback_http_scrape(item_url)
            
            # If fallback also fails, return original error with more context
            if fallback_result.get("status") == "error":
                result["error"] = f"Browser: {result.get('error')}, Fallback: {fallback_result.get('error')}"
                logger.error(f"[FALLBACK] Both methods failed for {item_url}")
            else:
                logger.info(f"[FALLBACK] HTTP fallback succeeded for {item_url}")
                return fallback_result
        
        return result
    
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