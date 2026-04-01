#!/bin/bash

# Setup daily MLS lead scraping at 6 AM
# This will run every morning and capture ALL expired, withdrawn, and price reduction leads

echo "Setting up daily MLS lead scraper..."

# Create cron job entry
CRON_JOB="0 6 * * * cd /Users/claw1/.openclaw/workspace && /usr/bin/python3 mls_lead_scraper.py >> mls_scraper.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null || echo "") | grep -v "mls_lead_scraper.py" | { cat; echo "$CRON_JOB"; } | crontab -

echo "✅ Daily MLS scraper scheduled for 6:00 AM"
echo "✅ Logs will be saved to: /Users/claw1/.openclaw/workspace/mls_scraper.log"
echo "✅ Lead files will be saved to: /Users/claw1/.openclaw/workspace/mls_leads_YYYYMMDD_HHMM.csv"

# Also create a test run script
cat > /Users/claw1/.openclaw/workspace/test_mls_scraper.sh << 'EOF'
#!/bin/bash
echo "Testing MLS lead scraper..."
cd /Users/claw1/.openclaw/workspace
python3 mls_lead_scraper.py
echo "Test complete. Check output above for results."
EOF

chmod +x /Users/claw1/.openclaw/workspace/test_mls_scraper.sh

echo ""
echo "🚀 MLS LEAD SYSTEM IS READY!"
echo ""
echo "What it will do EVERY MORNING at 6 AM:"
echo "  • Login to your CCMLS account"
echo "  • Search ALL expired listings (last 7 days)"
echo "  • Search ALL withdrawn listings (last 30 days)" 
echo "  • Search ALL price reductions"
echo "  • Filter by your 10 target areas"
echo "  • Extract full property details"
echo "  • Auto-add to Follow Up Boss with tags"
echo "  • Save CSV file for your review"
echo "  • You'll have fresh leads before competitors start their day"
echo ""
echo "Target Areas: Myrtle Beach, N Myrtle Beach, Little River, Longs,"
echo "              Conway, Surfside, Garden City, Murrells Inlet, Aynor, Loris"
echo ""
echo "To test it now, run: ./test_mls_scraper.sh"
echo ""