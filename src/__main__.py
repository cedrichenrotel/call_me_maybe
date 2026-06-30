import sys
try:
    from src.parser import Parser
    from src.models import FunctionsDefinition, PromptTest, FunctionCall
    from src.load_json import parse_json, create_json
    from src.utils import convert_in_models
    from src.generator_llm import GeneratorLlm
    import argparse
    from pydantic import ValidationError, BaseModel
except ImportError as e:
    print(f'[IMPORT ERROR]: {e}')
    sys.exit()


def main() -> None:

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

        try:
            data_prompt: list[dict] = parse_json(valid_parser.input)
        except Exception as e:
            print(f"[ERROR] input: function_calling_test.json -> {e}")
            sys.exit()

        try:
            data_fonction: list[dict] = parse_json(
                                            valid_parser.functions_definition
                                            )
        except Exception as e:
            print(f"[ERROR] input: functions_definition.json -> {e}")
            sys.exit()

        try:
            model_prompt: list[PromptTest] = convert_in_models(
                                                data_prompt,
                                                PromptTest
                                                )
        except Exception as e:
            print(f'[ERROR] input: function_calling_test."prompt": -> {e}')
            sys.exit()

        try:
            model_function: list[FunctionsDefinition] = convert_in_models(
                                                data_fonction,
                                                FunctionsDefinition
                                                )
        except Exception:
            print("[ERROR] models.py: Failed to convert functions to"
                  "FunctionsDefinition models")
            sys.exit()

        try:
            generator = GeneratorLlm()

            output: list[BaseModel] = []
            for prompt in model_prompt:

                rst: FunctionCall = generator.execute_llm(
                    prompt,
                    model_function
                    )
                output.append(rst.model_dump())

            create_json(valid_parser.output, output)
        except Exception as e:
            print(f"[ERROR] output: main.py Failed to generate or save "
                  f"output -> {e}")
            sys.exit()

    except KeyboardInterrupt:
        print("[WARNING]: The programme was stopped manually")
        sys.exit()


if __name__ == "__main__":
    main()
