import sys
try:
    from pydantic import ValidationError, BaseModel
    from parser import ParseError, Parser
    from models import (
        FunctionsDefinition,
        PromptTest,
    )
    from load_json import parse_json
    from utils import convert_in_models
    from generator_llm import GeneratorLlm
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
        
        for prompt in model_prompt:
            rst = GeneratorLlm.execute_llm(prompt, model_function)

    except KeyboardInterrupt:
        print("[WARNING]: The programme was stopped manually")
        sys.exit()

if __name__ == "__main__":
    main()
