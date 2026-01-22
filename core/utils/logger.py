import json
from datetime import datetime

def log_result(scan, decision):
    """
    Log vulnerability validation results that are not exploitable.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "scanner": scan.get("scanner"),
        "host": scan.get("host"),
        "port": scan.get("port"),
        "finding": scan.get("finding"),
        "severity": scan.get("severity"),
        "decision": decision,
        "status": "not_exploitable"
    }
    
    print(f"[+] Logged: {scan.get('finding')} - Not exploitable")
    
    # Optionally append to a log file
    try:
        with open("validation_log.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[!] Failed to write log: {e}")
