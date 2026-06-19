import sys
try:
    from src.load_json import parse_json
    from src.models import FunctionsDefinition
except ImportError:
    sys.exit()

# retourne liste de token qui correspond au nom de fonction  
def filter_vocab_by_prefix(element: str, vocab: dict) -> list[int]:

    filter_score: list[int] = []

    for token_str, token_id in vocab.items():
        # On nettoie les caractères d'espacement bizarres propres aux tokenizers (ex: Ġ ou █)
        clean_token = token_str.replace('Ġ', ' ').replace(' ', ' ')

        # Est-ce que le token commence ce qu'il nous reste à écrire ?
        if element.startswith(clean_token) and clean_token != "":
            filter_score.append(token_id)

    return filter_score

# retourne tous les nom de fonction qui commence comme le preficxe
def filter_list_str(prefix: str, elements: list[str]) -> list[str]:

    return [element for element in elements if element.startswith(prefix)]


def keyword_search(json_str: str, word: str) -> str:

    prefix: list[str] = json_str.split(word)
    return prefix[-1]


def filter_score(elements: list[str], prefix: str, vocab: dict,
                 scores: list[float]) -> list[float]:

    rst: list[int] = []

    for element in elements:
        rst.extend(filter_vocab_by_prefix(element[len(prefix):], vocab))

    if len(rst) == 0:
        rst.append(vocab.get('"'))

    for index, _ in enumerate(scores):
        if index not in rst:
            scores[index] = float('-inf')
    return scores


def constrained_decoding(scores: list[float], json_tokens: list[int],
                         vocab: dict, list_function: list[FunctionsDefinition],
                         json_str: str) -> list[float]:
    
    # Nettoyage de base pour éviter les espaces blancs qui faussent la détection
    json_str_clean = json_str.strip()

    # ÉTAPE 1 : Forcer le début du JSON s'il est vide ou juste "{"
    if json_str_clean == "" or json_str_clean == "{":
        # On ne veut autoriser QUE les tokens qui commencent par '"name": "'
        return filter_score(['"name": "'], "", vocab, scores)

    if '"name": "' in json_str and '"' not in keyword_search(json_str,
                                                             '"name": "'):

        list_name = [name.name for name in list_function]
        prefix: str = keyword_search(json_str, '"name": "')
        names_func: list[str] = filter_list_str(prefix, list_name)
        new_scores: list[float] = filter_score(names_func, prefix, vocab,
                                               scores)

    elif '"name": "' in json_str and '"parameters": { ' in json_str:

        # recupere le bon nom de fonction
        prefix: str = keyword_search(json_str, '"name": "')
        find_word: str = prefix.split('"')[0]

        function: FunctionsDefinition = (
            next((element for element in list_function
                  if element.name == find_word), None)
                  )

        if not function:
            raise ValueError('Function not found')

        # lister les dict de parameters
        list_keys: list[str] = list(function.parameters.keys())

        param_prefix: str = keyword_search(json_str, '"parameters": {')

        param = param_prefix.split(',')[-1]
        # gere le cas si '"' ouvrant de la clés est deja present
        if param.startswith(' "'):
            param = param[2:]

        # liste des cles de parameters non utiliser
        list_unused_keys: list[str] = [key for key in list_keys
                                       if not f'"{key}":' in json_str]

        # liste de cles non utliser mais filtrer avec prefix
        keys_list: list[str] = filter_list_str(param, list_unused_keys)

        new_scores: list[float] = filter_score(keys_list, param, vocab,
                                               scores)
    else:
        return scores
    return new_scores
