#!/usr/bin/env python3
"""
Contact Finder for MLS Leads
Multi-source phone number and contact info lookup
"""

import requests
import json
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ContactFinder:
    def __init__(self):
        self.setup_driver()
        self.phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        
    def setup_driver(self):
        """Setup headless browser for web scraping"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        self.driver = webdriver.Chrome(options=options)
        
    def clean_phone_number(self, phone):
        """Standardize phone number format"""
        if not phone:
            return None
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        # Must be 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        return None
        
    def search_truepeoplesearch(self, first_name, last_name, address, city, state="SC"):
        """Search TruePeopleSearch for contact info"""
        try:
            print(f"  Searching TruePeopleSearch for {first_name} {last_name}...")
            
            # Build search URL
            search_url = f"https://www.truepeoplesearch.com/results?name={first_name}%20{last_name}&citystatezip={city}%2C%20{state}"
            
            self.driver.get(search_url)
            time.sleep(3)
            
            # Look for phone numbers in results
            phone_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'phone')]")
            
            phones = []
            for element in phone_elements:
                phone_text = element.text
                phone_match = self.phone_pattern.search(phone_text)
                if phone_match:
                    clean_phone = self.clean_phone_number(phone_match.group())
                    if clean_phone:
                        phones.append(clean_phone)
            
            if phones:
                print(f"    ✅ Found phone: {phones[0]}")
                return {'phone': phones[0], 'source': 'TruePeopleSearch'}
            else:
                print(f"    ❌ No phone found")
                return None
                
        except Exception as e:
            print(f"    Error in TruePeopleSearch: {e}")
            return None
            
    def search_fastpeoplesearch(self, first_name, last_name, address, city, state="SC"):
        """Search FastPeopleSearch for contact info"""
        try:
            print(f"  Searching FastPeopleSearch for {first_name} {last_name}...")
            
            search_url = f"https://www.fastpeoplesearch.com/name/{first_name}-{last_name}_{city}-{state}"
            
            self.driver.get(search_url)
            time.sleep(3)
            
            # Look for phone numbers
            phone_elements = self.driver.find_elements(By.XPATH, "//span[contains(text(), '(') and contains(text(), ')')]")
            
            for element in phone_elements:
                phone_text = element.text
                clean_phone = self.clean_phone_number(phone_text)
                if clean_phone:
                    print(f"    ✅ Found phone: {clean_phone}")
                    return {'phone': clean_phone, 'source': 'FastPeopleSearch'}
            
            print(f"    ❌ No phone found")
            return None
            
        except Exception as e:
            print(f"    Error in FastPeopleSearch: {e}")
            return None
    
    def search_whitepages(self, first_name, last_name, address, city, state="SC"):
        """Search Whitepages for contact info"""
        try:
            print(f"  Searching Whitepages for {first_name} {last_name}...")
            
            search_url = f"https://www.whitepages.com/name/{first_name}-{last_name}/{city}-{state}"
            
            self.driver.get(search_url)
            time.sleep(4)
            
            # Look for phone numbers in results
            phone_elements = self.driver.find_elements(By.XPATH, "//a[starts-with(@href, 'tel:')]")
            
            for element in phone_elements:
                phone_text = element.text
                clean_phone = self.clean_phone_number(phone_text)
                if clean_phone:
                    print(f"    ✅ Found phone: {clean_phone}")
                    return {'phone': clean_phone, 'source': 'Whitepages'}
            
            print(f"    ❌ No phone found")
            return None
            
        except Exception as e:
            print(f"    Error in Whitepages: {e}")
            return None
    
    def lookup_property_owner(self, address, city):
        """Look up property owner from public records"""
        try:
            print(f"  Looking up property owner for {address}, {city}...")
            
            # Try Horry County property records
            if city.lower() in ['myrtle beach', 'north myrtle beach', 'surfside beach', 'garden city beach']:
                return self.search_horry_county_records(address)
            # Add other counties as needed
            
            return None
            
        except Exception as e:
            print(f"    Error in property lookup: {e}")
            return None
    
    def search_horry_county_records(self, address):
        """Search Horry County property records for owner info"""
        try:
            # This would need to be customized based on the county website structure
            search_url = f"https://www.horrycounty.org/PropertySearch/"
            
            self.driver.get(search_url)
            time.sleep(2)
            
            # Fill in search form (would need actual form field IDs)
            # This is a template - would need to inspect the actual site
            """
            address_field = self.driver.find_element(By.ID, "address_field")
            address_field.send_keys(address)
            
            search_btn = self.driver.find_element(By.ID, "search_button")
            search_btn.click()
            
            # Wait for results and extract owner name
            owner_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "owner-name"))
            )
            
            owner_name = owner_element.text.strip()
            return owner_name
            """
            
            # For now, return None - this needs site-specific implementation
            return None
            
        except Exception as e:
            print(f"    Error in Horry County search: {e}")
            return None
    
    def find_contact_info(self, lead):
        """Main method to find contact info for a lead"""
        print(f"\n🔍 Finding contact info for {lead.get('address', 'Unknown address')}")
        
        address = lead.get('address', '')
        city = lead.get('city', '')
        
        # First, try to get owner name from property records
        owner_name = self.lookup_property_owner(address, city)
        
        if not owner_name:
            # Generate likely owner names from address
            # Many property owners are "[Number] [Street] LLC" or similar
            address_parts = address.split(' ')
            if len(address_parts) >= 2:
                possible_names = [
                    ('Property', f'Owner {address_parts[0]} {address_parts[1]}'),
                    ('Owner', f'{address}'),
                ]
            else:
                possible_names = [('Property', 'Owner')]
        else:
            # Parse owner name
            name_parts = owner_name.split(' ')
            if len(name_parts) >= 2:
                possible_names = [(name_parts[0], ' '.join(name_parts[1:]))]
            else:
                possible_names = [(owner_name, '')]
        
        # Try multiple search sources for each name possibility
        for first_name, last_name in possible_names:
            print(f"\n  Trying name: {first_name} {last_name}")
            
            # Try TruePeopleSearch
            result = self.search_truepeoplesearch(first_name, last_name, address, city)
            if result:
                return result
            
            time.sleep(2)  # Rate limiting
            
            # Try FastPeopleSearch  
            result = self.search_fastpeoplesearch(first_name, last_name, address, city)
            if result:
                return result
            
            time.sleep(2)
            
            # Try Whitepages
            result = self.search_whitepages(first_name, last_name, address, city)
            if result:
                return result
            
            time.sleep(2)
        
        print(f"  ❌ No contact info found for {address}")
        return None
    
    def enrich_leads(self, leads):
        """Enrich a list of leads with contact information"""
        enriched_leads = []
        
        print(f"🔍 ENRICHING {len(leads)} LEADS WITH CONTACT INFO")
        print("=" * 60)
        
        for i, lead in enumerate(leads, 1):
            print(f"\n[{i}/{len(leads)}] Processing: {lead.get('address', 'Unknown')}")
            
            contact_info = self.find_contact_info(lead)
            
            if contact_info:
                lead['owner_phone'] = contact_info['phone']
                lead['contact_source'] = contact_info['source']
                lead['contact_found'] = True
            else:
                lead['contact_found'] = False
            
            enriched_leads.append(lead)
            
            # Rate limiting between leads
            if i < len(leads):
                print(f"  Waiting 5 seconds before next lookup...")
                time.sleep(5)
        
        found_count = len([lead for lead in enriched_leads if lead.get('contact_found')])
        print(f"\n📊 CONTACT ENRICHMENT COMPLETE")
        print(f"✅ Found contact info: {found_count}/{len(leads)} leads ({found_count/len(leads)*100:.1f}%)")
        
        return enriched_leads
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()

def main():
    """Test the contact finder with sample data"""
    finder = ContactFinder()
    
    try:
        # Test with sample lead
        test_lead = {
            'address': '123 Main St',
            'city': 'Myrtle Beach',
            'mls_number': 'TEST123',
            'price': '$300,000'
        }
        
        contact_info = finder.find_contact_info(test_lead)
        
        if contact_info:
            print(f"\n✅ Test successful!")
            print(f"Phone: {contact_info['phone']}")
            print(f"Source: {contact_info['source']}")
        else:
            print(f"\n❌ No contact info found for test address")
            
    finally:
        finder.cleanup()

if __name__ == "__main__":
    main()