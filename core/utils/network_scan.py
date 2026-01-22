import socket
import ipaddress
from datetime import datetime

# Safe, approved ports only
APPROVED_PORTS = [22, 80, 443, 3306, 5432, 8080]
TIMEOUT = 1  # seconds


def is_port_open(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        return sock.connect_ex((str(ip), port)) == 0
    except Exception:
        return False
    finally:
        sock.close()


def port_risk(port):
    if port in [3306, 5432]:
        return "high"
    if port in [22, 8080]:
        return "medium"
    return "low"


def scan_network_to_graph(cidr):
    network = ipaddress.ip_network(cidr, strict=False)

    graph = {
        "meta": {
            "cidr": cidr,
            "scan_time": datetime.utcnow().isoformat()
        },
        "nodes": [],
        "edges": []
    }

    # Network root node
    graph["nodes"].append({
        "id": "network",
        "label": cidr,
        "type": "network"
    })

    for ip in network.hosts():
        open_ports = []

        for port in APPROVED_PORTS:
            if is_port_open(ip, port):
                open_ports.append(port)

        if not open_ports:
            continue

        host_id = str(ip)

        graph["nodes"].append({
            "id": host_id,
            "label": host_id,
            "type": "host"
        })

        graph["edges"].append({
            "from": "network",
            "to": host_id
        })

        for port in open_ports:
            service_id = f"{host_id}:{port}"

            graph["nodes"].append({
                "id": service_id,
                "label": f"Port {port}",
                "type": "service",
                "risk": port_risk(port)
            })

            graph["edges"].append({
                "from": host_id,
                "to": service_id
            })

    return graph


if __name__ == "__main__":
    cidr = "127.0.0.0/30"  # CHANGE FOR CLIENT NETWORK
    graph_output = scan_network_to_graph(cidr)

    print("[+] Network exposure graph generated")
    print(graph_output)
