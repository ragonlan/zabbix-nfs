#!/usr/bin/env python3

import sys
import subprocess
import re
from typing import List, Tuple
import socket
import logging
import json

# Configurar el logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('nfs_check')

# Configurar un manejador para STDERR
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stderr_handler.setFormatter(formatter)
logger.addHandler(stderr_handler)

def run_command(command: List[str], timeout: int = 10) -> Tuple[int, str, str]:
    try:
        logger.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        logger.debug(f"Command output: {result.stdout}")
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        error_msg = f"Command '{' '.join(command)}' timed out after {timeout} seconds."
        logger.error(error_msg)
        return 124, "", error_msg
    except Exception as e:
        error_msg = f"{str(e)}"
        logger.error(error_msg)
        return 1, "", error_msg

def get_nfs_version(server: str) -> str:
    command = ["rpcinfo", "-t", server, "nfs"]
    exit_code, stdout, stderr = run_command(command)

    if exit_code != 0:
        logger.error(f"Failed to get NFS version for {server}: {stderr}")
        return -1

    versions = []
    for line in stdout.splitlines():
        if "ready and waiting" in line:
            match = re.search(r"version (\d+)", line)
            if match:
                versions.append(int(match.group(1)))

    if versions:
        result = str(max(versions))
        logger.info(f"NFS version for {server}: {result}")
        return result
    else:
        logger.warning(f"No NFS version found for {server}")
        return "0"

def check_nfs_share(server: str, shares: str) -> str:
    command = ["showmount", "-e", server]
    exit_code, stdout, stderr = run_command(command)

    if exit_code != 0:
        logger.error(f"Failed to check NFS shares for {server}: {stderr}")
        return f"Error: {stderr}"

    available_shares = set(line.split()[0] for line in stdout.splitlines()[1:])
    requested_shares = set(shares.split(","))

    not_found = requested_shares - available_shares
    if not_found:
        result = json.dumps(list(not_found))
        logger.warning(f"Shares not found on {server}: {result}")
        return result
    else:
        logger.info(f"All requested shares found on {server}")
        return ""

def main():
    if len(sys.argv) < 3:
        logger.error("Insufficient arguments")
        sys.exit(1)

    action = sys.argv[1]
    server = sys.argv[2]

    # Verificar si el servidor es accesible
    try:
        socket.gethostbyname(server)
        logger.info(f"Successfully resolved hostname {server}")
    except socket.gaierror:
        logger.error(f"Unable to resolve hostname {server}")
        sys.exit(1)

    if action == "version":
        result = get_nfs_version(server)
    elif action == "share":
        if len(sys.argv) < 4:
            logger.error("Shares parameter is required for 'share' action")
            sys.exit(1)
        shares = sys.argv[3]
        result = check_nfs_share(server, shares)
    else:
        logger.error(f"Unknown action '{action}'")
        sys.exit(1)

    print(result)

if __name__ == "__main__":
    main()
