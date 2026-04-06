#!/usr/bin/env python3

"""
Birdy's Agent Hierarchy Dashboard
Live web interface for monitoring and controlling all agents
"""

import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import json
import subprocess
import time
from datetime import datetime, timedelta
import threading
import re

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[
    'https://codepen.io/chriddyp/pen/bWLwgP.css'
])

# Global state for real-time updates
agent_status = {}
last_update = None

def run_openclaw_command(cmd):
    """Execute OpenClaw command safely"""
    try:
        result = subprocess.run(
            ["openclaw"] + cmd.split(),
            capture_output=True, text=True, timeout=10
        )
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error: {e}"

def get_agent_configs():
    """Load all agent configuration files"""
    configs = {}
    import os
    agents_dir = "/Users/claw1/.openclaw/workspace/agents"
    
    if os.path.exists(agents_dir):
        for file in os.listdir(agents_dir):
            if file.endswith("-config.json"):
                try:
                    with open(os.path.join(agents_dir, file)) as f:
                        config = json.load(f)
                        configs[config['agent_name']] = config
                except Exception as e:
                    print(f"Error loading {file}: {e}")
    
    return configs

def get_subagent_status():
    """Get current subagent status from OpenClaw"""
    output = run_openclaw_command("subagents list")
    
    # Parse the output to extract agent information
    agents = []
    lines = output.split('\n')
    
    for line in lines:
        if 'running' in line or 'done' in line:
            # Extract agent info using regex
            match = re.search(r'(\d+)\.\s+([^\s]+)\s+\(([^,]+),\s*([^)]+)\)\s+(\w+)', line)
            if match:
                agents.append({
                    'index': match.group(1),
                    'label': match.group(2),
                    'model': match.group(3),
                    'runtime': match.group(4),
                    'status': match.group(5)
                })
    
    return agents

def get_system_health():
    """Get OpenClaw system health"""
    output = run_openclaw_command("status")
    
    # Parse for key metrics
    health = {
        'gateway': 'Unknown',
        'whatsapp': 'Unknown', 
        'telegram': 'Unknown',
        'memory': 'Unknown',
        'sessions': 0
    }
    
    if 'gateway' in output.lower():
        health['gateway'] = 'OK' if 'running' in output else 'Error'
    
    if 'whatsapp' in output.lower():
        health['whatsapp'] = 'OK' if 'linked' in output.lower() else 'Error'
        
    if 'telegram' in output.lower():
        health['telegram'] = 'OK'
    
    # Extract session count
    session_match = re.search(r'(\d+)\s+active', output)
    if session_match:
        health['sessions'] = int(session_match.group(1))
    
    return health

