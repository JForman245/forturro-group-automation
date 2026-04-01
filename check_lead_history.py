#!/usr/bin/env python3
"""
Script to check lead tracking history and stats
"""

from lead_tracking import LeadTracker
import json

def main():
    tracker = LeadTracker()
    stats = tracker.get_stats()
    
    print("🔍 LEAD TRACKING HISTORY")
    print("=" * 50)
    print(f"Total leads tracked: {stats['total_tracked']}")
    print(f"Last updated: {stats.get('last_updated', 'Never')}")
    print()
    
    if stats['by_type']:
        print("Leads by type:")
        for lead_type, count in stats['by_type'].items():
            print(f"  • {lead_type}: {count}")
    else:
        print("No leads tracked yet.")
    
    print()
    print("This system will prevent duplicate leads from being:")
    print("  • Added to Follow Up Boss multiple times") 
    print("  • Included in daily CSV exports")
    print("  • Wasting your time calling the same people")
    print()
    print("Duplicates are detected by: MLS Number + Address + City")
    print("History is kept for 90 days, then auto-cleaned.")

if __name__ == "__main__":
    main()