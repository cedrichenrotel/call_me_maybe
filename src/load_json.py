import sys
try:
    from pathlib import Path
    import json
except ImportError:
    sys.exit()


def parse_json(file: Path) -> list[dict]:

    with open(file, 'r') as f:
        data = json.load(f)
    return data


def create_json(file: Path, data: list[dict]) -> None:

    with open(file, 'w') as f:
        data = json.dump(data, f, indent=4)
