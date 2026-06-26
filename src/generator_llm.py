import sys
try:
    from llm_sdk import Small_LLM_Model
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

        # retourne en str le chemin du fichier ou est stocker la liste
        # complète des tokens que le modèle (Qwen3-0.6B)
        self.vocab_path: str = self.llm_model.get_path_to_vocab_file()

        # liste de tous les tokens que l intelligeance connais
        self.vocab: dict[str, int] = parse_json(self.vocab_path)
        # Dans generator_llm.py, après avoir chargé le vocab
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

            while True:
                # combine 2 liste de tokens deja existant en une liste
                input_ids: list[float] = src.utils.build_input_ids(lst_token,
                                                                   json_tokens)

                # liste de tous les score des prochains token (1 score par
                # token)
                scores: list[float] = (self.llm_model.
                                       get_logits_from_input_ids(input_ids))

                # convertion de token en str
                json_str: str = self.llm_model.decode(json_tokens)

                # prefiltre les token qui serait plus interessant
                filter_score = src.constrained_decoding.constrained_decoding(
                    scores,
                    json_tokens,
                    self.clean_vocab,
                    lst_function,
                    json_str
                )

                # recupere la plus haute valeur du prochain token
                json_tokens = src.utils.select_best_token(json_tokens,
                                                          filter_score)

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
            print(f"[ERROR] GeneratorLlm.py: {e}")
            sys.exit()
