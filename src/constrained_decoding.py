import sys
try:
    from src.models import FunctionsDefinition
except ImportError:
    sys.exit()


# retourne liste de token qui correspond au nom de fonction
def filter_vocab_by_prefix(element: str, vocab: dict) -> list[int]:

    filter_score: list[int] = []

    for token_str, token_id in vocab.items():
        # On nettoie les caractères d'espacement bizarres propres aux
        # tokenizers (ex: Ġ ou █)
        clean_token = token_str.replace('Ġ', ' ').replace(' ', ' ')

        # Est-ce que le token commence ce qu'il nous reste à écrire ?
        if element.startswith(clean_token) and clean_token != "":
            filter_score.append(token_id)

    return filter_score


# retourne tous les nom de fonction qui commence comme le prefixe
def filter_list_str(prefix: str, elements: list[str]) -> list[str]:

    return [element for element in elements if element.startswith(prefix)]


# reourne un mot cles
def keyword_search(json_str: str, word: str) -> str:

    prefix: list[str] = json_str.split(word)

    return prefix[-1]


# selection tous les plus forte valeur des prochain tokens
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


# typage de ma valeur  de la cles(type)
def selection_type(hint: str, vocab: dict, scores: list[float]) -> list[float]:

    if hint == 'boolean':

        response_list: list[str] = ['false', 'true']
        score: list[float] = filter_score(response_list, "", vocab, scores)

    elif hint == 'number':

        response_list: list[str] = [
            '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
            ]
        score = filter_score(response_list, "", vocab, scores)

    elif hint == 'string':

        response_list: list[str] = ['"']
        score = filter_score(response_list, "", vocab, scores)

    else:
        raise ValueError('def selection_type: unknown type')

    return score


def constrained_decoding(scores: list[float], json_tokens: list[int],
                         vocab: dict, list_function: list[FunctionsDefinition],
                         json_str: str) -> list[float]:

    if ('"name": "' in json_str and
        '"' not in keyword_search(json_str, '"name": "') and
       '"parameters": {' not in json_str):

        list_name = [name.name for name in list_function]
        prefix: str = keyword_search(json_str, '"name": "')
        names_func: list[str] = filter_list_str(prefix, list_name)
        new_scores: list[float] = filter_score(names_func, prefix, vocab,
                                               scores)

    elif '"name": "' in json_str and '"parameters": {' in json_str:

        before_params = json_str.split('"parameters"')[0]
        prefix: str = keyword_search(before_params, '"name": "')
        find_word: str = prefix.split('"')[0]

        function: FunctionsDefinition = (
            next((element for element in list_function
                  if element.name == find_word), None)
                  )

        if not function:
            raise ValueError('Function not found')

        param_prefix: str = keyword_search(json_str, '"parameters": {')
        param = param_prefix.split(',')[-1]

        # lister les dict de parameters
        list_keys: list[str] = [k for k in function.parameters.keys()]

        # gere le cas si '"' ouvrant de la clés est deja present
        if param.startswith(' "'):

            param = param[2:]

        # liste des cles de parameters non utiliser
        list_unused_keys: list[str] = ['"' + key for key in list_keys
                                       if not f'{key}":' in
                                       param_prefix.replace(' ', '')]

        # si la liste des list_unused est vide ferme l'acolade
        if not list_unused_keys:
            if param.split(':')[1].strip():
                rst = [vocab.get('}')]
                for index, _ in enumerate(scores):

                    if index not in rst:
                        scores[index] = float('-inf')
                print(f'index: {index}')

            return scores

        # liste de cles non utliser mais filtrer avec prefix
        keys_list: list[str] = filter_list_str(param, list_unused_keys)

        # recuperer la valeur dans la cles(type)
        if (param.strip(' "') != "" and param.count('"') % 2 == 0 and
           ':' not in param):
            return scores

        elif ':' in param and '"' in param:
            key_name: str = param.split(':')[0].strip(' "')
            # print(f'key_name: {repr(key_name)}')

            if key_name in function.parameters:
                param_type: str = function.parameters[key_name]["type"]

                if param_type == "string" and '"' in param:
                    return scores

                elif not param.split(':')[1].strip():
                    new_scores: list[float] = selection_type(param_type,
                                                             vocab,
                                                             scores)
                    return new_scores

            return scores

        new_scores: list[float] = filter_score(keys_list, param, vocab,
                                               scores)
    else:

        return scores
    # print(json_str)
    return new_scores
