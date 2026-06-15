import sys
from src.parser import Parser
from src.models import FunctionsDefinition, PromptTest
from src.load_json import parse_json
from src.utils import convert_in_models
from src.generator_llm import GeneratorLlm
import argparse
try:
    from pydantic import ValidationError, BaseModel
except ImportError as e:
    print(f'[IMPORT ERROR]: {e}')
    sys.exit()


def main():
    print('trololo')
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

        except ValidationError as e:
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

        generator = GeneratorLlm()
        for prompt in model_prompt:
            rst = generator.execute_llm(prompt, model_function)

    except KeyboardInterrupt:
        print("[WARNING]: The programme was stopped manually")
        sys.exit()


if __name__ == "__main__":
    main()
