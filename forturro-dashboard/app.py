#!/usr/bin/env python3
"""
Forturro Group Business Dashboard — Backend
Royal Gold Theme Command Center
Port: 8050
"""

import os
import csv
import glob
import json
import subprocess
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

WORKSPACE = '/Users/claw1/.openclaw/workspace'

# Load FUB config
def load_env(path):
    env = {}
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
    return env

fub_env = load_env(os.path.join(WORKSPACE, '.env.fub'))
FUB_API_KEY = fub_env.get('FUB_API_KEY', '')

# ── FUB API Helpers ─────────────────────────────────────────────────────────

def fub_get(endpoint):
    """GET from Follow Up Boss API"""
    import requests
    try:
        resp = requests.get(
            f'https://api.followupboss.com/v1/{endpoint}',
            auth=(FUB_API_KEY, ''),
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"FUB API error ({endpoint}): {e}")
    return None


# ── API Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/deals')
def api_deals():
    """Fetch deals from FUB"""
    # Fetch Jeff's deals only (userId=4), with pagination
    JEFF_USER_ID = 4
    all_deals = []
    next_cursor = None
    for _ in range(10):  # max 10 pages
        url = f'deals?limit=100&userId={JEFF_USER_ID}'
        if next_cursor:
            url += f'&next={next_cursor}'
        data = fub_get(url)
        if not data:
            break
        all_deals.extend(data.get('deals', []))
        next_cursor = data.get('_metadata', {}).get('next')
        if not next_cursor:
            break
    
    if not all_deals:
        return jsonify({'deals': [], 'pipeline': {}, 'closed_ytd': [], 'stats': {}, 'error': 'No deals found'})
    
    # Group by stage
    pipeline = {}
    closed_ytd = []
    current_year = datetime.now().year
    CLOSED_STAGES = {'closed', 'won', 'closed won', 'sold'}
    
    for deal in all_deals:
        stage = deal.get('stageName', '') or 'Unknown'
        pipeline_name = deal.get('pipelineName', '')
        price = deal.get('price', 0) or 0
        status = deal.get('status', '')
        
        try:
            price = float(str(price).replace('$', '').replace(',', ''))
        except:
            price = 0
        
        # Use pipeline + stage for display
        display_stage = f"{pipeline_name} — {stage}" if pipeline_name else stage
        
        deal_info = {
            'id': deal.get('id'),
            'name': deal.get('name', ''),
            'price': price,
            'stage': display_stage,
            'stageName': stage,
            'pipelineName': pipeline_name,
            'status': status,
            'created': deal.get('createdAt', ''),
            'closedAt': deal.get('projectedCloseDate', '') or '',
            'enteredStage': deal.get('enteredStageAt', ''),
            'agent': deal.get('users', [{}])[0].get('name', '') if deal.get('users') else '',
            'contact': deal.get('people', [{}])[0].get('name', '') if deal.get('people') else '',
            'address': deal.get('address', '') or deal.get('name', ''),
            'closingDate': deal.get('projectedCloseDate', '') or deal.get('closedAt', '') or '',
            'peopleRoles': [
                {'name': p.get('name', ''), 'role': 'Seller' if 'seller' in pipeline_name.lower() else 'Buyer' if 'buyer' in pipeline_name.lower() else ''}
                for p in (deal.get('people') or [])
            ],
        }
        
        if display_stage not in pipeline:
            pipeline[display_stage] = []
        pipeline[display_stage].append(deal_info)
        
        # Check if closed this year (YTD resets Jan 1)
        stage_lower = stage.lower()
        is_closed = stage_lower in CLOSED_STAGES or 'closed' in stage_lower or status.lower() == 'won'
        if is_closed:
            # Use createdAt as proxy — check if deal entered closed stage in current year
            entered_stage = deal.get('enteredStageAt', '') or deal.get('createdAt', '')
            if entered_stage and str(current_year) in entered_stage[:4]:
                closed_ytd.append(deal_info)
    
    # Calculate stats
    total_pipeline = sum(d['price'] for deals_list in pipeline.values() for d in deals_list 
                        if d.get('status', '').lower() == 'active')
    ytd_volume = sum(d['price'] for d in closed_ytd)
    ytd_count = len(closed_ytd)
    avg_price = ytd_volume / ytd_count if ytd_count else 0
    active_count = sum(1 for deals_list in pipeline.values() for d in deals_list if d.get('status', '').lower() == 'active')
    
    return jsonify({
        'pipeline': pipeline,
        'closed_ytd': closed_ytd,
        'stats': {
            'pipeline_value': total_pipeline,
            'ytd_volume': ytd_volume,
            'ytd_count': ytd_count,
            'avg_price': avg_price,
            'total_deals': len(all_deals),
            'active_deals': active_count,
        }
    })


