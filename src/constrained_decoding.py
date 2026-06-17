import sys
try:
    from src.load_json import parse_json
    from src.models import FunctionsDefinition
except ImportError:
    sys.exit()

# retourne liste de token qui correspond au nomde fonction  
def filter_vocab_by_prefix(element: str, vocab: dict) -> list[int]:

    filter_score: list[int] = []

    for key, value in vocab.items():

        if element.startswith(key):
            filter_score.append(value)

    return filter_score

# retourne tous les nom de fonction qui commence comme le preficxe
def valid_fonction_name(prefix: str, function_name: list[str]) -> list[str]:

    return [element for element in function_name if element.startswith(prefix)]


def constrained_decoding(scores: list[float], json_tokens: list[int],
                         vocab: dict, list_function: list[FunctionsDefinition],
                         json_str: str) -> list[float]:

    rst: list[int] = []

    if 'name' in json_str and 'parameters' not in json_str:

        list_name = [name.name for name in list_function]
        prefix: list[str] = json_str.split('"name": "')
        names: list[str] = valid_fonction_name(prefix[1], list_name)

        for name in names:
            rst.extend(filter_vocab_by_prefix(name[len(prefix[1]):], vocab))

        for i in enumerate(scores):
            if not scores[i] in rst:
                scores[i] = float('-inf')

