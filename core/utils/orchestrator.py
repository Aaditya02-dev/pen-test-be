import json
import sys
import os
from dotenv import load_dotenv
from openai import OpenAI

# Add current directory to path for imports when run as script
if __name__ == "__main__":
    from executor import run_script
    from logger import log_result
    from jira_client import create_jira
    from scanner_parser import parse_scanner_output
else:
    # When imported as module, use absolute imports
    from core.utils.executor import run_script
    from core.utils.logger import log_result
    from core.utils.jira_client import create_jira
    from core.utils.scanner_parser import parse_scanner_output

# --------------------------------------------------
# INIT
# --------------------------------------------------
if __name__ == "__main__":
    load_dotenv()
    client = OpenAI()

    print("\n==============================================")
    print(" Gen-AI Vulnerability Validation POC (App Probe)")
    print("==============================================\n")
else:
    # When imported as module, only initialize if needed
    load_dotenv()
    client = OpenAI()

# --------------------------------------------------
# GEN-AI: SCRIPT GENERATION (APPLICATION PROBING)
# --------------------------------------------------
def generate_validation_script(scan):
    """
    Gen-AI generates a SAFE application-probing script
    for a single vulnerability.
    """

    prompt = f"""
You are a security automation assistant.

INPUT (single vulnerability):
{scan}

TASK:
Generate a SAFE Python script to PROBE a web application.

STRICT RULES (MANDATORY):
- Output ONLY valid Python code
- DO NOT include explanations, comments, or markdown
- DO NOT include code fences (```)

SCRIPT REQUIREMENTS:
SCRIPT REQUIREMENTS:
- If the finding mentions "Web Server" or "Unauthenticated":
    - Send HTTP GET requests to / and /admin
- If the finding mentions "SSL" or "TLS":
    - ONLY test if the port is reachable using a socket connection
- Do NOT attempt HTTPS requests unless a service is confirmed
- Print FINAL_STATUS=SUCCESS or FINAL_STATUS=FAILURE
- Do NOT exploit or modify anything
- Capture HTTP status codes
- If ANY endpoint returns HTTP 200 without authentication:
    print FINAL_STATUS=SUCCESS
  else:
    print FINAL_STATUS=FAILURE
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    print(response.choices[0].message.content)
    return response.choices[0].message.content


# --------------------------------------------------
# GEN-AI: RESULT ANALYSIS
# --------------------------------------------------
def analyze_execution_output(execution_output):
    """
    Gen-AI analyzes execution output and decides exploitability.
    """

    prompt = f"""
Execution output:
{execution_output}

RULES:
- FINAL_STATUS=SUCCESS → exploitable
- FINAL_STATUS=FAILURE → not exploitable

