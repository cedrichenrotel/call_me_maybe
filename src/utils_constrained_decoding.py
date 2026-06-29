def filter_vocab_by_prefix(element: str, vocab: dict[str, int]) -> list[int]:
    """
    Filtre le vocabulaire pour ne garder que les tokens qui peuvent
    continuer ou écrire l'élément attendu, en gérant les espaces des
    tokenizers.
    """
    filter_score: list[int] = []

    for token_str, token_id in vocab.items():

        if len(token_str) > 0 and token_str.strip() == "":
            filter_score.append(token_id)
            continue
        match_token: str = token_str.lstrip()

        if match_token and (element.startswith(match_token) or
                            match_token.startswith(element)):
            filter_score.append(token_id)

    return filter_score


def filter_list_str(prefix: str, elements: list[str]) -> list[str]:
    """Retourne tous les noms (clés ou fonctions) qui commencent par le
    préfixe."""

    return [element for element in elements if element.startswith(prefix)]


def keyword_search(json_str: str, word: str) -> str:
    """Isole la fin de la chaîne après le mot-clé recherché."""
    return json_str.split(word)[-1]


def filter_score(elements: list[str], prefix: str, vocab: dict,
                 scores: list[float]) -> list[float]:
    """Masque les scores pour ne garder que les tokens valides pour
    les éléments fournis."""
    rst: list[int] = []

    for element in elements:
        rst.extend(filter_vocab_by_prefix(element[len(prefix):], vocab))

    if len(rst) == 0:
        return scores

    rst_set: set[int] = set(rst)

    for index, _ in enumerate(scores):
        if index not in rst_set:
            scores[index] = float('-inf')

    return scores


def selection_type(hint: str, vocab: dict, scores: list[float]) -> list[float]:
    """Force le modèle à choisir des tokens correspondants au type attendu."""
    if hint == 'boolean':
        response_list: list[str] = ['false', 'true']
    elif hint == 'number':
        response_list: list[str] = [
            '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
        ]
    elif hint == 'string':
        response_list: list[str] = ['"']
    else:
        raise ValueError('def selection_type: unknown type')

    allowed_token: list[int] = []
    for resp in response_list:
        allowed_token.extend(filter_vocab_by_prefix(resp, vocab))

    mask: list[float] = [float('-inf')] * len(scores)
    for token in allowed_token:
        if token is not None and token < len(mask):
            mask[token] = scores[token]

    return mask


def is_key_complete(key: str, param_prefix: str) -> bool:
    """Vérifie si une clé et sa valeur sont complètement écrites."""

    clean = param_prefix.replace(' ', '')

    if f'{key}":' not in clean:
        return False
    after_key = clean.split(f'{key}":')[1]

    if ',' in after_key or '}' in after_key:
        return True

    if after_key.count('"') >= 2:
        return True
    return False


def check_repetition(json_txt: str, min_len: int = 3) -> bool:

    len_text = len(json_txt)

    for i in range(min_len, len_text // 2 + 1):
        if json_txt[len_text - i:] == json_txt[len_text - (2 * i):
                                               len_text - i]:
            return True
    return False
