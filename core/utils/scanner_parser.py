def parse_scanner_output(raw_scan):
    """
    Normalize raw scanner output (Nessus etc)
    into minimal, token-efficient vulnerability objects.
    """

    trimmed_vulns = []

    scanner_name = raw_scan.get("scan", {}).get("scanner", "unknown")

    for host in raw_scan.get("hosts", []):
        host_name = host.get("hostname") or host.get("ip")

        for v in host.get("vulnerabilities", []):

            trimmed_vulns.append({
                "scanner": scanner_name,
                "host": host_name,
                "port": v.get("port"),
                "protocol": v.get("protocol"),
                "finding": v.get("plugin_name"),
                "severity": v.get("severity"),
                "summary": v.get("description")[:300]  # HARD LIMIT
            })

    return trimmed_vulns