Respond ONLY in JSON:
{{
  "exploitable": "yes/no",
  "reason": "short explanation"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    decision = response.choices[0].message.content.strip()
    # print(decision)

    # Safety: strip markdown if model slips
    if decision.startswith("```"):
        decision = decision.split("```")[1].strip()

    return decision


# --------------------------------------------------
# MAIN FLOW
# --------------------------------------------------
if __name__ == "__main__":
    print("[+] Loading raw scanner output...")

    with open("scanner_output.json") as f:
        raw_scan = json.load(f)

    # Normalize scanner output
    vulnerabilities = parse_scanner_output(raw_scan)

    print(f"[+] Vulnerabilities identified: {len(vulnerabilities)}\n")

    # --------------------------------------------------
    # PROCESS EACH VULNERABILITY
    # --------------------------------------------------
    for idx, scan in enumerate(vulnerabilities, start=1):

        print(f"================ Vulnerability {idx} ================")
        print(f"Scanner : {scan.get('scanner')}")
        print(f"Finding : {scan.get('finding')}")
        print(f"Target  : {scan.get('host')}:{scan.get('port')}")
        print(f"Severity: {scan.get('severity')}\n")

        # ----------------------------------------------
        # Gen-AI generates probing script
        # ----------------------------------------------
        print("[+] Feeding vulnerability to Gen-AI (script generation)...")
        script_code = generate_validation_script(scan)

        # SAFETY: clean Gen-AI output
        script_code = script_code.strip()
        if script_code.startswith("```"):
            script_code = script_code.split("```")[1].strip()

        if not script_code:
            print("[!] Empty script generated — skipping vulnerability")
            continue

        with open("validate.py", "w") as f:
            f.write(script_code)

        # ----------------------------------------------
        # Execute script locally
        # ----------------------------------------------
        print("[+] Executing validation script...\n")
        execution_output = run_script("validate.py")

        print("----- Execution Output -----")
        print(execution_output)
        print("----------------------------\n")

        # ----------------------------------------------
        # Gen-AI analyzes execution output
        # ----------------------------------------------
        print("[+] Feeding execution output to Gen-AI (analysis)...")
        decision = analyze_execution_output(execution_output)

        print("[+] Gen-AI Decision:")
        print(decision)
        print()

        # ----------------------------------------------
        # Action
        # ----------------------------------------------
        print("[+] Taking action...\n")

        if '"yes"' in decision.lower():
            create_jira(scan, decision)
        else:
            log_result(scan, decision)
            print("[+] Not exploitable — logged")

    print("\n==============================================")
    print(" POC COMPLETED FOR ALL VULNERABILITIES ")
print("==============================================\n")


def get_vulnerabilities_list():
    """
    Returns a list of vulnerabilities in frontend-ready format
    """
    return [
        {
            'id': 1,
            'severity': 'CRITICAL',
            'name': 'SQL Injection in Login Form',
            'description': 'The login form is vulnerable to SQL injection attacks allowing authentication bypass',
            'host': '192.168.1.50',
            'port': 443,
            'protocol': 'https',
            'scanner': 'Nessus',
            'cve': 'CVE-2023-12345'
        },
        {
            'id': 2,
            'severity': 'HIGH',
            'name': 'Cross-Site Scripting (XSS) Vulnerability',
            'description': 'Reflected XSS vulnerability found in search parameter allowing arbitrary JavaScript execution',
            'host': '192.168.1.50',
            'port': 443,
            'protocol': 'https',
            'scanner': 'Burp Suite',
            'cve': 'CVE-2023-23456'
        },
        {
            'id': 3,
            'severity': 'HIGH',
            'name': 'Remote Code Execution via File Upload',
            'description': 'Unrestricted file upload allows execution of malicious scripts on the server',
            'host': '192.168.1.50',
            'port': 8080,
            'protocol': 'http',
            'scanner': 'OWASP ZAP',
            'cve': 'CVE-2023-34567'
        },
        {
            'id': 4,
            'severity': 'MEDIUM',
            'name': 'Weak SSL/TLS Configuration',
            'description': 'Server supports weak cipher suites and deprecated TLS 1.0 protocol',
            'host': '192.168.1.50',
            'port': 443,
            'protocol': 'https',
            'scanner': 'Nessus',
            'cve': 'CVE-2022-45678'
        },
        {
            'id': 5,
            'severity': 'MEDIUM',
            'name': 'Directory Traversal Vulnerability',
            'description': 'Application allows access to files outside the web root directory',
            'host': '192.168.1.50',
            'port': 8080,
            'protocol': 'http',
            'scanner': 'Nikto',
            'cve': 'CVE-2023-45678'
        },
        {
            'id': 6,
            'severity': 'LOW',
            'name': 'Missing Security Headers',
            'description': 'Server does not implement critical security headers like X-Frame-Options and CSP',
            'host': '192.168.1.50',
            'port': 443,
            'protocol': 'https',
            'scanner': 'OWASP ZAP',
            'cve': 'CVE-2023-56789'
        },
        {
            'id': 7,
            'severity': 'MEDIUM',
            'name': 'Exposed Admin Panel',
            'description': 'Administrative interface is accessible without authentication at /admin endpoint',
            'host': '192.168.1.50',
            'port': 80,
            'protocol': 'http',
            'scanner': 'Nmap',
            'cve': 'CVE-2023-67890'
        }
    ]
