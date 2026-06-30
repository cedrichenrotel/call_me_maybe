def filter_vocab_by_prefix(element: str, vocab: dict[str, int]) -> list[int]:
    """
    Filters the vocabulary to retain only those tokens that can
    continue or complete the expected element, whilst handling the spaces from
    the tokenisers.
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
    """Returns all names (keys or functions) that begin with the
    préfix."""

    return [element for element in elements if element.startswith(prefix)]


def keyword_search(json_str: str, word: str) -> str:
    """Isolates the end of the string after the search term."""

    return json_str.split(word)[-1]


def filter_score(elements: list[str], prefix: str, vocab: dict,
                 scores: list[float]) -> list[float]:
    """Hides the scores to retain only the valid tokens for
     the elements provided."""

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
    """Forces the model to select tokens that match the expected type."""

    if hint == 'boolean':
        response_list: list[str] = ['false', 'true']

    elif hint == 'number' or hint == 'integer':
        response_list = [
            '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
        ]

    elif hint == 'string':
        response_list = ['"']

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
    """Checks whether a key and its value have been written in full."""

    clean: str = param_prefix.replace(' ', '')

    if f'{key}":' not in clean:
        return False
    after_key: str = clean.split(f'{key}":')[1]

    if ',' in after_key or '}' in after_key:
        return True

    if after_key.count('"') >= 2:
        return True

    return False


def count_unescaped_quotes(s: str) -> int:
    """Counts the unescaped quotation marks in s."""

    count: int = 0
    i: int = 0

    while i < len(s):

        if s[i] == '\\':
            i += 2

        else:
            if s[i] == '"':
                count += 1
            i += 1

    return count


def check_repetition(json_txt: str, min_len: int = 3) -> bool:
    """check the infinity ball"""

    len_text: int = len(json_txt)

    for i in range(min_len, len_text // 2 + 1):

        if json_txt[len_text - i:] == json_txt[len_text - (2 * i):
                                               len_text - i]:
            return True

    return False