@app.route('/api/transactions')
def api_transactions():
    """Fetch active listings and pending/contract deals with all date fields"""
    JEFF_USER_ID = 4
    all_deals = []
    next_cursor = None
    for _ in range(10):
        url = f'deals?limit=100&userId={JEFF_USER_ID}&status=Active'
        if next_cursor:
            url += f'&next={next_cursor}'
        data = fub_get(url)
        if not data:
            break
        all_deals.extend(data.get('deals', []))
        next_cursor = data.get('_metadata', {}).get('next')
        if not next_cursor:
            break
    
    active_listings = []
    pending_deals = []
    
    for d in all_deals:
        stage = d.get('stageName', '')
        pipeline = d.get('pipelineName', '')
        price = d.get('price', 0) or 0
        try:
            price = float(str(price).replace('$', '').replace(',', ''))
        except:
            price = 0
        
        deal_info = {
            'id': d.get('id'),
            'name': d.get('name', ''),
            'price': price,
            'stage': stage,
            'pipeline': pipeline,
            'status': d.get('status', ''),
            'created': d.get('createdAt', ''),
            'contact': d.get('people', [{}])[0].get('name', '') if d.get('people') else '',
            'projectedCloseDate': d.get('projectedCloseDate'),
            'earnestMoneyDueDate': d.get('earnestMoneyDueDate'),
            'dueDiligenceDate': d.get('dueDiligenceDate'),
            'mutualAcceptanceDate': d.get('mutualAcceptanceDate'),
            'finalWalkThroughDate': d.get('finalWalkThroughDate'),
            'possessionDate': d.get('possessionDate'),
        }
        
        if stage == 'Listed':
            active_listings.append(deal_info)
        elif stage in ('Pending', 'Buyer Contract'):
            pending_deals.append(deal_info)
    
    # Sort pending by closest closing date
    def close_sort(d):
        c = d.get('projectedCloseDate') or ''
        return c if c else 'z'
    pending_deals.sort(key=close_sort)
    
    return jsonify({
        'active_listings': active_listings,
        'pending_deals': pending_deals,
    })


@app.route('/api/stale-listings')
def api_stale_listings():
    """Listings on market 200+ days"""
    from datetime import timezone
    JEFF_USER_ID = 4
    all_deals = []
    next_cursor = None
    for _ in range(10):
        url = f'deals?limit=100&userId={JEFF_USER_ID}&status=Active'
        if next_cursor:
            url += f'&next={next_cursor}'
        data = fub_get(url)
        if not data:
            break
        all_deals.extend(data.get('deals', []))
        next_cursor = data.get('_metadata', {}).get('next')
        if not next_cursor:
            break
    
    threshold = int(request.args.get('days', 200))
    now = datetime.now(timezone.utc)
    stale = []
    
    for d in all_deals:
        if d.get('stageName') != 'Listed':
            continue
        created = d.get('createdAt', '')
        if not created:
            continue
        dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
        dom = (now - dt).days
        if dom >= threshold:
            price = d.get('price', 0) or 0
            try:
                price = float(str(price).replace('$', '').replace(',', ''))
            except:
                price = 0
            stale.append({
                'id': d.get('id'),
                'name': d.get('name', ''),
                'price': price,
                'contact': (d.get('people') or [{}])[0].get('name', '') if d.get('people') else '',
                'dom': dom,
                'created': created[:10],
                'pipeline': d.get('pipelineName', ''),
            })
    
    stale.sort(key=lambda x: -x['dom'])
    return jsonify({'stale_listings': stale, 'threshold': threshold, 'count': len(stale)})


