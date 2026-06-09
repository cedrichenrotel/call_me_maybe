import os
import sys

try:
    import argparse
    import json

except ImportError:
    sys.exit()


def main() -> None:
    try:
        file = 'functions_definition.json'
        with open(file, 'r') as f:
            data = json.load(f)

    except KeyboardInterrupt:
        print("[WARNING]: The programme was stopped manually")
        sys.exit()


if __name__ == '__main__':
    main()