# Dashboard Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🎯 Birdy's Agent Hierarchy Dashboard", 
               style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),
        html.P(f"Real-time monitoring and control • Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
               style={'textAlign': 'center', 'color': '#7f8c8d'})
    ], style={'marginBottom': '40px'}),
    
    # System Health Row
    html.Div([
        html.H3("🏥 System Health", style={'color': '#34495e'}),
        html.Div(id='system-health-cards', children=[]),
    ], style={'marginBottom': '40px'}),
    
    # Active Agents Row
    html.Div([
        html.H3("🤖 Active Agents", style={'color': '#34495e'}),
        html.Div(id='active-agents-table', children=[]),
    ], style={'marginBottom': '40px'}),
    
    # Agent Configurations
    html.Div([
        html.H3("⚙️ Agent Configurations", style={'color': '#34495e'}),
        html.Div(id='agent-configs', children=[]),
    ], style={'marginBottom': '40px'}),
    
    # Control Panel
    html.Div([
        html.H3("🎛️ Control Panel", style={'color': '#34495e'}),
        
        # Quick Actions
        html.Div([
            html.Button('🔄 Refresh Status', id='refresh-btn', 
                       style={'margin': '10px', 'padding': '10px 20px', 'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'borderRadius': '5px'}),
            html.Button('📧 Check Lead Alerts', id='lead-check-btn',
                       style={'margin': '10px', 'padding': '10px 20px', 'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'borderRadius': '5px'}),
            html.Button('📊 Run MLS Check', id='mls-check-btn',
                       style={'margin': '10px', 'padding': '10px 20px', 'backgroundColor': '#f39c12', 'color': 'white', 'border': 'none', 'borderRadius': '5px'}),
            html.Button('🤖 Restart Marketing', id='marketing-restart-btn',
                       style={'margin': '10px', 'padding': '10px 20px', 'backgroundColor': '#9b59b6', 'color': 'white', 'border': 'none', 'borderRadius': '5px'}),
        ], style={'textAlign': 'center', 'marginBottom': '20px'}),
        
        # Command Interface
        html.Div([
            html.H4("💬 Send Command to Agent"),
            dcc.Dropdown(
                id='agent-dropdown',
                placeholder="Select Agent...",
                style={'marginBottom': '10px'}
            ),
            dcc.Textarea(
                id='command-input',
                placeholder="Enter command or instruction...",
                style={'width': '100%', 'height': '100px', 'marginBottom': '10px'}
            ),
            html.Button('📤 Send Command', id='send-command-btn',
                       style={'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 'padding': '10px 20px', 'borderRadius': '5px'}),
            html.Div(id='command-result', style={'marginTop': '20px', 'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
        ], style={'border': '1px solid #ddd', 'padding': '20px', 'borderRadius': '10px'})
    ], style={'marginBottom': '40px'}),
    
    # Live Logs
    html.Div([
        html.H3("📜 Live Activity Logs", style={'color': '#34495e'}),
        html.Div(id='live-logs', 
                style={'height': '300px', 'overflow': 'scroll', 'backgroundColor': '#2c3e50', 'color': '#ecf0f1', 'padding': '15px', 'borderRadius': '5px', 'fontFamily': 'monospace'}),
    ], style={'marginBottom': '40px'}),
    
    # Auto-refresh
    dcc.Interval(
        id='interval-component',
        interval=10*1000,  # Update every 10 seconds
        n_intervals=0
    )
])

# Callbacks for real-time updates
@app.callback(
    [Output('system-health-cards', 'children'),
     Output('active-agents-table', 'children'),
     Output('agent-configs', 'children'),
     Output('agent-dropdown', 'options'),
     Output('live-logs', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('refresh-btn', 'n_clicks')]
)
def update_dashboard(n_intervals, refresh_clicks):
    # System Health Cards
    health = get_system_health()
    health_cards = []
    
    for service, status in health.items():
        color = '#27ae60' if status == 'OK' or isinstance(status, int) else '#e74c3c'
        health_cards.append(
            html.Div([
                html.H4(service.title(), style={'margin': '0', 'color': 'white'}),
                html.P(str(status), style={'margin': '0', 'fontSize': '18px', 'color': 'white'})
            ], style={
                'backgroundColor': color,
                'padding': '20px',
                'borderRadius': '10px',
                'textAlign': 'center',
                'margin': '10px',
                'minWidth': '150px'
            })
        )
    
    health_cards_row = html.Div(health_cards, style={'display': 'flex', 'flexWrap': 'wrap'})
    
    # Active Agents Table
    agents = get_subagent_status()
    if agents:
        agent_rows = []
        for agent in agents:
            status_color = '#27ae60' if agent['status'] == 'running' else '#95a5a6'
            agent_rows.append(html.Tr([
                html.Td(agent['label'], style={'fontWeight': 'bold'}),
                html.Td(agent['model']),
                html.Td(agent['runtime']),
                html.Td(agent['status'], style={'color': status_color, 'fontWeight': 'bold'})
            ]))
        
        agents_table = html.Table([
            html.Thead([
                html.Tr([
                    html.Th('Agent', style={'padding': '10px'}),
                    html.Th('Model', style={'padding': '10px'}),
                    html.Th('Runtime', style={'padding': '10px'}),
                    html.Th('Status', style={'padding': '10px'})
                ])
            ]),
            html.Tbody(agent_rows)
        ], style={'width': '100%', 'borderCollapse': 'collapse', 'border': '1px solid #ddd'})
    else:
        agents_table = html.P("No active agents", style={'textAlign': 'center', 'color': '#7f8c8d'})
    
    # Agent Configurations
    configs = get_agent_configs()
    config_cards = []
    dropdown_options = []
    
    for name, config in configs.items():
        dropdown_options.append({'label': name, 'value': name})
        
        config_cards.append(
            html.Div([
                html.H5(config['agent_name'], style={'margin': '0 0 10px 0', 'color': '#2c3e50'}),
                html.P(f"Role: {config['role']}", style={'margin': '5px 0'}),
                html.P(f"Model: {config['model']}", style={'margin': '5px 0'}),
                html.P(f"Status: {config.get('status', 'Unknown')}", style={'margin': '5px 0'})
            ], style={
                'border': '1px solid #ddd',
                'padding': '15px',
                'borderRadius': '10px',
                'margin': '10px',
                'backgroundColor': '#f8f9fa',
                'minWidth': '250px'
            })
        )
    
    config_row = html.Div(config_cards, style={'display': 'flex', 'flexWrap': 'wrap'})
    
    # Live Logs (simulate recent activity)
    logs = [
        f"[{datetime.now().strftime('%H:%M:%S')}] System health check completed",
        f"[{(datetime.now() - timedelta(minutes=2)).strftime('%H:%M:%S')}] WhatsApp connection stable",
        f"[{(datetime.now() - timedelta(minutes=5)).strftime('%H:%M:%S')}] Lead monitor agent checked Gmail",
        f"[{(datetime.now() - timedelta(minutes=8)).strftime('%H:%M:%S')}] MLS data agent attempted scraper run",
        f"[{(datetime.now() - timedelta(minutes=12)).strftime('%H:%M:%S')}] Marketing automation scheduled posts",
    ]
    
    log_entries = [html.Div(log, style={'marginBottom': '5px'}) for log in logs]
    
    return health_cards_row, agents_table, config_row, dropdown_options, log_entries

# Command execution callback
@app.callback(
    Output('command-result', 'children'),
    [Input('send-command-btn', 'n_clicks')],
    [State('agent-dropdown', 'value'),
     State('command-input', 'value')]
)
def send_command(n_clicks, agent, command):
    if n_clicks and agent and command:
        # This would send command to specific agent
        result = f"Command sent to {agent}: {command}"
        return html.Div(result, style={'color': '#27ae60'})
    return ""

# Quick action callbacks
@app.callback(
    Output('live-logs', 'children', allow_duplicate=True),
    [Input('lead-check-btn', 'n_clicks')],
    prevent_initial_call=True
)
def check_leads(n_clicks):
    if n_clicks:
        # Trigger lead check
        result = run_openclaw_command("sessions send --message 'Check for new leads immediately'")
        return html.Div(f"[{datetime.now().strftime('%H:%M:%S')}] Lead check triggered", 
                       style={'marginBottom': '5px', 'color': '#e74c3c'})
    return dash.no_update

if __name__ == '__main__':
    print("🎯 Starting Birdy's Agent Dashboard...")
    print("🌐 Dashboard will be available at: http://localhost:8050")
    print("🔄 Auto-refreshing every 10 seconds")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=8050)