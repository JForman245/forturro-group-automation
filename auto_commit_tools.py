#!/usr/bin/env python3
"""
Auto-commit new tools and scripts to GitHub repository
Automatically backs up and versions all business automation tools
"""

import os
import subprocess
import json
from datetime import datetime

class GitAutoCommit:
    def __init__(self):
        self.repo_path = "/Users/claw1/.openclaw/workspace/forturro-group-automation"
        self.workspace_path = "/Users/claw1/.openclaw/workspace"
        
    def sync_new_tools(self):
        """Copy any new tools from workspace to repository"""
        print("🔄 Syncing new tools to GitHub repository...")
        
        # Files to monitor and sync
        tool_files = [
            "mls_lead_scraper.py",
            "contact_finder.py", 
            "lead_tracking.py",
            "fub_mls_organizer.py",
            "find_phones_for_existing_leads.py",
            "check_lead_history.py",
            "auto_commit_tools.py",
            "daily_reminder_check.sh",
            # Any new .py or .sh files we create
        ]
        
        copied_files = []
        
        for filename in tool_files:
            workspace_file = os.path.join(self.workspace_path, filename)
            repo_file = os.path.join(self.repo_path, filename)
            
            if os.path.exists(workspace_file):
                # Check if file is newer in workspace
                if not os.path.exists(repo_file) or \
                   os.path.getmtime(workspace_file) > os.path.getmtime(repo_file):
                    
                    subprocess.run(['cp', workspace_file, repo_file])
                    copied_files.append(filename)
                    print(f"  ✅ Updated: {filename}")
        
        # Also copy any new Python scripts
        for file in os.listdir(self.workspace_path):
            if file.endswith('.py') or file.endswith('.sh'):
                workspace_file = os.path.join(self.workspace_path, file)
                repo_file = os.path.join(self.repo_path, file)
                
                if not os.path.exists(repo_file) and file not in tool_files:
                    subprocess.run(['cp', workspace_file, repo_file])
                    copied_files.append(file)
                    print(f"  ✅ New tool: {file}")
        
        return copied_files
    
    def commit_and_push(self, files, description=""):
        """Commit and push changes to GitHub"""
        if not files:
            print("  No new changes to commit")
            return
            
        os.chdir(self.repo_path)
        
        # Add all changes
        subprocess.run(['git', 'add', '.'])
        
        # Create commit message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if description:
            commit_msg = f"Auto-update: {description} [{timestamp}]"
        else:
            commit_msg = f"Auto-update tools: {', '.join(files[:3])}{'...' if len(files) > 3 else ''} [{timestamp}]"
        
        # Commit and push
        try:
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            subprocess.run(['git', 'push'], check=True)
            print(f"  ✅ Committed and pushed: {commit_msg}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Git error: {e}")
            return False
    
    def update_readme_if_needed(self, new_tools):
        """Update README.md if new tools were added"""
        if not new_tools:
            return
            
        # Could add logic here to auto-update README with new tool descriptions
        pass
    
    def run_auto_sync(self, description=""):
        """Main method to sync all tools"""
        print(f"🚀 AUTO-SYNCING TOOLS TO GITHUB")
        print("=" * 50)
        
        try:
            copied_files = self.sync_new_tools()
            
            if copied_files:
                self.update_readme_if_needed(copied_files)
                success = self.commit_and_push(copied_files, description)
                
                if success:
                    print(f"\n✅ Successfully backed up {len(copied_files)} tools to GitHub")
                    print(f"🔗 Repository: https://github.com/JForman245/forturro-group-automation")
                else:
                    print(f"\n❌ Failed to push changes")
            else:
                print(f"\n✅ Repository is up to date")
                
        except Exception as e:
            print(f"❌ Error during auto-sync: {e}")

def main():
    """Manual run for testing"""
    syncer = GitAutoCommit()
    syncer.run_auto_sync("Manual sync test")

if __name__ == "__main__":
    main()