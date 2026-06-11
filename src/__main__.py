import sys
try:
    from pydantic import ValidationError, BaseModel
    from src.parser import ParseError, Parser
    from src.models import (
        FunctionsDefinition,
        PromptTest,
    )
    from src.load_json import parse_json
    from src.utils import convert_in_models
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
            print(f'[ERROR] Parser: {e}')
            sys.exit()

        data_prompt: list[dict] = parse_json(valid_parser.input)
        data_fonction: list[dict] = parse_json(
                                        valid_parser.functions_definition
                                        )

        model_prompt: list[BaseModel] = convert_in_models(
                                            data_prompt,
                                            PromptTest
                                        )
        model_function: list[BaseModel] = convert_in_models(
                                            data_fonction,
                                            FunctionsDefinition
                                        )

    except KeyboardInterrupt:
        print("[WARNING]: The programme was stopped manually")
        sys.exit()

if __name__ == "__main__":
    main()
