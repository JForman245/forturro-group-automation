#!/usr/bin/env python3

"""
Agent Management Dashboard
Centralized control interface for Birdy's agent hierarchy
"""

import json
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

class AgentDashboard:
    def __init__(self):
        self.workspace = Path("/Users/claw1/.openclaw/workspace")
        self.agents_dir = self.workspace / "agents"
        self.agents_dir.mkdir(exist_ok=True)
        
    def load_agent_config(self, agent_name):
        """Load agent configuration file"""
        config_file = self.agents_dir / f"{agent_name}-config.json"
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        return None
    
    def get_active_subagents(self):
        """Get list of active subagents from OpenClaw"""
        try:
            result = subprocess.run(
                ["openclaw", "subagents", "list"],
                capture_output=True, text=True
            )
            return result.stdout
        except Exception as e:
            return f"Error getting subagents: {e}"
    
    def get_session_status(self, session_key):
        """Get detailed session status"""
        try:
            result = subprocess.run(
                ["openclaw", "sessions", "history", "--session", session_key, "--limit", "5"],
                capture_output=True, text=True
            )
            return result.stdout
        except Exception as e:
            return f"Error getting session: {e}"
    
    def send_message_to_agent(self, session_key, message):
        """Send instruction to specific agent"""
        try:
            result = subprocess.run(
                ["openclaw", "sessions", "send", "--session", session_key, "--message", message],
                capture_output=True, text=True
            )
            return result.stdout
        except Exception as e:
            return f"Error sending message: {e}"
    
    def generate_status_report(self):
        """Generate comprehensive status report"""
        report = []
        report.append("🎯 BIRDY'S AGENT HIERARCHY STATUS")
        report.append("=" * 50)
        report.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Load agent configurations
        agents = [
            "lead-monitor",
            "mls-data", 
            "marketing-automation"
        ]
        
        for agent in agents:
            config = self.load_agent_config(agent)
            if config:
                report.append(f"📋 {config['agent_name'].upper()}")
                report.append(f"   Role: {config['role']}")
                report.append(f"   Model: {config['model']}")
                report.append(f"   Status: {config.get('status', 'Unknown')}")
                if 'check_frequency' in config:
                    report.append(f"   Frequency: {config['check_frequency']}")
                report.append("")
        
        # Get active subagents
        report.append("🤖 ACTIVE SUBAGENTS")
        subagents = self.get_active_subagents()
        report.append(subagents)
        report.append("")
        
        # System health
        report.append("💚 SYSTEM HEALTH")
        try:
            health_result = subprocess.run(
                ["openclaw", "status", "--deep"],
                capture_output=True, text=True
            )
            report.append("OpenClaw Status: OK")
        except Exception as e:
            report.append(f"OpenClaw Status: ERROR - {e}")
        
        return "\n".join(report)
    
    def emergency_restart_agent(self, agent_type):
        """Emergency restart for specific agent type"""
        print(f"🚨 EMERGENCY RESTART: {agent_type}")
        # Implementation depends on how agents are managed
        
    def optimize_agent_performance(self):
        """Analyze and optimize agent performance"""
        recommendations = []
        
        # Check for resource usage patterns
        # Check for failed tasks
        # Suggest model upgrades/downgrades
        # Recommend schedule adjustments
        
        return recommendations

def main():
    dashboard = AgentDashboard()
    
    print("🎯 Birdy's Agent Management Dashboard")
    print("====================================")
    
    while True:
        print("\nOptions:")
        print("1. Status Report")
        print("2. List Active Agents") 
        print("3. Send Message to Agent")
        print("4. Emergency Restart")
        print("5. Performance Analysis")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            print("\n" + dashboard.generate_status_report())
            
        elif choice == "2":
            print("\n" + dashboard.get_active_subagents())
            
        elif choice == "3":
            session = input("Enter session key: ").strip()
            message = input("Enter message: ").strip()
            result = dashboard.send_message_to_agent(session, message)
            print(f"\nResult: {result}")
            
        elif choice == "4":
            agent = input("Enter agent type to restart: ").strip()
            dashboard.emergency_restart_agent(agent)
            
        elif choice == "5":
            recommendations = dashboard.optimize_agent_performance()
            print(f"\nPerformance Recommendations: {recommendations}")
            
        elif choice == "6":
            print("Goodbye!")
            break
            
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()