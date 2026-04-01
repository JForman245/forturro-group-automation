#!/usr/bin/env python3
"""
CCMLS SolidEarth Lead Scraper
Automated daily lead generation from MLS expired/withdrawn listings
"""

import os
import csv
import json
import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from lead_tracking import LeadTracker
from contact_finder import ContactFinder

class MLSLeadScraper:
    def __init__(self):
        self.load_config()
        self.setup_driver()
        self.leads = []
        self.tracker = LeadTracker()
        self.contact_finder = ContactFinder()
        
    def load_config(self):
        """Load MLS credentials from environment"""
        self.url = os.getenv('MLS_URL')
        self.username = os.getenv('MLS_USERNAME')
        self.password = os.getenv('MLS_PASSWORD')
        self.areas = os.getenv('MLS_AREAS', '').split(',')
        self.areas = [area.strip() for area in self.areas if area.strip()]
        
    def setup_driver(self):
        """Setup headless Chrome driver"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)
        
    def login(self):
        """Login to MLS system"""
        print(f"Logging into MLS at {self.url}")
        self.driver.get(self.url)
        
        try:
            # Wait for login form and fill credentials
            username_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            
            # Submit form
            submit_btn = self.driver.find_element(By.TYPE, "submit")
            submit_btn.click()
            
            # Wait for successful login (dashboard or search page)
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "dashboard")),
                    EC.presence_of_element_located((By.CLASS_NAME, "search")),
                    EC.presence_of_element_located((By.ID, "main-content"))
                )
            )
            print("✅ Successfully logged in")
            return True
            
        except TimeoutException:
            print("❌ Login failed - timeout")
            return False
            
    def search_expired_listings(self):
        """Search for recently expired listings"""
        print("Searching expired listings...")
        
        # Navigate to search
        search_url = self.url.replace('/authenticate', '/search')
        self.driver.get(search_url)
        
        try:
            # Set status filter to Expired
            status_filter = self.wait.until(
                EC.element_to_be_clickable((By.NAME, "status"))
            )
            status_filter.click()
            
            expired_option = self.driver.find_element(By.XPATH, "//option[text()='Expired']")
            expired_option.click()
            
            # Set date range (last 7 days)
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%m/%d/%Y')
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%m/%d/%Y')
            
            date_from = self.driver.find_element(By.NAME, "date_from")
            date_to = self.driver.find_element(By.NAME, "date_to")
            
            date_from.clear()
            date_from.send_keys(week_ago)
            date_to.clear()
            date_to.send_keys(yesterday)
            
            # Submit search
            search_btn = self.driver.find_element(By.TYPE, "submit")
            search_btn.click()
            
            # Extract results
            return self.extract_search_results("expired")
            
        except Exception as e:
            print(f"Error searching expired listings: {e}")
            return []
            
    def search_withdrawn_listings(self):
        """Search for recently withdrawn listings (potential FSBOs)"""
        print("Searching withdrawn listings...")
        
        try:
            # Similar to expired search but for Withdrawn status
            status_filter = self.wait.until(
                EC.element_to_be_clickable((By.NAME, "status"))
            )
            status_filter.click()
            
            withdrawn_option = self.driver.find_element(By.XPATH, "//option[text()='Withdrawn']")
            withdrawn_option.click()
            
            # Set date range (last 30 days for withdrawn)
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%m/%d/%Y')
            month_ago = (datetime.now() - timedelta(days=30)).strftime('%m/%d/%Y')
            
            date_from = self.driver.find_element(By.NAME, "date_from")
            date_to = self.driver.find_element(By.NAME, "date_to")
            
            date_from.clear()
            date_from.send_keys(month_ago)
            date_to.clear()  
            date_to.send_keys(yesterday)
            
            search_btn = self.driver.find_element(By.TYPE, "submit")
            search_btn.click()
            
            return self.extract_search_results("withdrawn")
            
        except Exception as e:
            print(f"Error searching withdrawn listings: {e}")
            return []
            
    def search_price_reductions(self):
        """Search for recent price reductions"""
        print("Searching price reductions...")
        
        try:
            # Look for Active listings with recent price changes
            status_filter = self.wait.until(
                EC.element_to_be_clickable((By.NAME, "status"))
            )
            status_filter.click()
            
            active_option = self.driver.find_element(By.XPATH, "//option[text()='Active']")
            active_option.click()
            
            # Set price change filter if available
            price_change_filter = self.driver.find_element(By.NAME, "price_change")
            if price_change_filter:
                price_change_filter.send_keys("Yes")
            
            search_btn = self.driver.find_element(By.TYPE, "submit")
            search_btn.click()
            
            return self.extract_search_results("price_reduction")
            
        except Exception as e:
            print(f"Error searching price reductions: {e}")
            return []
            
    def extract_search_results(self, lead_type):
        """Extract listing data from search results"""
        leads = []
        
        try:
            # Wait for results table
            results_table = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "results-table"))
            )
            
            rows = results_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
            
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) >= 6:  # Minimum expected columns
                        lead = {
                            'type': lead_type,
                            'mls_number': cells[0].text.strip(),
                            'address': cells[1].text.strip(), 
                            'city': cells[2].text.strip(),
                            'price': cells[3].text.strip(),
                            'beds': cells[4].text.strip(),
                            'baths': cells[5].text.strip(),
                            'sqft': cells[6].text.strip() if len(cells) > 6 else '',
                            'dom': cells[7].text.strip() if len(cells) > 7 else '',
                            'status_date': cells[8].text.strip() if len(cells) > 8 else '',
                            'listing_agent': cells[9].text.strip() if len(cells) > 9 else '',
                            'scraped_date': datetime.now().isoformat(),
                        }
                        
                        # Filter by target areas
                        if self.filter_by_area(lead['city']):
                            leads.append(lead)
                            
                except Exception as e:
                    print(f"Error extracting row data: {e}")
                    continue
                    
        except TimeoutException:
            print("No results found or timeout waiting for results")
            
        print(f"Found {len(leads)} {lead_type} leads")
        return leads
        
    def filter_by_area(self, city):
        """Check if listing is in target areas"""
        if not self.areas:
            return True
            
        city_lower = city.lower()
        for area in self.areas:
            if area.lower() in city_lower:
                return True
        return False
        
    def get_contact_info(self, mls_number):
        """Try to extract owner/contact information"""
        # This would require navigating to individual listing details
        # Implementation depends on MLS structure
        return {
            'owner_name': '',
            'owner_phone': '',
            'owner_email': ''
        }
        
    def save_leads_csv(self):
        """Save leads to CSV file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"/Users/claw1/.openclaw/workspace/mls_leads_{timestamp}.csv"
        
        if not self.leads:
            print("No leads to save")
            return filename
            
        fieldnames = [
            'type', 'mls_number', 'address', 'city', 'price', 'beds', 'baths', 
            'sqft', 'dom', 'status_date', 'listing_agent', 'scraped_date',
            'owner_phone', 'contact_source', 'contact_found'
        ]
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.leads)
            
        print(f"✅ Saved {len(self.leads)} leads to {filename}")
        return filename
        
    def add_to_followup_boss(self):
        """Add leads to Follow Up Boss CRM"""
        if not self.leads:
            print("No leads to add to FUB")
            return
            
        fub_api_key = os.getenv('FUB_API_KEY')
        if not fub_api_key:
            print("No FUB API key found, skipping CRM integration")
            return
            
        success_count = 0
        error_count = 0
        today = datetime.now().strftime('%Y-%m-%d')
            
        for lead in self.leads:
            try:
                # Create meaningful contact name from property address
                address_parts = lead['address'].split(' ')
                property_number = address_parts[0] if address_parts else ''
                street_name = ' '.join(address_parts[1:3]) if len(address_parts) > 1 else ''
                
                # Create FUB contact
                contact_data = {
                    'firstName': f"Owner of {property_number}",
                    'lastName': f"{street_name}, {lead['city']}",
                    'emails': [{'value': lead.get('owner_email', ''), 'type': 'home'}] if lead.get('owner_email') else [],
                    'phones': [{'value': lead.get('owner_phone', ''), 'type': 'mobile'}] if lead.get('owner_phone') else [],
                    'tags': [
                        f'MLS-{lead["type"].title()}',
                        'Daily MLS Leads',
                        f'Found-{today}',
                        f'{lead["city"]}'
                    ],
                    'source': 'MLS Daily Scraper',
                    'customFields': {
                        'property_address': f"{lead['address']}, {lead['city']}",
                        'mls_number': lead['mls_number'],
                        'asking_price': lead['price'],
                        'beds_baths': f"{lead.get('beds', '')}bd/{lead.get('baths', '')}ba",
                        'sqft': lead.get('sqft', ''),
                        'days_on_market': lead.get('dom', ''),
                        'listing_agent': lead.get('listing_agent', ''),
                        'lead_type': lead['type']
                    }
                }
                
                response = requests.post(
                    'https://api.followupboss.com/v1/people',
                    auth=(fub_api_key, ''),
                    json=contact_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 201:
                    success_count += 1
                    print(f"✅ Added {lead['address']} to FUB")
                else:
                    error_count += 1
                    print(f"❌ Failed to add {lead['address']} to FUB: {response.status_code} - {response.text}")
                    
            except Exception as e:
                error_count += 1
                print(f"Error adding lead {lead['address']} to FUB: {e}")
                
        print(f"\nFUB Integration Summary:")
        print(f"✅ Successfully added: {success_count} leads")
        if error_count > 0:
            print(f"❌ Failed: {error_count} leads")
        print(f"📊 Success rate: {(success_count/(success_count+error_count)*100):.1f}%")
                
    def run_daily_scrape(self):
        """Main method to run daily lead scraping"""
        try:
            if not self.login():
                return False
                
            print("Starting lead scraping...")
            
            # Scrape different lead types
            expired_leads = self.search_expired_listings()
            withdrawn_leads = self.search_withdrawn_listings()
            reduction_leads = self.search_price_reductions()
            
            # Combine all leads
            all_leads = expired_leads + withdrawn_leads + reduction_leads
            
            print(f"Total leads found: {len(all_leads)}")
            print(f"- Expired: {len(expired_leads)}")
            print(f"- Withdrawn: {len(withdrawn_leads)}")  
            print(f"- Price Reductions: {len(reduction_leads)}")
            
            # Filter out duplicates
            print("\nFiltering duplicates...")
            self.leads = self.tracker.filter_duplicates(all_leads)
            
            print(f"\nFinal new leads to process: {len(self.leads)}")
            
            # Clean up old leads from history (keep 90 days)
            self.tracker.cleanup_old_leads(90)
            
            # Save tracking history
            self.tracker.save_history()
            
            # Only process if we have new leads
            if self.leads:
                # Enrich leads with contact information
                print("\n📞 ENRICHING LEADS WITH PHONE NUMBERS")
                print("=" * 50)
                self.leads = self.contact_finder.enrich_leads(self.leads)
                
                # Save and process leads
                csv_file = self.save_leads_csv()
                self.add_to_followup_boss()
                
                # Show tracking stats
                stats = self.tracker.get_stats()
                print(f"\nLead tracking stats:")
                print(f"- Total leads in history: {stats['total_tracked']}")
                print(f"- By type: {stats['by_type']}")
                
                return csv_file
            else:
                print("✅ No new leads found today (all were duplicates)")
                return None
            
        except Exception as e:
            print(f"Error in daily scrape: {e}")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
            self.contact_finder.cleanup()

def main():
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')
    
    scraper = MLSLeadScraper()
    result = scraper.run_daily_scrape()
    
    if result:
        print(f"✅ Daily lead scraping completed: {result}")
    elif result is None:
        print("✅ Daily lead scraping completed (no new leads found)")
    else:
        print("❌ Daily lead scraping failed")

if __name__ == "__main__":
    main()