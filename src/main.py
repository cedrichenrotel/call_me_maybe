import sys
try:
    from pydantic import ValidationError
    from src.parser import ParseError, Parser
    import argparse
except ImportError:
    sys.exit()


def main():
    try:
        args_parser = argparse.ArgumentParser()

        args_parser.add_argument('--input', default=(
                'data/input/function_calling_tests.json'
                )
        )
        args_parser.add_argument('--output', default=(
            'data/output/function_calls.json'
            )
        )
        args_parser.add_argument('--functions_definition', default=(
            'data/input/functions_definition.json'
            )
        )

        args = args_parser.parse_args()

        try:
            valid_parser = Parser(**vars(args))
        except (ParseError, ValidationError) as e:
            print(f'[ERROR]: {e}')
            sys.exit()

    except KeyboardInterrupt:
        print("[WARNING]: The programme was stopped manually")
        sys.exit()

if __name__ == "__main__":
    main()
