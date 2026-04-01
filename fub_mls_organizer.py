#!/usr/bin/env python3
"""
Follow Up Boss MLS Lead Organizer
View and manage your daily MLS leads in Follow Up Boss
"""

import os
import json
import requests
from datetime import datetime, timedelta

def get_mls_leads_from_fub():
    """Retrieve all MLS leads from Follow Up Boss"""
    fub_api_key = os.getenv('FUB_API_KEY')
    if not fub_api_key:
        print("No FUB API key found")
        return []
    
    try:
        # Search for contacts with MLS tags
        response = requests.get(
            'https://api.followupboss.com/v1/people',
            auth=(fub_api_key, ''),
            params={'tag': 'Daily MLS Leads', 'limit': 1000},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('people', [])
        else:
            print(f"Error fetching leads: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error connecting to FUB: {e}")
        return []

def analyze_mls_leads():
    """Analyze and display MLS lead statistics"""
    print("📊 ANALYZING MLS LEADS IN FOLLOW UP BOSS")
    print("=" * 50)
    
    leads = get_mls_leads_from_fub()
    
    if not leads:
        print("No MLS leads found in Follow Up Boss yet.")
        print("Run the MLS scraper first: ./test_mls_scraper.sh")
        return
    
    print(f"Total MLS leads: {len(leads)}")
    print()
    
    # Analyze by tags
    tag_counts = {}
    city_counts = {}
    date_counts = {}
    
    for lead in leads:
        tags = lead.get('tags', [])
        
        # Count by lead type
        for tag in tags:
            if tag.startswith('MLS-'):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            elif tag.startswith('Found-'):
                date_counts[tag] = date_counts.get(tag, 0) + 1
            elif not tag.startswith('Daily') and not tag.startswith('MLS-') and not tag.startswith('Found-'):
                city_counts[tag] = city_counts.get(tag, 0) + 1
    
    # Display breakdown
    print("By Lead Type:")
    for tag, count in sorted(tag_counts.items()):
        print(f"  • {tag}: {count}")
    print()
    
    print("By City:")
    for city, count in sorted(city_counts.items()):
        if count > 0:  # Only show cities with leads
            print(f"  • {city}: {count}")
    print()
    
    print("By Date Found:")
    for date_tag, count in sorted(date_counts.items(), reverse=True):
        date_str = date_tag.replace('Found-', '')
        print(f"  • {date_str}: {count}")
    print()
    
    # Show recent leads
    print("Recent Leads (Last 5):")
    recent_leads = sorted(leads, key=lambda x: x.get('created', ''), reverse=True)[:5]
    
    for lead in recent_leads:
        name = f"{lead.get('firstName', '')} {lead.get('lastName', '')}".strip()
        custom_fields = lead.get('customFields', {})
        address = custom_fields.get('property_address', 'No address')
        price = custom_fields.get('asking_price', 'No price')
        lead_type = custom_fields.get('lead_type', 'Unknown')
        
        print(f"  • {name} - {address} - ${price} ({lead_type})")

def show_todays_leads():
    """Show leads found today"""
    today = datetime.now().strftime('%Y-%m-%d')
    today_tag = f'Found-{today}'
    
    print(f"🔍 TODAY'S MLS LEADS ({today})")
    print("=" * 40)
    
    leads = get_mls_leads_from_fub()
    todays_leads = [lead for lead in leads if today_tag in lead.get('tags', [])]
    
    if not todays_leads:
        print("No leads found today yet.")
        print("Check back after the 6 AM daily scrape runs.")
        return
    
    print(f"Found {len(todays_leads)} new leads today:\n")
    
    for i, lead in enumerate(todays_leads, 1):
        custom_fields = lead.get('customFields', {})
        address = custom_fields.get('property_address', 'No address')
        price = custom_fields.get('asking_price', 'No price')
        lead_type = custom_fields.get('lead_type', 'Unknown')
        mls_number = custom_fields.get('mls_number', 'No MLS#')
        
        print(f"{i:2d}. {address}")
        print(f"    Price: ${price} | Type: {lead_type} | MLS: {mls_number}")
        print()

def main():
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('/Users/claw1/.openclaw/workspace/.env.fub')
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'today':
        show_todays_leads()
    else:
        analyze_mls_leads()
    
    print()
    print("💡 Tips:")
    print("  • View today's leads: python3 fub_mls_organizer.py today")
    print("  • Filter in FUB by tag: 'Daily MLS Leads' or 'MLS-Expired'")
    print("  • Search by city: Use city name as tag filter")
    print("  • Find recent: Sort by 'Date Created' in FUB")

if __name__ == "__main__":
    main()