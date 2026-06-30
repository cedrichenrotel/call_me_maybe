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
    Analyses the current state of the generated JSON and applies constraints
    to the scores of subsequent tokens to ensure compliance with the function’s
    schema.
    """

    json_clean: str = json_str.replace(' ', '')

    if '"name":"' not in json_clean:

        opening_normalized: str = '{"name":"'
        normalized: str = json_str.replace(' ', '')
        next_char: str = opening_normalized[0]

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

    elif '"name":"' in json_clean and '"parameters":{' not in json_clean:

        if '"name": "' in json_str:
            prefix: str = utils.keyword_search(json_str, '"name": "')

        else:
            prefix = utils.keyword_search(json_str, '"name":"')

        if '"' in prefix:
            return scores

        list_name: list[str] = [name.name for name in list_function]
        names_func: list[str] = utils.filter_list_str(prefix, list_name)
        new_scores: list[float] = utils.filter_score(names_func,
                                                     prefix,
                                                     vocab,
                                                     scores
                                                     )

    elif '"name":"' in json_clean and '"parameters":{' in json_clean:

        before_params: str = json_str.split('"parameters"')[0]

        if '"name": "' in before_params:
            prefix = utils.keyword_search(before_params, '"name": "')

        else:
            prefix = utils.keyword_search(before_params, '"name":"')

        find_word: str = prefix.split('"')[0].strip()

        function: FunctionsDefinition | None = (
            next((f for f in list_function if f.name == find_word), None)
        )

        if not function:
            raise ValueError('connstrained_decoding.py -> Function not found')

        if '"parameters": {' in json_str:
            param_prefix: str = utils.keyword_search(
                json_str,
                '"parameters": {'
                )

        else:
            param_prefix = utils.keyword_search(
                json_str,
                '"parameters":{'
                )

        param: str = param_prefix.split(',')[-1]

        list_keys: list[str] = list(function.parameters.keys())

        list_unused_keys: list[str] = ['"' + key for key in list_keys
                                       if not utils.is_key_complete(
                                           key,
                                           param_prefix
                                           )]

        param = param.lstrip(' ')

        if param.startswith('"'):
            param = param[1:]

        if not list_unused_keys:
            close_bracket: int | None = vocab.get('}')

            if close_bracket is not None:
                mask: list[float] = [float('-inf')] * len(scores)
                mask[close_bracket] = scores[close_bracket]
                return mask

            return scores

        if not param:
            raw_param: str = param_prefix.split(',')[-1].lstrip(' ')

            if not raw_param.startswith('"'):
                quote_token: int | None = vocab.get('"')

                if quote_token is not None:
                    mask = [float('-inf')] * len(scores)
                    mask[quote_token] = scores[quote_token]
                    return mask

            else:
                keys_without_quote: list[str] = [k[1:] for k in
                                                 list_unused_keys]
                new_scores = utils.filter_score(
                    keys_without_quote,
                    '',
                    vocab, scores
                    )
            return new_scores

        param_stripped: str = param.strip()

        if param_stripped.endswith('"') and ':' not in param_stripped:
            colon_token = vocab.get(':')

            if colon_token is not None:
                mask = [float('-inf')] * len(scores)
                mask[colon_token] = scores[colon_token]
                return mask

        if ':' in param:
            parts: list[str] = param.split(':', 1)
            key_name: str = parts[0].strip(' "')

            if key_name in function.parameters:
                param_type: str = function.parameters[key_name]["type"]

                if param_type == "string":
                    after_colon = parts[1]

                    if after_colon.replace('\\"', '').count('"') < 2:
                        string_content: str = after_colon.lstrip('"')

                        if (string_content and
                           utils.check_repetition(string_content, 3)):
                            quote_token = vocab.get('"')

                            if quote_token is not None:
                                mask = ([float('-inf')] * len(scores))
                                mask[quote_token] = scores[quote_token]
                                return mask

                        for token_str, token_id in vocab.items():
                            if '}' in token_str or ',' in token_str:
                                scores[token_id] = float('-inf')

                            elif ('"' in token_str and
                                  not token_str.endswith('"')):
                                scores[token_id] = float('-inf')

                            elif '\\n' in token_str or '\\r' in token_str:
                                scores[token_id] = float('-inf')

                        return scores

                    else:
                        mask = [float('-inf')] * len(scores)
                        comma_token = vocab.get(',')
                        if comma_token is not None:
                            mask[comma_token] = scores[comma_token]
                        return mask

                elif not parts[1].strip():
                    new_scores = utils.selection_type(
                        param_type,
                        vocab,
                        scores
                        )
                    return new_scores

            return scores

        keys_list: list[str] = utils.filter_list_str(param, list_unused_keys)
        new_scores = utils.filter_score(keys_list, param, vocab, scores)

    else:
        return scores
    return new_scores
