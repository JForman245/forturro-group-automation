#!/usr/bin/env python3
"""
Lead tracking and duplicate detection system
Maintains history of previously captured leads to prevent duplicates
"""

import json
import os
import hashlib
from datetime import datetime, timedelta

class LeadTracker:
    def __init__(self):
        self.history_file = "/Users/claw1/.openclaw/workspace/lead_history.json"
        self.load_history()
        
    def load_history(self):
        """Load existing lead history"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            else:
                self.history = {
                    'leads': {},
                    'last_updated': None
                }
        except Exception as e:
            print(f"Error loading lead history: {e}")
            self.history = {'leads': {}, 'last_updated': None}
    
    def save_history(self):
        """Save lead history to file"""
        try:
            self.history['last_updated'] = datetime.now().isoformat()
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving lead history: {e}")
    
    def create_lead_id(self, lead):
        """Create unique ID for a lead based on MLS number and address"""
        identifier = f"{lead.get('mls_number', '')}_{lead.get('address', '')}_{lead.get('city', '')}"
        return hashlib.md5(identifier.encode()).hexdigest()
    
    def is_duplicate(self, lead):
        """Check if lead already exists in history"""
        lead_id = self.create_lead_id(lead)
        return lead_id in self.history['leads']
    
    def add_lead(self, lead):
        """Add new lead to history"""
        lead_id = self.create_lead_id(lead)
        self.history['leads'][lead_id] = {
            'mls_number': lead.get('mls_number'),
            'address': lead.get('address'), 
            'city': lead.get('city'),
            'first_seen': datetime.now().isoformat(),
            'lead_type': lead.get('type'),
            'status': 'new'
        }
    
    def filter_duplicates(self, leads):
        """Filter out duplicate leads from a list"""
        new_leads = []
        duplicate_count = 0
        
        for lead in leads:
            if not self.is_duplicate(lead):
                new_leads.append(lead)
                self.add_lead(lead)
            else:
                duplicate_count += 1
        
        print(f"Filtered out {duplicate_count} duplicate leads")
        print(f"Added {len(new_leads)} new unique leads")
        
        return new_leads
    
    def cleanup_old_leads(self, days_to_keep=90):
        """Remove old leads from history to prevent file from growing too large"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        leads_to_remove = []
        for lead_id, lead_data in self.history['leads'].items():
            try:
                first_seen = datetime.fromisoformat(lead_data['first_seen'])
                if first_seen < cutoff_date:
                    leads_to_remove.append(lead_id)
            except:
                # Remove leads with invalid dates
                leads_to_remove.append(lead_id)
        
        for lead_id in leads_to_remove:
            del self.history['leads'][lead_id]
        
        if leads_to_remove:
            print(f"Cleaned up {len(leads_to_remove)} old leads from history")
    
    def get_stats(self):
        """Get statistics about tracked leads"""
        total_leads = len(self.history['leads'])
        
        # Count by type
        type_counts = {}
        for lead_data in self.history['leads'].values():
            lead_type = lead_data.get('lead_type', 'unknown')
            type_counts[lead_type] = type_counts.get(lead_type, 0) + 1
        
        return {
            'total_tracked': total_leads,
            'by_type': type_counts,
            'last_updated': self.history.get('last_updated')
        }