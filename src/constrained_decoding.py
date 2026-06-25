import sys
try:
    from src.models import FunctionsDefinition
except ImportError:
    sys.exit()


def filter_vocab_by_prefix(element: str, vocab: dict) -> list[int]:
    """
    Filtre le vocabulaire pour ne garder que les tokens qui peuvent
    continuer ou écrire l'élément attendu, en gérant les espaces des
    tokenizers.
    """
    filter_score: list[int] = []

    for token_str, token_id in vocab.items():
        # emplace les caractères spéciaux du tokenizer (Ġ qui représente
        # un espace)
        clean_token: str = token_str.replace('Ġ', ' ')

        # autorise a la LLM de creer des espaces
        if len(clean_token) > 0 and clean_token.strip() == "":
            filter_score.append(token_id)
            continue

        # Permet d enlever les espaces a gauche pour comparer correctement les
        # mots
        match_token: str = clean_token.lstrip()

        # si le token ou le debut de la string sont identique ajoute
        # dans filter_tocken
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
    return False


def constrained_decoding(scores: list[float], json_tokens: list[int],
                         vocab: dict, list_function: list[FunctionsDefinition],
                         json_str: str) -> list[float]:
    """
    Analyse l'état actuel du JSON généré et applique des contraintes sur les
    scores des prochains tokens pour forcer le respect du schéma de la
    fonction.
    """

    # ÉTAPE 1 : forcer l'écriture de '{"name":"' au début
    if '"name": "' not in json_str and '"name":"' not in json_str:

        opening_normalized: str = '{"name":"'
        normalized: str = json_str.replace(' ', '')

        next_char: str = opening_normalized[0]  # défaut : '{'
        for i in range(len(opening_normalized), 0, -1):
            if normalized.endswith(opening_normalized[:i]):
                if i < len(opening_normalized):
                    next_char = opening_normalized[i]
                break

        rst: set[int] = set(filter_vocab_by_prefix(next_char, vocab))
        for index, _ in enumerate(scores):
            if index not in rst:
                scores[index] = float('-inf')
        return scores

    # ÉTAPE 2 : le nom de la fonction est en cours d'écriture
    elif (('"name": "' in json_str or '"name":"' in json_str) and
          '"parameters": {' not in json_str and
          '"parameters":{' not in json_str):

        if '"name": "' in json_str:
            prefix: str = keyword_search(json_str, '"name": "')
        else:
            prefix: str = keyword_search(json_str, '"name":"')

        # nom déjà complet → on attend "parameters"
        if '"' in prefix:
            return scores

        list_name: list[str] = [name.name for name in list_function]
        names_func: list[str] = filter_list_str(prefix, list_name)
        new_scores: list[float] = filter_score(names_func, prefix, vocab,
                                               scores)

    # ÉTAPE 3 : les paramètres sont en cours d'écriture
    elif (('"name": "' in json_str or '"name":"' in json_str) and
          ('"parameters": {' in json_str or '"parameters":{' in json_str)):

        before_params: str = json_str.split('"parameters"')[0]

        if '"name": "' in before_params:
            prefix: str = keyword_search(before_params, '"name": "')
        else:
            prefix: str = keyword_search(before_params, '"name":"')

        find_word: str = prefix.split('"')[0].strip()

        function: FunctionsDefinition = (
            next((f for f in list_function if f.name == find_word), None)
        )
        if not function:
            raise ValueError('Function not found')

        if '"parameters": {' in json_str:
            param_prefix: str = keyword_search(json_str, '"parameters": {')
        else:
            param_prefix: str = keyword_search(json_str, '"parameters":{')

        # isole le dernier paramètre en cours
        param: str = param_prefix.split(',')[-1]

        list_keys: list[str] = list(function.parameters.keys())

        # liste des clés non encore utilisées (avec guillemet ouvrant)
        list_unused_keys: list[str] = ['"' + key for key in list_keys
                                       if not is_key_complete(key,
                                                              param_prefix)]
        # enlève les espaces puis UN guillemet ouvrant si présent
        param = param.lstrip(' ')
        if param.startswith('"'):
            param = param[1:]

        # toutes les clés écrites → fermer l'accolade
        if not list_unused_keys:
            if ':' in param and param.split(':', 1)[1].strip():
                close_bracket = vocab.get('}')
                if close_bracket is not None:
                    mask: list[float] = [float('-inf')] * len(scores)
                    mask[close_bracket] = scores[close_bracket]
                    return mask
            return scores

        # rien écrit encore → forcer les clés valides avec guillemet ouvrant
        if not param:
            # vérifier si le guillemet ouvrant est déjà écrit dans param_prefix
            raw_param = param_prefix.split(',')[-1].lstrip(' ')
            print(f"[DEBUG raw param]: {repr(param)}")

            if not raw_param.startswith('"'):

                # guillemet pas encore écrit → forcer "
                quote_token = vocab.get('"')
                if quote_token is not None:
                    mask: list[float] = [float('-inf')] * len(scores)
                    mask[quote_token] = scores[quote_token]
                    return mask
            else:
                # guillemet déjà écrit → forcer le nom de la clé
                keys_without_quote: list[str] = [k[1:] for k in
                                                 list_unused_keys]
                new_scores: list[float] = filter_score(keys_without_quote, '',
                                                       vocab, scores)
            return new_scores
        # clé fermée par " mais pas encore de ':' → forcer ':'
        param_stripped: str = param.strip()
        if param_stripped.endswith('"') and ':' not in param_stripped:
            colon_token = vocab.get(':')
            if colon_token is not None:
                mask: list[float] = [float('-inf')] * len(scores)
                mask[colon_token] = scores[colon_token]
                return mask

        # ':' présent → fournir la valeur
        if ':' in param:
            parts: list[str] = param.split(':', 1)
            key_name: str = parts[0].strip(' "')

            if key_name in function.parameters:
                param_type: str = function.parameters[key_name]["type"]

                if param_type == "string":
                    if parts[1].count('"') < 2:

                        for token_str, token_id in vocab.items():
                            if '}' in token_str:
                                scores[token_id] = float('-inf')

                        return scores

                elif not parts[1].strip():
                    new_scores: list[float] = selection_type(param_type,
                                                             vocab,
                                                             scores)
                    return new_scores

            return scores

        # LLM en train d'écrire le nom de la clé
        keys_list: list[str] = filter_list_str(param, list_unused_keys)
        new_scores: list[float] = filter_score(keys_list, param, vocab, scores)

    else:
        return scores

    return new_scores
