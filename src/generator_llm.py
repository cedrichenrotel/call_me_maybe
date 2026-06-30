import sys
try:
    from llm_sdk import Small_LLM_Model  # type: ignore
    from src.models import FunctionCall, PromptTest, FunctionsDefinition
    from src.load_json import parse_json
    import src.constrained_decoding
    import src.utils
    import torch
    import json
except ImportError as e:
    print(f'[IMPORT ERROR]: {e}')
    sys.exit()


class GeneratorLlm():

    def __init__(self) -> None:
        self.llm_model: Small_LLM_Model = Small_LLM_Model()

        self.vocab_path: str = self.llm_model.get_path_to_vocab_file()

        self.vocab: dict[str, int] = parse_json(self.vocab_path)

        self.clean_vocab: dict[str, int] = {
            token_str.replace('Ġ', ' '): token_id
            for token_str, token_id in self.vocab.items()
        }

    def execute_llm(self, prompt: PromptTest,
                    lst_function: list[FunctionsDefinition]) -> FunctionCall:

        text: str = "Available functions:\n"
        for function in lst_function:
            text += f"- {function.name}: {function.parameters}\n"
        text += f"request: {prompt.prompt}\n"
        text += 'Respond only in JSON format with name and parameters.'

        lst_token: torch.Tensor = self.llm_model.encode(text)

        try:

            json_tokens: list[int] = []
            max_tokens = 200

            while len(json_tokens) < max_tokens:
                input_ids: list[float] = src.utils.build_input_ids(lst_token,
                                                                   json_tokens)

                scores: list[float] = (self.llm_model.
                                       get_logits_from_input_ids(input_ids))

                json_str: str = self.llm_model.decode(json_tokens).replace(
                    ' ',
                    ''
                    )

                filter_score = src.constrained_decoding.constrained_decoding(
                    scores,
                    json_tokens,
                    self.clean_vocab,
                    lst_function,
                    json_str
                )

                json_tokens = src.utils.select_best_token(json_tokens,
                                                          filter_score)

                if src.utils.bracket_validator(
                        self.llm_model.decode(json_tokens)):
                    break

            else:
                print("[WARNING] Max tokens reached without a valid closing"
                      "bracket.")

            json_str = self.llm_model.decode(json_tokens)

            data = json.loads(json_str)
            data['prompt'] = prompt.prompt

            for f in lst_function:
                if f.name == data.get('name'):

                    for key, val in f.parameters.items():
                        if val['type'] == 'number':
                            data['parameters'][key] = float(
                                data['parameters'][key])

            print(f"{data}")
            return FunctionCall(**data)
        except json.decoder.JSONDecodeError as e:
            print(f"[ERROR] GeneratorLlm.py: {e}")
            sys.exit()
