#!/usr/bin/env python3
"""
Zillow Property Data Scraper
Fetches Zestimate, listing price comparison, and property photos from Zillow.
Integrates with MLS lead scraper to enrich property data.
"""

import os
import re
import time
import json
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup


class ZillowScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def search_property(self, address, city="", state="SC"):
        """Search for a property on Zillow and return data"""
        try:
            # Format address for Zillow search
            search_address = f"{address}, {city}, {state}".strip(", ")
            print(f"    Searching Zillow for: {search_address}")
            
            # Zillow search URL
            search_url = f"https://www.zillow.com/homes/{quote(search_address)}_rb/"
            
            response = self.session.get(search_url, timeout=15)
            if response.status_code != 200:
                print(f"    Zillow search failed: HTTP {response.status_code}")
                return {}
            
            # Parse the search results page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for property cards or direct property page
            property_data = self._parse_property_page(soup, response.url)
            
            if not property_data:
                # Try extracting from search results
                property_data = self._parse_search_results(soup)
            
            if property_data:
                property_data['zillow_url'] = response.url
                print(f"    ✅ Found Zillow data for {search_address}")
            else:
                print(f"    ❌ No Zillow data found for {search_address}")
            
            return property_data
            
        except Exception as e:
            print(f"    Zillow search error: {e}")
            return {}
    
    def _parse_property_page(self, soup, url):
        """Parse a direct Zillow property page"""
        try:
            data = {}
            
            # Try to extract JSON data from script tags (Zillow embeds data)
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and 'zestimate' in script.string.lower():
                    # Try to extract JSON data
                    json_match = re.search(r'{"address".*?"listingDataSource"[^}]*}', script.string)
                    if json_match:
                        try:
                            json_data = json.loads(json_match.group())
                            data.update(self._extract_from_json(json_data))
                        except:
                            pass
            
            # Fallback to HTML parsing
            if not data:
                data = self._parse_html_elements(soup)
            
            # Extract photo URLs
            photos = self._extract_photos(soup)
            if photos:
                data['photos'] = photos
            
            return data
            
        except Exception as e:
            print(f"    Property page parse error: {e}")
            return {}
    
    def _parse_search_results(self, soup):
        """Parse Zillow search results page"""
        try:
            # Look for the first property result
            property_cards = soup.find_all(['div', 'article'], attrs={'data-test': 'property-card'})
            
            if not property_cards:
                # Alternative selectors
                property_cards = soup.find_all('div', class_=re.compile(r'property-card|search-result'))
            
            if property_cards:
                return self._parse_property_card(property_cards[0])
            
            return {}
            
        except Exception as e:
            print(f"    Search results parse error: {e}")
            return {}
    
    def _parse_property_card(self, card):
        """Extract data from a property card"""
        try:
            data = {}
            
            # Price elements
            price_elem = card.find(text=re.compile(r'\$[\d,]+'))
            if price_elem:
                data['zillow_price'] = price_elem.strip()
            
            # Zestimate
            zest_elem = card.find(text=re.compile(r'Zestimate.*\$[\d,]+'))
            if zest_elem:
                zest_match = re.search(r'\$[\d,]+', zest_elem)
                if zest_match:
                    data['zestimate'] = zest_match.group()
            
            # Property details
            details = card.find_all(text=re.compile(r'\d+\s+(bed|bath|sqft)'))
            for detail in details:
                if 'bed' in detail.lower():
                    data['beds'] = re.search(r'\d+', detail).group()
                elif 'bath' in detail.lower():
                    data['baths'] = re.search(r'\d+', detail).group()
                elif 'sqft' in detail.lower():
                    data['sqft'] = re.search(r'[\d,]+', detail).group()
            
            return data
            
        except Exception as e:
            print(f"    Property card parse error: {e}")
            return {}
    
    def _parse_html_elements(self, soup):
        """Parse property data from HTML elements"""
        try:
            data = {}
            
            # Look for price elements
            price_selectors = [
                '[data-test="price"]',
                '.price',
                '[class*="price"]'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem and price_elem.text:
                    price_text = price_elem.text.strip()
                    if '$' in price_text:
                        data['zillow_price'] = price_text
                        break
            
            # Look for Zestimate
            zest_selectors = [
                '[data-test="zestimate"]',
                '.zestimate',
                '[class*="zestimate" i]'
            ]
            
            for selector in zest_selectors:
                zest_elem = soup.select_one(selector)
                if zest_elem and zest_elem.text:
                    zest_text = zest_elem.text.strip()
                    zest_match = re.search(r'\$[\d,]+', zest_text)
                    if zest_match:
                        data['zestimate'] = zest_match.group()
                        break
            
            return data
            
        except Exception as e:
            print(f"    HTML parse error: {e}")
            return {}
    
    def _extract_from_json(self, json_data):
        """Extract property data from embedded JSON"""
        try:
            data = {}
            
            if 'zestimate' in json_data:
                data['zestimate'] = f"${json_data['zestimate']:,}"
            
            if 'price' in json_data:
                data['zillow_price'] = f"${json_data['price']:,}"
            
            if 'livingArea' in json_data:
                data['sqft'] = str(json_data['livingArea'])
            
            if 'bedrooms' in json_data:
                data['beds'] = str(json_data['bedrooms'])
                
            if 'bathrooms' in json_data:
                data['baths'] = str(json_data['bathrooms'])
            
            return data
            
        except Exception as e:
            print(f"    JSON extraction error: {e}")
            return {}
    
    def _extract_photos(self, soup):
        """Extract property photo URLs"""
        try:
            photos = []
            
            # Look for image elements
            img_selectors = [
                'img[src*="photos.zillowstatic.com"]',
                'img[data-src*="photos.zillowstatic.com"]',
                '.photo-gallery img',
                '[data-test="photo"] img'
            ]
            
            for selector in img_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src and 'photos.zillowstatic.com' in src:
                        # Clean up the URL to get high-res version
                        clean_url = src.split('?')[0]  # Remove query params
                        if clean_url not in photos:
                            photos.append(clean_url)
                        
                        if len(photos) >= 10:  # Limit to first 10 photos
                            break
                
                if photos:
                    break
            
            return photos[:10]  # Return max 10 photos
            
        except Exception as e:
            print(f"    Photo extraction error: {e}")
            return []
    
    def calculate_price_difference(self, listing_price, zestimate):
        """Calculate difference between listing price and Zestimate"""
        try:
            # Clean price strings
            listing = float(re.sub(r'[^\d.]', '', str(listing_price)))
            zest = float(re.sub(r'[^\d.]', '', str(zestimate)))
            
            if listing and zest:
                diff_amount = listing - zest
                diff_percent = (diff_amount / zest) * 100
                
                return {
                    'price_difference': f"${diff_amount:,.0f}",
                    'price_difference_percent': f"{diff_percent:+.1f}%",
                    'listing_vs_zestimate': f"{'Above' if diff_amount > 0 else 'Below'} Zestimate"
                }
        except Exception as e:
            print(f"    Price calculation error: {e}")
        
        return {}
    
    def enrich_property(self, property_data):
        """Enrich a single property with Zillow data"""
        address = property_data.get('address', '')
        city = property_data.get('city', '')
        
        if not address:
            return property_data
        
        # Search Zillow
        zillow_data = self.search_property(address, city)
        
        if zillow_data:
            # Add Zillow data to property
            property_data.update(zillow_data)
            
            # Calculate price comparison
            listing_price = property_data.get('price', '')
            zestimate = zillow_data.get('zestimate', '')
            
            if listing_price and zestimate:
                price_comparison = self.calculate_price_difference(listing_price, zestimate)
                property_data.update(price_comparison)
        
        # Rate limiting
        time.sleep(2)
        
        return property_data
    
    def cleanup(self):
        """Close session"""
        self.session.close()


if __name__ == "__main__":
    # Test the Zillow scraper
    scraper = ZillowScraper()
    
    test_property = {
        'address': '1234 Ocean Blvd',
        'city': 'Myrtle Beach',
        'price': '$500,000'
    }
    
    enriched = scraper.enrich_property(test_property)
    print(json.dumps(enriched, indent=2))
    
    scraper.cleanup()