"""
Browserless.io client for cloud-based headless browser automation.
This module provides a wrapper around the Browserless.io API to perform browser automation
in the cloud, which is more reliable for deployment environments like Render.
"""

import os
import json
import time
import asyncio
import requests
from bs4 import BeautifulSoup
import re
from pyppeteer.errors import TimeoutError

class BrowserlessClient:
    """Client for interacting with Browserless.io API"""
    
    def __init__(self, api_key=None):
        """
        Initialize the Browserless client
        
        Args:
            api_key (str, optional): Browserless API key. If not provided, will look for
                                    BROWSERLESS_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get('BROWSERLESS_API_KEY')
        if not self.api_key:
            raise ValueError("Browserless API key is required. Set BROWSERLESS_API_KEY environment variable.")
        
        self.base_url = f"https://chrome.browserless.io"
    
    def scrape_page(self, url, selector=None, wait_for=None, scroll_count=0, scroll_delay=1):
        """
        Scrape a web page using Browserless.io
        
        Args:
            url (str): URL to scrape
            selector (str, optional): CSS selector to wait for before returning HTML
            wait_for (int, optional): Time in milliseconds to wait before returning HTML
            scroll_count (int, optional): Number of times to scroll the page
            scroll_delay (int, optional): Delay between scrolls in seconds
            
        Returns:
            str: HTML content of the page
        """
        print(f"Scraping {url} with Browserless.io")
        
        # Create the function to execute in the browser
        function = """
        async ({ page, context, timeout = 10000 }) => {
            // Set a generous timeout
            await page.setDefaultNavigationTimeout(timeout);
            
            // Navigate to the URL
            await page.goto(context.url, { waitUntil: 'networkidle2' });
            
            // Wait for specific selector if provided
            if (context.selector) {
                try {
                    await page.waitForSelector(context.selector, { timeout });
                } catch (e) {
                    console.log(`Selector ${context.selector} not found, continuing anyway`);
                }
            }
            
            // Wait additional time if specified
            if (context.wait) {
                await new Promise(resolve => setTimeout(resolve, context.wait));
            }
            
            // Scroll the page if requested
            for (let i = 0; i < context.scrollCount; i++) {
                await page.evaluate(() => {
                    window.scrollBy(0, window.innerHeight);
                });
                await new Promise(resolve => setTimeout(resolve, context.scrollDelay * 1000));
            }
            
            // Return the HTML content
            return await page.content();
        }
        """
        
        # Create the context object with parameters
        context = {
            "url": url,
            "selector": selector,
            "wait": wait_for,
            "scrollCount": scroll_count,
            "scrollDelay": scroll_delay
        }
        
        # Make the API request
        endpoint = f"{self.base_url}/function?token={self.api_key}"
        payload = {
            "code": function,
            "context": context
        }
        
        try:
            response = requests.post(endpoint, json=payload, timeout=120)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error scraping with Browserless: {e}")
            return None
    
    def extract_json_from_html(self, html_content):
        """
        Extract embedded JSON data from HTML content
        
        Args:
            html_content (str): HTML content
            
        Returns:
            dict: Extracted JSON data or None if not found
        """
        if not html_content:
            return None
        
        try:
            # Parse the HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for script tags containing JSON data
            json_data = None
            for script in soup.find_all('script'):
                script_text = script.string
                if not script_text:
                    continue
                
                # Look for marketplace listings JSON
                if 'marketplace_search_feed_cards_feedback_actions_renderer' in script_text:
                    # Extract JSON data using regex
                    json_matches = re.findall(r'({.*})', script_text)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if 'require' in data and isinstance(data['require'], list):
                                for item in data['require']:
                                    if isinstance(item, list) and len(item) > 2:
                                        if 'marketplace_search_feed_cards_feedback_actions_renderer' in str(item):
                                            json_data = item[2]
                                            return json_data
                        except:
                            continue
            
            return json_data
        except Exception as e:
            print(f"Error extracting JSON from HTML: {e}")
            return None
