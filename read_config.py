import json
import sys
from pathlib import Path


def read_config(json_path: str) -> list:
    """Read and validate hosts from a JSON file."""
    path = Path(json_path)

    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "hosts" not in data or not isinstance(data["hosts"], list):
        raise ValueError("JSON must contain a 'hosts' list")

    required_keys = {"hostname", "port", "command"}

    for idx, host in enumerate(data["hosts"], start=1):
        missing = required_keys - host.keys()
        if missing:
            raise ValueError(f"Host #{idx} is missing keys: {missing}")

    return data["hosts"]


def main():
    if len(sys.argv) != 2:
        print("Usage: python read_hosts.py <config.json>")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        hosts = read_config(config_file)

        for i, host in enumerate(hosts, start=1):
            hostname = host["hostname"]
            port = host["port"]
            command = host["command"]

            print(f"Host #{i}")
            print(f"  Hostname: {hostname}")
            print(f"  Port: {port}")
            print(f"  Command: {command}")
            print("-" * 30)

            # Here you could:
            # - execute locally
            # - execute via SSH
            # - send to an API
            # etc.

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
