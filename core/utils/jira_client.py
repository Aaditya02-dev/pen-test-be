import json
from datetime import datetime

def create_jira(scan, decision):
    """
    Create a JIRA ticket for exploitable vulnerabilities.
    In a real implementation, this would use the JIRA API.
    For now, it just logs the ticket creation.
    """
    ticket = {
        "timestamp": datetime.utcnow().isoformat(),
        "title": f"[EXPLOITABLE] {scan.get('finding')}",
        "description": f"""
Vulnerability Details:
- Scanner: {scan.get('scanner')}
- Host: {scan.get('host')}
- Port: {scan.get('port')}
- Severity: {scan.get('severity')}
- Finding: {scan.get('finding')}
- Summary: {scan.get('summary')}

AI Decision:
{decision}

Action Required: This vulnerability has been validated as exploitable and requires immediate attention.
        """.strip(),
        "severity": scan.get('severity'),
        "host": scan.get('host'),
        "port": scan.get('port'),
        "status": "exploitable"
    }
    
    print(f"\n{'='*60}")
    print(f"[+] JIRA TICKET CREATED")
    print(f"{'='*60}")
    print(f"Title: {ticket['title']}")
    print(f"Host: {scan.get('host')}:{scan.get('port')}")
    print(f"Severity: {scan.get('severity')}")
    print(f"{'='*60}\n")
    
    # Optionally save to a file (simulating JIRA ticket creation)
    try:
        with open("jira_tickets.json", "a") as f:
            f.write(json.dumps(ticket) + "\n")
    except Exception as e:
        print(f"[!] Failed to write ticket: {e}")
    
    return ticket
