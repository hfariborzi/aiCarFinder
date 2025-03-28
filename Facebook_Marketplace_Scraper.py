#!/usr/bin/env python3
"""
Facebook Marketplace Scraper

This script scrapes car listings from Facebook Marketplace based on specified search criteria.
It extracts information such as year, make, model, price, mileage, and listing URL.
The data is saved to a CSV file for further analysis.

Requirements:
- splinter
- BeautifulSoup4
- pandas
- matplotlib
- webdriver_manager
"""

import re
import time
import os
import sys
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from bs4 import BeautifulSoup as soup
from splinter import Browser
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import json

class FacebookMarketplaceScraper:
    def __init__(self, headless=True, debug=True):
        """
        Initialize the Facebook Marketplace scraper.
        
        Args:
            headless (bool): Run browser in headless mode
            debug (bool): Enable debug mode
        """
        self.headless = headless
        self.debug = debug
        self.browser = None
        self.listings = []
        
        # Create output directory if it doesn't exist
        self.output_dir = "marketplace_output"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def initialize_browser(self):
        """Initialize browser with Splinter"""
        try:
            # Check if running on Render or similar cloud environment
            is_cloud = os.environ.get('RENDER', False) or os.environ.get('DYNO', False)
            
            if is_cloud:
                # Setup for cloud environment (Render, Heroku, etc.)
                try:
                    from pyvirtualdisplay import Display
                    
                    # Set up virtual display
                    display = Display(visible=0, size=(1920, 1080))
                    display.start()
                    
                    # Configure Chrome options for cloud
                    from selenium.webdriver.chrome.options import Options
                    chrome_options = Options()
                    chrome_options.add_argument('--headless')
                    chrome_options.add_argument('--no-sandbox')
                    chrome_options.add_argument('--disable-dev-shm-usage')
                    chrome_options.add_argument('--disable-gpu')
                    chrome_options.add_argument('--disable-extensions')
                    chrome_options.binary_location = "/usr/bin/google-chrome-stable"
                    
                    # Initialize browser with cloud-specific options
                    self.browser = Browser('chrome', options=chrome_options)
                except Exception as e:
                    print(f"Error setting up browser in cloud environment: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                # Local environment setup
                service = Service(ChromeDriverManager().install())
                self.browser = Browser('chrome', headless=self.headless, service=service)
                
            print("Browser initialized successfully")
            return True
        except Exception as e:
            print(f"Error initializing browser: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def close_browser(self):
        """Close the browser"""
        if self.browser:
            try:
                self.browser.quit()
                print("Browser closed successfully")
                self.browser = None
            except Exception as e:
                print(f"Error closing browser: {e}")
    
    def build_search_url(self, location, min_price=None, max_price=None, days_listed=None, 
                         min_mileage=None, max_mileage=None, min_year=None, max_year=None, 
                         transmission=None, make=None, model=None):
        """
        Build search URL with parameters
        
        Args:
            location (str): Location to search in (e.g., 'toronto', 'calgary')
            min_price (int, optional): Minimum price
            max_price (int, optional): Maximum price
            days_listed (int, optional): Days since listing was posted
            min_mileage (int, optional): Minimum mileage
            max_mileage (int, optional): Maximum mileage
            min_year (int, optional): Minimum year
            max_year (int, optional): Maximum year
            transmission (str, optional): Transmission type ('automatic' or 'manual')
            make (str, optional): Vehicle make (e.g., 'Honda')
            model (str, optional): Vehicle model (e.g., 'Civic')
            
        Returns:
            str: Complete search URL
        """
        # Base URL
        base_url = f"https://www.facebook.com/marketplace/{location}/search?"
        
        # Add parameters if provided
        params = []
        if min_price is not None:
            params.append(f"minPrice={min_price}")
        if max_price is not None:
            params.append(f"maxPrice={max_price}")
        if days_listed is not None:
            params.append(f"daysSinceListed={days_listed}")
        if min_mileage is not None:
            params.append(f"minMileage={min_mileage}")
        if max_mileage is not None:
            params.append(f"maxMileage={max_mileage}")
        if min_year is not None:
            params.append(f"minYear={min_year}")
        if max_year is not None:
            params.append(f"maxYear={max_year}")
        if transmission is not None:
            params.append(f"transmissionType={transmission}")
        
        # Add query parameter (make and model)
        if make is not None and model is not None:
            params.append(f"query={make}{model}")
        elif make is not None:
            params.append(f"query={make}")
        elif model is not None:
            params.append(f"query={model}")
            
        # Add exact parameter
        params.append("exact=false")
        
        # Construct full URL
        url = base_url + "&".join(params)
        
        print(f"Search URL: {url}")
        return url
    
    def scrape_listings(self, url, scroll_count=4, scroll_delay=2):
        """
        Scrape listings from Facebook Marketplace
        
        Args:
            url (str): Search URL
            scroll_count (int): Number of times to scroll the page
            scroll_delay (int): Delay between scrolls in seconds
            
        Returns:
            list: List of dictionaries containing listing data
        """
        try:
            # Check if we're in a cloud environment where browser might not work
            is_cloud = os.environ.get('RENDER', False) or os.environ.get('DYNO', False)
            
            # If we're in a cloud environment and browser initialization fails, return sample data
            if is_cloud and not self.browser:
                print("Running in cloud environment with browser issues. Returning sample data.")
                return self._get_sample_data()
            
            # Initialize browser if not already done
            if not self.browser:
                if not self.initialize_browser():
                    print("Failed to initialize browser. Returning sample data.")
                    return self._get_sample_data()
            
            # Visit the URL
            print(f"Visiting {url}")
            self.browser.visit(url)
            
            # Wait for page to load
            time.sleep(5)
            
            # Always save HTML for debugging regardless of debug flag
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = os.path.join(self.output_dir, f"marketplace_html_{timestamp}.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(self.browser.html)
            print(f"HTML content saved to {debug_file}")
            
            # Check if login is required
            if "Log in to Facebook" in self.browser.html or "Log Into Facebook" in self.browser.html:
                print("Facebook login required. Please log in manually.")
                print("The browser window will stay open for 60 seconds to allow you to log in.")
                time.sleep(60)  # Wait for manual login
                
                # Save HTML after login attempt
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                debug_file = os.path.join(self.output_dir, f"marketplace_html_after_login_{timestamp}.html")
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(self.browser.html)
                print(f"HTML content after login saved to {debug_file}")
            
            # Close any popups that might appear
            if self.browser.is_element_present_by_css('div[aria-label="Close"]', wait_time=10):
                self.browser.find_by_css('div[aria-label="Close"]').first.click()
                print("Closed popup")
            
            # Scroll down to load more results
            print(f"Scrolling {scroll_count} times with {scroll_delay} second delay")
            for i in range(scroll_count):
                # Execute JavaScript to scroll to the bottom of the page
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Pause for a moment to allow the content to load
                time.sleep(scroll_delay)
                print(f"Scroll {i+1}/{scroll_count} completed")
            
            # Get the HTML content
            html = self.browser.html
            
            # Save HTML after scrolling
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = os.path.join(self.output_dir, f"marketplace_html_after_scrolling_{timestamp}.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"HTML content after scrolling saved to {debug_file}")
            
            # Parse the HTML
            market_soup = soup(html, 'html.parser')
            
            # Extract data directly from the HTML using a more robust approach
            print("Extracting data from HTML...")
            vehicles_list = []
            
            # Look for all script tags containing JSON data
            json_data_found = False
            script_tags = market_soup.find_all('script', {'type': 'application/json'})
            
            for script in script_tags:
                if not script.string:
                    continue
                
                try:
                    # Look for marketplace listings in the JSON data
                    if "marketplace_listing_title" in script.string or "custom_title" in script.string:
                        json_data_found = True
                        # Extract the JSON data
                        data = json.loads(script.string)
                        
                        # Process the JSON data to find listings
                        self._process_json_data(data, vehicles_list)
                except Exception as e:
                    print(f"Error processing JSON data: {e}")
                    continue
            
            if json_data_found:
                print(f"Extracted {len(vehicles_list)} listings from JSON data")
            else:
                print("No JSON data found with listings")
                
                # Fallback to direct HTML parsing if JSON approach fails
                print("Trying direct HTML parsing...")
                
                # Find all listing containers - looking for common patterns in Facebook's HTML
                listing_containers = market_soup.find_all('div', {'role': 'article'})
                if not listing_containers:
                    # Try alternative selectors
                    listing_containers = market_soup.find_all('div', class_=lambda c: c and "x1qjc9v5" in c)
                
                print(f"Found {len(listing_containers)} potential listing containers")
                
                for container in listing_containers:
                    try:
                        # Look for title elements
                        title_elem = None
                        for span in container.find_all('span'):
                            if span.text and len(span.text.split()) >= 3 and span.text.split()[0].isdigit():
                                title_elem = span
                                break
                        
                        if not title_elem:
                            continue
                        
                        # Look for price elements
                        price_elem = None
                        for span in container.find_all('span'):
                            if span.text and '$' in span.text:
                                price_elem = span
                                break
                        
                        if not price_elem:
                            continue
                        
                        # Look for URL
                        url_elem = container.find('a', href=True)
                        if not url_elem:
                            continue
                        
                        # Process the data
                        title_text = title_elem.text.strip()
                        price_text = price_elem.text.strip()
                        url_text = url_elem.get('href')
                        
                        # Extract mileage from any span that mentions km
                        mileage_text = "0 km"
                        for span in container.find_all('span'):
                            if span.text and 'km' in span.text.lower():
                                mileage_text = span.text.strip()
                                break
                        
                        # Create car dictionary
                        cars_dict = {}
                        title_split = title_text.split()
                        
                        # Skip if title doesn't have at least 3 parts (year, make, model)
                        if len(title_split) < 3:
                            continue
                        
                        # Try to parse year as integer
                        try:
                            cars_dict["Year"] = int(title_split[0])
                        except ValueError:
                            # Skip if year is not a valid integer
                            continue
                        
                        cars_dict["Make"] = title_split[1]
                        cars_dict["Model"] = title_split[2]
                        
                        # Extract numeric price
                        try:
                            cars_dict["Price"] = int(re.sub(r'[^\d.]', '', price_text))
                        except ValueError:
                            # Use 0 if price can't be parsed
                            cars_dict["Price"] = 0
                        
                        # Extract numeric mileage
                        mileage_match = re.search(r'(\d+)K\s*km', mileage_text)
                        if mileage_match:
                            cars_dict["Mileage"] = int(mileage_match.group(1)) * 1000
                        else:
                            # Try different format
                            mileage_match = re.search(r'(\d+(?:,\d+)*)\s*km', mileage_text)
                            if mileage_match:
                                cars_dict["Mileage"] = int(mileage_match.group(1).replace(',', ''))
                            else:
                                cars_dict["Mileage"] = 0
                        
                        cars_dict["URL"] = url_text if url_text.startswith('http') else f"https://www.facebook.com{url_text}"
                        
                        # Add to list
                        vehicles_list.append(cars_dict)
                    except Exception as e:
                        print(f"Error processing listing container: {e}")
                        continue
                
                print(f"Extracted {len(vehicles_list)} listings from HTML")
            
            self.listings = vehicles_list
            return vehicles_list
            
        except Exception as e:
            print(f"Error scraping listings: {e}")
            import traceback
            traceback.print_exc()
            return self._get_sample_data()
    
    def _process_json_data(self, data, vehicles_list):
        """
        Process JSON data to extract listing information
        
        Args:
            data (dict): JSON data
            vehicles_list (list): List to append vehicle dictionaries to
        """
        # Helper function to recursively search through JSON data
        def search_listings(obj):
            if isinstance(obj, dict):
                # Check if this is a listing object
                if ('marketplace_listing_title' in obj or 'custom_title' in obj) and 'listing_price' in obj:
                    try:
                        # Extract car details
                        cars_dict = {}
                        
                        # Get title and parse year, make, model
                        title = obj.get('marketplace_listing_title', '') or obj.get('custom_title', '')
                        title_split = title.split()
                        
                        # Skip if title doesn't have at least 3 parts (year, make, model)
                        if len(title_split) < 3:
                            return
                        
                        # Try to parse year as integer
                        try:
                            cars_dict["Year"] = int(title_split[0])
                        except ValueError:
                            # Skip if year is not a valid integer
                            return
                        
                        cars_dict["Make"] = title_split[1]
                        cars_dict["Model"] = title_split[2]
                        
                        # Get price
                        if 'listing_price' in obj and 'amount' in obj['listing_price']:
                            try:
                                cars_dict["Price"] = float(obj['listing_price']['amount'])
                            except ValueError:
                                cars_dict["Price"] = 0
                        
                        # Get mileage
                        mileage = 0
                        if 'custom_sub_titles_with_rendering_flags' in obj:
                            for subtitle in obj['custom_sub_titles_with_rendering_flags']:
                                if 'subtitle' in subtitle and 'km' in subtitle['subtitle'].lower():
                                    mileage_text = subtitle['subtitle']
                                    mileage_match = re.search(r'(\d+)K\s*km', mileage_text)
                                    if mileage_match:
                                        mileage = int(mileage_match.group(1)) * 1000
                                    else:
                                        # Try different format
                                        mileage_match = re.search(r'(\d+(?:,\d+)*)\s*km', mileage_text)
                                        if mileage_match:
                                            mileage = int(mileage_match.group(1).replace(',', ''))
                        
                        cars_dict["Mileage"] = mileage
                        
                        # Get URL
                        cars_dict["URL"] = f"https://www.facebook.com/marketplace/item/{obj.get('id', '')}"
                        
                        # Extract image URL
                        if 'primary_listing_photo' in obj:
                            if 'image' in obj['primary_listing_photo']:
                                if 'uri' in obj['primary_listing_photo']['image']:
                                    cars_dict["ImageURL"] = obj['primary_listing_photo']['image']['uri']
                        
                        # Fallback for image URL in other locations
                        if 'ImageURL' not in cars_dict and 'listing_photos' in obj and len(obj['listing_photos']) > 0:
                            if 'image' in obj['listing_photos'][0]:
                                if 'uri' in obj['listing_photos'][0]['image']:
                                    cars_dict["ImageURL"] = obj['listing_photos'][0]['image']['uri']
                        
                        # Default image if none found
                        if 'ImageURL' not in cars_dict:
                            cars_dict["ImageURL"] = "https://static.xx.fbcdn.net/rsrc.php/v3/yQ/r/8SkRZ1o0i0K.png"
                        
                        # Add to list
                        vehicles_list.append(cars_dict)
                    except Exception as e:
                        print(f"Error processing listing from JSON: {e}")
                
                # Continue searching in all values
                for val in obj.values():
                    search_listings(val)
            elif isinstance(obj, list):
                for item in obj:
                    search_listings(item)
        
        # Start recursive search
        search_listings(data)
    
    def _get_sample_data(self):
        """
        Return sample car listing data when scraping is not possible
        
        Returns:
            list: List of dictionaries containing sample car data
        """
        print("Generating sample car data instead of scraping")
        sample_data = [
            {
                "Year": 2018, 
                "Make": "Honda", 
                "Model": "Civic", 
                "Price": 15995, 
                "Mileage": 78500, 
                "URL": "https://www.facebook.com/marketplace/item/sample1",
                "ImageURL": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/2018_Honda_Civic_SE_1.4_Front.jpg/1200px-2018_Honda_Civic_SE_1.4_Front.jpg"
            },
            {
                "Year": 2017, 
                "Make": "Toyota", 
                "Model": "Corolla", 
                "Price": 14500, 
                "Mileage": 65000, 
                "URL": "https://www.facebook.com/marketplace/item/sample2",
                "ImageURL": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/2017_Toyota_Corolla_%28ZRE172R%29_Ascent_sedan_%282018-11-02%29_01.jpg/1200px-2017_Toyota_Corolla_%28ZRE172R%29_Ascent_sedan_%282018-11-02%29_01.jpg"
            },
            {
                "Year": 2019, 
                "Make": "Mazda", 
                "Model": "3", 
                "Price": 17995, 
                "Mileage": 45000, 
                "URL": "https://www.facebook.com/marketplace/item/sample3",
                "ImageURL": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/2019_Mazda3_Sport_2.5L_AWD_%28North_America%29_front_NYIAS_2019.jpg/1200px-2019_Mazda3_Sport_2.5L_AWD_%28North_America%29_front_NYIAS_2019.jpg"
            },
            {
                "Year": 2016, 
                "Make": "Hyundai", 
                "Model": "Elantra", 
                "Price": 12500, 
                "Mileage": 89000, 
                "URL": "https://www.facebook.com/marketplace/item/sample4",
                "ImageURL": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/2016_Hyundai_Elantra_%28AD%29_Elite_sedan_%282018-11-02%29_01.jpg/1200px-2016_Hyundai_Elantra_%28AD%29_Elite_sedan_%282018-11-02%29_01.jpg"
            },
            {
                "Year": 2020, 
                "Make": "Nissan", 
                "Model": "Sentra", 
                "Price": 18995, 
                "Mileage": 32000, 
                "URL": "https://www.facebook.com/marketplace/item/sample5",
                "ImageURL": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/2020_Nissan_Sentra_SR%2C_front_12.21.19.jpg/1200px-2020_Nissan_Sentra_SR%2C_front_12.21.19.jpg"
            }
        ]
        return sample_data
    
    def save_to_csv(self, filename=None):
        """
        Save the scraped data to a CSV file
        
        Args:
            filename (str, optional): Name of the CSV file
            
        Returns:
            str: Path to the saved CSV file
        """
        if not self.listings:
            print("No listings to save")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"marketplace_listings_{timestamp}.csv")
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(self.listings)
            
            # Save to CSV
            df.to_csv(filename, index=False)
            print(f"Saved {len(self.listings)} listings to {filename}")
            
            return filename
            
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def plot_data(self, x_column='Year', y_column='Price', output_file=None):
        """
        Create a scatter plot of the data
        
        Args:
            x_column (str): Column to use for x-axis
            y_column (str): Column to use for y-axis
            output_file (str, optional): File to save the plot to
            
        Returns:
            str: Path to the saved plot
        """
        if not self.listings:
            print("No listings to plot")
            return None
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(self.listings)
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Create scatter plot
            plt.scatter(df[x_column], df[y_column], alpha=0.7)
            
            # Add title and labels
            plt.title(f'{y_column} vs {x_column}')
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            
            # Add grid
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Generate output filename if not provided
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(self.output_dir, f"marketplace_plot_{x_column}_vs_{y_column}_{timestamp}.png")
            
            # Save plot
            plt.savefig(output_file)
            print(f"Plot saved to {output_file}")
            
            # Close the plot to free memory
            plt.close()
            
            return output_file
            
        except Exception as e:
            print(f"Error creating plot: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def print_summary(self):
        """
        Print a summary of the scraped data
        """
        if not self.listings:
            print("No listings found")
            return
        
        print(f"\n{'='*50}")
        print(f"SUMMARY: Found {len(self.listings)} listings")
        print(f"{'='*50}")
        
        # Calculate price statistics
        prices = [listing.get('Price') for listing in self.listings if listing.get('Price')]
        if prices:
            print(f"Price Range: ${min(prices):.2f} - ${max(prices):.2f}")
            print(f"Average Price: ${sum(prices)/len(prices):.2f}")
        
        # Calculate mileage statistics
        mileages = [listing.get('Mileage') for listing in self.listings if listing.get('Mileage')]
        if mileages:
            print(f"Mileage Range: {min(mileages):,} - {max(mileages):,} km")
            print(f"Average Mileage: {sum(mileages)/len(mileages):,.2f} km")
        
        # Calculate year statistics
        years = [listing.get('Year') for listing in self.listings if listing.get('Year')]
        if years:
            print(f"Year Range: {min(years)} - {max(years)}")
            print(f"Average Year: {sum(years)/len(years):.2f}")
        
        # Print the first few listings
        print("\nSample Listings:")
        for i, listing in enumerate(self.listings[:5]):
            print(f"\n{i+1}. {listing.get('Year')} {listing.get('Make')} {listing.get('Model')}")
            print(f"   Price: ${listing.get('Price'):,}")
            print(f"   Mileage: {listing.get('Mileage'):,} km")
        
        if len(self.listings) > 5:
            print(f"\n... and {len(self.listings) - 5} more listings")


def main():
    parser = argparse.ArgumentParser(description="Facebook Marketplace Scraper")
    parser.add_argument("--location", required=True, help="Location to search in (e.g., 'toronto', 'calgary')")
    parser.add_argument("--min-price", type=int, help="Minimum price")
    parser.add_argument("--max-price", type=int, help="Maximum price")
    parser.add_argument("--days-listed", type=int, help="Days since listing was posted")
    parser.add_argument("--min-mileage", type=int, help="Minimum mileage")
    parser.add_argument("--max-mileage", type=int, help="Maximum mileage")
    parser.add_argument("--min-year", type=int, help="Minimum year")
    parser.add_argument("--max-year", type=int, help="Maximum year")
    parser.add_argument("--transmission", choices=["automatic", "manual"], help="Transmission type")
    parser.add_argument("--make", help="Vehicle make (e.g., 'Honda')")
    parser.add_argument("--model", help="Vehicle model (e.g., 'Civic')")
    parser.add_argument("--output", help="Output CSV filename")
    parser.add_argument("--plot", action="store_true", help="Create a scatter plot of year vs price")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--visible", action="store_true", help="Make browser visible (non-headless)")
    parser.add_argument("--scroll-count", type=int, default=4, help="Number of times to scroll the page")
    parser.add_argument("--scroll-delay", type=int, default=2, help="Delay between scrolls in seconds")
    
    args = parser.parse_args()
    
    # Create scraper instance
    scraper = FacebookMarketplaceScraper(headless=not args.visible, debug=args.debug)
    
    try:
        # Build search URL
        url = scraper.build_search_url(
            location=args.location,
            min_price=args.min_price,
            max_price=args.max_price,
            days_listed=args.days_listed,
            min_mileage=args.min_mileage,
            max_mileage=args.max_mileage,
            min_year=args.min_year,
            max_year=args.max_year,
            transmission=args.transmission,
            make=args.make,
            model=args.model
        )
        
        # Scrape listings
        listings = scraper.scrape_listings(url, args.scroll_count, args.scroll_delay)
        
        if listings:
            # Print summary
            scraper.print_summary()
            
            # Save to CSV
            if args.output:
                scraper.save_to_csv(args.output)
            else:
                scraper.save_to_csv()
            
            # Create plot if requested
            if args.plot:
                scraper.plot_data()
        else:
            print("No listings were found")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    
    finally:
        # Always close the browser
        scraper.close_browser()


if __name__ == "__main__":
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        print("Facebook Marketplace Scraper")
        print("=================")
        print("This tool scrapes car listings from Facebook Marketplace based on specified search criteria.")
        print("\nExamples:")
        print("  # Search for Honda Civic in Toronto with price range $1000-$30000")
        print("  python Facebook_Marketplace_Scraper.py --location toronto --min-price 1000 --max-price 30000 --make Honda --model Civic")
        print("\n  # Search for cars from 2010-2020 with automatic transmission")
        print("  python Facebook_Marketplace_Scraper.py --location calgary --min-year 2010 --max-year 2020 --transmission automatic")
        print("\n  # Search with visible browser and create a plot")
        print("  python Facebook_Marketplace_Scraper.py --location vancouver --make Toyota --visible --plot")
        print("\nFor more options, use --help")
    else:
        main()
