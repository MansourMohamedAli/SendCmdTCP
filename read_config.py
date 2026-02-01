import json
import sys
from pathlib import Path

from logger import logger

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

    required_keys: set = {"hostname", "port", "commands"}
    diabled_payloads_index = []

    for idx, payload in enumerate(data[command_set], start=1):
        missing = required_keys - payload.keys()
        if missing:
            msg = f"Host #{idx!r} is missing keys: {missing!r}"
            raise ValueError(msg)
        if "disabled" in payload:
            diabled_payloads_index.append(idx-1)
            # logger.debug(f"Optional Keys: {optional_keys} for payload #{idx!r}. {payload["hostname"]}:{payload["port"]}")
            # logger.debug(type(data[command_set]))
            # logger.debug(data[command_set])
            # logger.debug(data[command_set].pop(idx-1))
            # diabled_payloads.append(data[command_set].pop(idx-1))
    # logger.debug(f"Disabled: {diabled_payloads}")
    for i in reversed(diabled_payloads_index):
        data[command_set].pop(i)
    # logger.debug(data[command_set])

    return data[command_set]


def serialize_commands(commands: list):
    return json.dumps(commands).encode("utf-8")


def main():
    if len(sys.argv) <= 2:
        logger.info("Usage: python read_hosts.py <config.json>")
        sys.exit(1)

    config_file = sys.argv[1]
    command_set = sys.argv[2]

    try:
        commandsets = read_config(config_file, command_set)
        for i, commandset in enumerate(commandsets):
            logger.info(f"#{i}: {commandset}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
