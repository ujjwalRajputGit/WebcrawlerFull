import requests
import time
import traceback
import random
from utils.logger import get_logger
from utils.config import TIMEOUT, MAX_RETRIES, USER_AGENT, CRAWL_DELAY
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os

logger = get_logger(__name__)

# Global driver to reuse browser session
_driver = None

def get_driver():
    """
    Initialize or return the existing Selenium WebDriver with appropriate settings.
    Reusing the driver helps maintain cookies and session data.
    """
    global _driver
    if _driver is None:
        logger.info("Initializing Selenium WebDriver")
        try:
            chrome_options = Options()
            # Run headless (no GUI)
            chrome_options.add_argument("--headless")
            # Set window size to appear more like a regular browser
            chrome_options.add_argument("--window-size=1920,1080")
            # Disable images to improve performance
            chrome_options.add_argument("--blink-settings=imagesEnabled=false")
            # Use a realistic user agent
            chrome_options.add_argument(f"--user-agent={USER_AGENT}")
            # Disable automation flags that can be detected
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # Initialize the driver
            _driver = webdriver.Chrome(options=chrome_options)
            
            # Set page load timeout
            _driver.set_page_load_timeout(TIMEOUT)
            
            # Execute JS to hide Selenium/WebDriver traces
            _driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            logger.error(traceback.format_exc())
            raise
    return _driver

def close_driver():
    """Close the WebDriver when no longer needed"""
    global _driver
    if _driver:
        try:
            _driver.quit()
        except:
            pass
        _driver = None

def fetch_page(url: str) -> str:
    """
    Fetches a webpage content given a URL.
    Uses direct HTTP requests first, then falls back to browser automation if needed.
    
    Args:
    - url (str): The URL to fetch.

    Returns:
    - str: The webpage content as a string or None if failed.
    """
    logger.info(f"Fetching page: {url}")
    
    # Try with direct HTTP requests first (original method)
    html_content = fetch_with_requests(url)
    
    # If direct request fails, try with Selenium browser automation
    if html_content is None:
        logger.warning(f"Direct HTTP request failed for {url}, falling back to Selenium browser automation")
        html_content = fetch_with_selenium(url)
    
    return html_content

def fetch_with_selenium(url: str) -> str:
    """
    Fetch page using Selenium WebDriver to bypass bot detection.
    """
    retries = 0
    while retries < MAX_RETRIES:
        try:
            driver = get_driver()
            
            # Add human-like delay to avoid detection
            time.sleep(CRAWL_DELAY + random.uniform(1, 3))
            
            # Load the page
            driver.get(url)
            
            # Wait for page to load (look for body element)
            WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Mimic human scrolling behavior
            mimic_human_behavior(driver)
            
            # Get the page source after JavaScript execution
            html_content = driver.page_source
            
            # Check if we hit a CAPTCHA or robot check
            if 'captcha' in html_content.lower() or 'robot' in html_content.lower() or 'denied' in html_content.lower():
                logger.error(f"CAPTCHA or access denied detected for {url}")
                logger.error(f"Response content preview: {html_content[:500]}...")
                retries += 1
                # Clear cookies and refresh session occasionally
                if retries >= 2:
                    logger.info("Clearing cookies and refreshing session")
                    driver.delete_all_cookies()
                continue
            
            logger.info(f"Successfully fetched {url} with Selenium")
            return html_content
            
        except TimeoutException:
            retries += 1
            logger.error(f"Selenium timeout for {url}")
            
        except WebDriverException as e:
            retries += 1
            logger.error(f"Selenium WebDriver error for {url}: {e}")
            
        except Exception as e:
            retries += 1
            logger.error(f"Unexpected error using Selenium for {url}: {e}")
            logger.error(traceback.format_exc())
        
        # Exponential backoff with jitter
        backoff_time = CRAWL_DELAY * (2 ** retries) * (0.5 + 0.5 * random.random())
        logger.warning(f"Selenium retry {retries}/{MAX_RETRIES} for {url} in {backoff_time:.2f} seconds")
        time.sleep(backoff_time)
    
    logger.error(f"Failed to fetch {url} with Selenium after {MAX_RETRIES} retries")
    return None

def mimic_human_behavior(driver):
    """
    Mimic human browsing behavior to avoid detection.
    """
    try:
        # Get page height
        page_height = driver.execute_script("return document.body.scrollHeight")
        
        # Scroll down gradually
        scroll_pause_time = random.uniform(0.5, 1.5)
        current_position = 0
        step = random.randint(300, 700)  # Random scroll step
        
        while current_position < page_height:
            # Scroll down by a random amount
            current_position += step
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            
            # Add a random pause
            time.sleep(scroll_pause_time)
            
            # Occasionally jiggle the mouse (simulated)
            if random.random() < 0.3:  # 30% chance to jiggle
                driver.execute_script("window.scrollTo(0, {});".format(current_position - random.randint(5, 20)))
                time.sleep(0.1)
                driver.execute_script("window.scrollTo(0, {});".format(current_position))
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(scroll_pause_time)
        
    except Exception as e:
        logger.warning(f"Error while mimicking human behavior: {e}")

def fetch_with_requests(url: str) -> str:
    """
    Fetches a webpage content given a URL with rate limiting.
    
    Args:
    - url (str): The URL to fetch.

    Returns:
    - str: The webpage content as a string or None if failed.
    """
    logger.info(f"Fetching page: {url}")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml",
        "Accept-Language": "en-US,en;q=0.9"
    }
    retries = 0

    # Add delay to respect server resources
    time.sleep(CRAWL_DELAY)

    while retries < MAX_RETRIES:
        try:
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()  # Raise exception for HTTP errors
            return response.text
        except requests.RequestException as e:
            retries += 1
            logger.warning(f"Failed attempt {retries}/{MAX_RETRIES} for {url}: {e}")
            # Exponential backoff
            time.sleep(CRAWL_DELAY * (2 ** retries))

    logger.error(f"Failed to fetch {url} after {MAX_RETRIES} retries.")
    return None