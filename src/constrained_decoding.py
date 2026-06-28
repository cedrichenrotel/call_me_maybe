import sys
try:
    from src.models import FunctionsDefinition
    import src.utils_constrained_decoding as utils
except ImportError:
    sys.exit()


def constrained_decoding(scores: list[float], json_tokens: list[int],
                         vocab: dict[str, int],
                         list_function: list[FunctionsDefinition],
                         json_str: str) -> list[float]:
    """
    Analyse l'état actuel du JSON généré et applique des contraintes sur les
    scores des prochains tokens pour forcer le respect du schéma de la
    fonction.
    """

    print(f'[DEBUG] -> JSON_STR: {repr(json_str)}')
    json_clean: str = json_str.replace(' ', '')
    if '"name":"' not in json_clean:

        opening_normalized: str = '{"name":"'
        normalized: str = json_str.replace(' ', '')

        next_char: str = opening_normalized[0]  # défaut : '{'
        for i in range(len(opening_normalized), 0, -1):
            if normalized.endswith(opening_normalized[:i]):
                if i < len(opening_normalized):
                    next_char = opening_normalized[i]
                break

        rst: set[int] = set(utils.filter_vocab_by_prefix(next_char, vocab))
        for index, _ in enumerate(scores):
            if index not in rst:
                scores[index] = float('-inf')
        return scores

    # ÉTAPE 2 : le nom de la fonction est en cours d'écriture
    elif '"name":"' in json_clean and '"parameters":{' not in json_clean:

        if '"name": "' in json_str:
            prefix: str = utils.keyword_search(json_str, '"name": "')
        else:
            prefix: str = utils.keyword_search(json_str, '"name":"')

        # nom déjà complet → on attend "parameters"
        if '"' in prefix:
            return scores

        list_name: list[str] = [name.name for name in list_function]
        names_func: list[str] = utils.filter_list_str(prefix, list_name)
        new_scores: list[float] = utils.filter_score(names_func,
                                                     prefix,
                                                     vocab,
                                                     scores
                                                     )

    # ÉTAPE 3 : les paramètres sont en cours d'écriture
    elif '"name":"' in json_clean and '"parameters":{' in json_clean:

        before_params: str = json_str.split('"parameters"')[0]

        if '"name": "' in before_params:
            prefix: str = utils.keyword_search(before_params, '"name": "')
        else:
            prefix: str = utils.keyword_search(before_params, '"name":"')

        find_word: str = prefix.split('"')[0].strip()

        function: FunctionsDefinition = (
            next((f for f in list_function if f.name == find_word), None)
        )
        if not function:
            raise ValueError('connstrained_decoding.py -> Function not found')

        if '"parameters": {' in json_str:
            param_prefix: str = utils.keyword_search(json_str,
                                                     '"parameters": {')
        else:
            param_prefix: str = utils.keyword_search(json_str,
                                                     '"parameters":{')

        # isole le dernier paramètre en cours
        param: str = param_prefix.split(',')[-1]

        list_keys: list[str] = list(function.parameters.keys())

        # liste des clés non encore utilisées (avec guillemet ouvrant)
        list_unused_keys: list[str] = ['"' + key for key in list_keys
                                       if not utils.is_key_complete(
                                           key,
                                           param_prefix
                                           )]
        # enlève les espaces puis UN guillemet ouvrant si présent
        param = param.lstrip(' ')
        if param.startswith('"'):
            param = param[1:]

        # toutes les clés écrites → fermer l'accolade
        if not list_unused_keys:

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
                new_scores: list[float] = utils.filter_score(
                    keys_without_quote,
                    '',
                    vocab, scores
                    )
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
                    after_colon = parts[1]

                    if after_colon.count('"') < 2:
                        # string pas encore fermée → interdire }
                        for token_str, token_id in vocab.items():
                            if '}' in token_str or ',' in token_str:
                                scores[token_id] = float('-inf')
                        return scores
                    else:
                        # string fermée → s'il n'y a plus de clés, interdire ,
                        if len(list_unused_keys) == 1:
                            comma_token = vocab.get(',')
                            if comma_token is not None:
                                scores[comma_token] = float('-inf')
                        return scores

                elif not parts[1].strip():
                    new_scores: list[float] = utils.selection_type(
                        param_type,
                        vocab,
                        scores
                        )
                    return new_scores

            return scores

        # LLM en train d'écrire le nom de la clé
        keys_list: list[str] = utils.filter_list_str(param, list_unused_keys)
        new_scores: list[float] = utils.filter_score(keys_list, param, vocab,
                                                     scores)

    else:
        return scores
    return new_scores
