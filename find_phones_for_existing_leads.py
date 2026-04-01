#!/usr/bin/env python3
"""
Find phone numbers for existing leads that don't have contact info
"""

import csv
import json
import os
from contact_finder import ContactFinder
from datetime import datetime

def load_leads_from_csv(csv_file):
    """Load leads from CSV file"""
    leads = []
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                leads.append(row)
        print(f"Loaded {len(leads)} leads from {csv_file}")
        return leads
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return []

def save_enriched_leads(leads, output_file):
    """Save leads with phone numbers to new CSV"""
    if not leads:
        return
        
    fieldnames = [
        'type', 'mls_number', 'address', 'city', 'price', 'beds', 'baths', 
        'sqft', 'dom', 'status_date', 'listing_agent', 'scraped_date',
        'owner_phone', 'contact_source', 'contact_found'
    ]
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads)
    
    print(f"✅ Saved enriched leads to {output_file}")

def main():
    print("📞 PHONE NUMBER ENRICHMENT FOR EXISTING LEADS")
    print("=" * 60)
    
    # Find the most recent lead file
    import glob
    csv_files = glob.glob('/Users/claw1/.openclaw/workspace/mls_leads_*.csv')
    
    if not csv_files:
        print("No existing lead files found.")
        print("Run the MLS scraper first: ./test_mls_scraper.sh")
        return
    
    # Use the most recent file
    latest_file = max(csv_files, key=os.path.getctime)
    print(f"Using latest lead file: {latest_file}")
    
    # Load leads
    leads = load_leads_from_csv(latest_file)
    
    if not leads:
        return
    
    # Filter leads that need phone numbers
    needs_phone = [lead for lead in leads if not lead.get('owner_phone') or lead.get('contact_found') != 'True']
    
    print(f"Found {len(needs_phone)} leads that need phone numbers")
    
    if not needs_phone:
        print("All leads already have phone numbers!")
        return
    
    # Initialize contact finder
    finder = ContactFinder()
    
    try:
        # Enrich leads with contact info
        enriched_leads = finder.enrich_leads(needs_phone)
        
        # Update the original leads list
        enriched_dict = {f"{lead['address']}_{lead['city']}": lead for lead in enriched_leads}
        
        for i, lead in enumerate(leads):
            key = f"{lead['address']}_{lead['city']}"
            if key in enriched_dict:
                leads[i] = enriched_dict[key]
        
        # Save updated leads
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        output_file = f"/Users/claw1/.openclaw/workspace/mls_leads_enriched_{timestamp}.csv"
        save_enriched_leads(leads, output_file)
        
        # Show results
        with_phone = [lead for lead in leads if lead.get('owner_phone')]
        print(f"\n📊 ENRICHMENT RESULTS:")
        print(f"Total leads: {len(leads)}")
        print(f"Now have phone numbers: {len(with_phone)} ({len(with_phone)/len(leads)*100:.1f}%)")
        print(f"Enriched file saved: {output_file}")
        
    finally:
        finder.cleanup()

if __name__ == "__main__":
    main()