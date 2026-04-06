#!/usr/bin/env python3
"""Quick test of Zillow scraper"""

from zillow_scraper import ZillowScraper

# Test property
test_property = {
    'address': '1234 Ocean Blvd',
    'city': 'Myrtle Beach',
    'price': '$500,000'
}

scraper = ZillowScraper()
result = scraper.enrich_property(test_property)

print("Zillow enrichment test:")
for key, value in result.items():
    print(f"  {key}: {value}")

scraper.cleanup()