import sys
try:
    from llm_sdk import Small_LLM_Model
    from src.models import FunctionCall, PromptTest, FunctionsDefinition
    from src.constrained_decoding 
    import src.utils
    import torch
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

        try:
            json_tokens: list[int] = [90]

            while True:
                # combine 2 liste de tokens deja existant en une liste
                input_ids: list[float] = src.utils.build_input_ids(lst_token,
                                                                   json_tokens)

                # liste de tous les score des prochains token (1 score par token)
                scores: list[float] = (self.llm_model.
                                       get_logits_from_input_ids(input_ids))
                
                # application des constrained coding
                constrained = 

                # recupere la plus haute valeur du prochain token
                json_tokens = src.utils.select_best_token(json_tokens, scores)

                # condition d arret pour la boucle 
                if src.utils.bracket_validator(
                        self.llm_model.decode(json_tokens)):
                    break

            json_str = self.llm_model.decode(json_tokens)
            print(f"{json_str}")
            data = json.loads(json_str)
            data['prompt'] = prompt.prompt
            return FunctionCall(**data)
        except ValueError as e:
            print(f"[ERROR] GeneratorLlm(): {e}")