@app.route('/api/tasks')
def api_tasks():
    """Fetch tasks from FUB"""
    data = fub_get('tasks?status=open&limit=50&sort=dueDate')
    if not data:
        return jsonify({'tasks': [], 'error': 'Failed to fetch tasks'})
    
    tasks = data.get('tasks', [])
    result = []
    for t in tasks:
        result.append({
            'id': t.get('id'),
            'name': t.get('name', ''),
            'dueDate': t.get('dueDate', ''),
            'assignedTo': t.get('assignedTo', {}).get('name', '') if isinstance(t.get('assignedTo'), dict) else '',
            'isOverdue': t.get('isOverdue', False),
            'personName': t.get('person', {}).get('name', '') if isinstance(t.get('person'), dict) else '',
        })
    
    return jsonify({'tasks': result})


@app.route('/api/calendar')
def api_calendar():
    """Fetch next 7 days from Google Calendar via gog CLI"""
    try:
        result = subprocess.run(
            ['gog', 'calendar', 'list', '--days', '7', '--format', 'json'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            events = json.loads(result.stdout) if result.stdout.strip() else []
            return jsonify({'events': events})
    except Exception as e:
        print(f"Calendar error: {e}")
    
    # Fallback: parse plain text TSV format (ID\tSTART\tEND\tSUMMARY)
    try:
        result = subprocess.run(
            ['gog', 'calendar', 'list', '--days', '7', '--plain'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            events = []
            for line in lines:
                if line.startswith('ID') or not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 4:
                    events.append({
                        'start': parts[1].strip(),
                        'summary': parts[3].strip(),
                        'location': '',
                    })
            return jsonify({'events': events})
    except:
        pass
    
    return jsonify({'events': [], 'error': 'Could not fetch calendar'})


@app.route('/api/mls-stats')
def api_mls_stats():
    """MLS lead statistics from scraper CSVs"""
    # Find all MLS lead CSVs
    mls_files = sorted(glob.glob(os.path.join(WORKSPACE, 'mls_leads_*.csv')))
    enriched_files = sorted(glob.glob(os.path.join(WORKSPACE, 'enriched_leads_*.csv')))
    
    stats = {
        'today': {'total': 0, 'with_phone': 0, 'with_email': 0, 'with_name': 0},
        'history': [],
        'total_all_time': 0,
    }
    
    # Get today's enriched file stats
    if enriched_files:
        latest = enriched_files[-1]
        try:
            with open(latest) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                stats['today']['total'] = len(rows)
                stats['today']['with_phone'] = sum(1 for r in rows if r.get('primary_phone', '').strip() or r.get('Mobile-1', '').strip())
                stats['today']['with_email'] = sum(1 for r in rows if r.get('Email-1', '').strip())
                stats['today']['with_name'] = sum(1 for r in rows if r.get('first_name', '').strip())
        except:
            pass
    elif mls_files:
        latest = mls_files[-1]
        try:
            with open(latest) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                stats['today']['total'] = len(rows)
        except:
            pass
    
    # Build history from all MLS files
    for f in mls_files[-7:]:
        try:
            basename = os.path.basename(f)
            date_part = basename.replace('mls_leads_', '').replace('.csv', '').split('_')[0]
            date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
            with open(f) as fh:
                count = sum(1 for _ in csv.DictReader(fh))
            stats['history'].append({'date': date_str, 'count': count})
        except:
            pass
    
    # Dedup stats
    seen_file = os.path.join(WORKSPACE, 'seen_leads.json')
    if os.path.exists(seen_file):
        try:
            with open(seen_file) as f:
                seen = json.load(f)
                stats['total_all_time'] = len(seen.get('mls_numbers', {}))
        except:
            pass
    
    return jsonify(stats)


@app.route('/api/tracerfy')
def api_tracerfy():
    """Tracerfy credit balance"""
    tracerfy_env = load_env(os.path.join(WORKSPACE, '.env.tracerfy'))
    token = tracerfy_env.get('TRACERFY_API_TOKEN', '')
    if not token:
        return jsonify({'balance': 0, 'error': 'No token'})
    
    import requests
    try:
        resp = requests.get(
            'https://tracerfy.com/v1/api/analytics/',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        if resp.status_code == 200:
            return jsonify(resp.json())
    except:
        pass
    return jsonify({'balance': 0, 'error': 'API error'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)
