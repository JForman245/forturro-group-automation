# Birdy's Agent Hierarchy

## 🎯 Boss Agent: Birdy
**Role:** Strategic oversight, complex decisions, client communication  
**Model:** Claude Opus 4.6 (highest capability)  
**Session:** `agent:main:main`

### Responsibilities:
- Deal analysis and complex negotiations
- Offering Memoranda creation
- Client relationship management
- Emergency escalation handling
- Agent coordination and oversight

---

## 👥 Employee Agents

### 📧 Lead Monitor Agent
**Role:** Gmail monitoring, lead alerts, initial qualification  
**Model:** Claude Haiku (cost-efficient for repetitive tasks)  
**Session:** TBD after initialization  
**Check Frequency:** Every 5 minutes

**Responsibilities:**
- Monitor Dave Ramsey & HomeLight leads
- Send WhatsApp alerts to Forturro Group
- Qualify leads and track response times
- Sync qualified leads to Follow Up Boss
- Escalate high-value opportunities

**Escalation Triggers:**
- Properties >$500k
- Urgent responses needed (<1hr)
- Complex inquiries requiring strategy

---

### 📊 MLS Data Agent  
**Role:** Property data, market analysis, investment opportunities  
**Model:** Claude Sonnet (balanced capability/cost)  
**Session:** TBD after initialization  
**Check Frequency:** Every 2 hours

**Responsibilities:**
- Monitor CCAR MLS for new listings/changes
- Generate comp analysis
- Track market trends
- Identify investment opportunities
- Maintain property database

**Deliverables:**
- Daily market summary
- Weekly comp reports  
- Monthly trend analysis
- Investment opportunity alerts

---

### 🤖 Marketing Automation Agent
**Role:** Social media, marketing materials, transaction monitoring  
**Model:** Claude Haiku (fast execution)  
**Session:** TBD after initialization  
**Execution:** Hourly checks

**Responsibilities:**
- Schedule social media posts (Facebook, LinkedIn, Instagram)
- Create listing flyers via Canva
- Monitor dotloop transactions
- Automate routine marketing tasks
- Track engagement metrics

**Approval Required:**
- Client-specific posts
- Market predictions
- Promotional campaigns
- Paid advertising

---

## 🎛️ Management Interface

### Commands:
```bash
# View all active agents
python3 agent-management-dashboard.py

# Quick status check
openclaw subagents list

# Send message to specific agent
openclaw sessions send --session [session-key] --message "Your instruction"

# Monitor agent activity
openclaw sessions history --session [session-key] --limit 10
```

### Agent Configurations:
- `agents/lead-monitor-config.json`
- `agents/mls-data-config.json` 
- `agents/marketing-automation-config.json`

### Emergency Procedures:
1. **Agent Non-Responsive:** Use `openclaw subagents kill [session]` then respawn
2. **Performance Issues:** Check model allocation and frequency settings
3. **Escalation:** All agents report critical issues to Birdy's main session

---

## 📊 Reporting Structure

**Daily:**
- Lead Monitor: New lead count and response times
- MLS Data: Market activity summary  
- Marketing: Post performance metrics

**Weekly:** 
- Comprehensive performance review
- Agent optimization recommendations
- Cost analysis and model efficiency

**Monthly:**
- ROI analysis across all agents
- Strategic adjustments to agent roles
- Expansion planning for additional agents

---

*Hierarchy initialized: 2026-04-05 10:52 EDT*  
*Boss Agent: Birdy 🐦*