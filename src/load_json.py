import sys
try:
    from pathlib import Path
    from typing import Any
    import json
except ImportError:
    sys.exit()


def parse_json(file: Path | str) -> Any:

    with open(file, 'r') as f:
        data = json.load(f)

    return data


def create_json(file: Path, data: list[dict[str, Any]]) -> None:

    with open(file, 'w') as f:
        json.dump(data, f, indent=4)
