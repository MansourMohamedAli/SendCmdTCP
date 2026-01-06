import json
import sys
from pathlib import Path


def read_config(json_path: str, command_set: str) -> list:
    """Read and validate hosts from a JSON file."""
    path = Path(json_path)

    if not path.is_file():
        msg = f"JSON file not found: {json_path!r}"
        raise FileNotFoundError(msg)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if command_set not in data or not isinstance(data[command_set], list):
        raise ValueError(f"{command_set} not found in {json_path}")

    required_keys = {"hostname", "port", "commands"}

    for idx, host in enumerate(data[command_set], start=1):
        missing = required_keys - host.keys()
        if missing:
            msg = f"Host #{idx!r} is missing keys: {missing!r}"
            raise ValueError(msg)

    return data[command_set]


def serialize_commands(commands: list):
    return json.dumps(commands).encode("utf-8")


def main():
    if len(sys.argv) <= 2:
        print("Usage: python read_hosts.py <config.json>")
        sys.exit(1)

    config_file = sys.argv[1]
    command_set = sys.argv[2]

    try:
        commandsets = read_config(config_file, command_set)
        for commandset in enumerate(commandsets):
            print(commandset)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
