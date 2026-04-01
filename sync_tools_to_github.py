#!/usr/bin/env python3
"""
Quick sync function for Birdy to backup new tools to GitHub
"""

import sys
import os
sys.path.append('/Users/claw1/.openclaw/workspace')
from auto_commit_tools import GitAutoCommit

def sync_tools(description="New automation tools"):
    """Sync all tools to GitHub with description"""
    syncer = GitAutoCommit()
    syncer.run_auto_sync(description)

if __name__ == "__main__":
    description = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Tool updates"
    sync_tools(description)