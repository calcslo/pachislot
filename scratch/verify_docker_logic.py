import os
import sqlite3
import logging
import requests
import subprocess
import time
import re

# Import or copy constants
PROXY_SERVER = "http://localhost:8118"
CONTAINER_NAME = "vpngate-proxy"

# Copy functions from the script
def is_proxy_working() -> bool:
    try:
        resp = requests.get(
            "http://httpbin.org/ip",
            proxies={"http": PROXY_SERVER, "https": PROXY_SERVER},
            timeout=5
        )
        if resp.status_code == 200:
            print(f"Proxy check OK: {resp.json().get('origin')}")
            return True
    except Exception as e:
        print(f"Proxy check failed: {e}")
    return False

def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def is_port_owner_docker(port: int) -> bool:
    try:
        res = subprocess.run(
            ["docker", "ps", "--filter", f"publish={port}", "--format", "{{.ID}}"],
            capture_output=True, text=True
        )
        return bool(res.stdout.strip())
    except Exception:
        return False

if __name__ == "__main__":
    print(f"Port 8118 in use: {is_port_in_use(8118)}")
    if is_port_in_use(8118):
        print(f"Port owner is Docker: {is_port_owner_docker(8118)}")
        print(f"Proxy is working: {is_proxy_working()}")
