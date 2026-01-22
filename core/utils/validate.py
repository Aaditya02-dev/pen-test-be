import socket
import requests

host = 'localhost'
port = 443

def is_port_reachable(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) == 0

if is_port_reachable(host, port):
    try:
        response_root = requests.get(f'https://{host}/', verify=False)
        response_admin = requests.get(f'https://{host}/admin', verify=False)
        
        if response_root.status_code == 200 or response_admin.status_code == 200:
            print("FINAL_STATUS=SUCCESS")
        else:
            print("FINAL_STATUS=FAILURE")
    except requests.exceptions.RequestException:
        print("FINAL_STATUS=FAILURE")
else:
    print("FINAL_STATUS=FAILURE")