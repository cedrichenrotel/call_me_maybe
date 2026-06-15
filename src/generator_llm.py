import sys
try:
    from llm_sdk import Small_LLM_Model
    from src.models import FunctionCall, PromptTest, FunctionsDefinition
    import src.utils
    import torch
    import numpy
    import json
except ImportError as e:
    print(f'[IMPORT ERROR]: {e}')
    sys.exit()


class GeneratorLlm():

    def __init__(self) -> None:
        self.llm_model: Small_LLM_Model = Small_LLM_Model()

    def execute_llm(self, prompt: PromptTest,
                    lst_function: list[FunctionsDefinition]) -> FunctionCall:

        text: str = "Available functions:\n"
        for function in lst_function:
            text += f"- {function.name}\n"
        text += f"request: {prompt.prompt}\n"
        text += 'Respond only in JSON: {"name": "...", "parameters": {...}}'

        lst_token: torch.Tensor = self.llm_model.encode(text)
        #self.llm_model.get_path_to_vocab_file()
        try:
            json_tokens: list[str] = []

            while not src.utils.bracket_validator(
                self.llm_model.decode(json_tokens)
                 ):
                input_ids: list[float] = lst_token[0].tolist() + json_tokens
                score: list[float] = self.llm_model.get_logits_from_input_ids(input_ids)
                best_token: int = int(numpy.argmax(score))
                json_tokens.append(best_token)
                print(f"Generated: {json_tokens}")

            json_str = self.llm_model.decode(json_tokens)
            
            data = json.loads(json_str)
            return FunctionCall(**data)
        except ValueError as e:
            print(f"[ERROR] GeneratorLlm(): {e}")
