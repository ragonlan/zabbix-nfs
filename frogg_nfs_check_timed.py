#!/usr/bin/env python3

import sys
import subprocess
import re
from typing import List, Tuple
import socket

def run_command(command: List[str], timeout: int = 10) -> Tuple[int, str, str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"Error: Command '{' '.join(command)}' timed out after {timeout} seconds."
    except Exception as e:
        return 1, "", f"Error: {str(e)}"

def get_nfs_version(server: str) -> str:
    command = ["rpcinfo", "-t", server, "nfs"]
    exit_code, stdout, stderr = run_command(command)

    if exit_code != 0:
        return f"Error: {stderr}"

    versions = []
    for line in stdout.splitlines():
        if "ready and waiting" in line:
            match = re.search(r"version (\d+)", line)
            if match:
                versions.append(int(match.group(1)))

    if versions:
        return str(max(versions))
    else:
        return "0"

def check_nfs_share(server: str, shares: str) -> str:
    command = ["showmount", "-e", server]
    exit_code, stdout, stderr = run_command(command)

    if exit_code != 0:
        return f"Error: {stderr}"

    available_shares = set(line.split()[0] for line in stdout.splitlines()[1:])
    requested_shares = set(shares.split(","))

    not_found = requested_shares - available_shares
    return ",".join(f"[{share}]" for share in not_found) if not_found else ""
  def main():
    if len(sys.argv) < 3:
        print("Usage: python3 script.py <action> <server> [shares]")
        sys.exit(1)

    action = sys.argv[1]
    server = sys.argv[2]

    # Verificar si el servidor es accesible
    try:
        socket.gethostbyname(server)
    except socket.gaierror:
        print(f"Error: Unable to resolve hostname {server}")
        sys.exit(1)

    if action == "version":
        result = get_nfs_version(server)
    elif action == "share":
        if len(sys.argv) < 4:
            print("Error: Shares parameter is required for 'share' action")
            sys.exit(1)
        shares = sys.argv[3]
        result = check_nfs_share(server, shares)
    else:
        print(f"Error: Unknown action '{action}'")
        sys.exit(1)

    print(result)

if __name__ == "__main__":
    main()
