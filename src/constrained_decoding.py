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
        # On nettoie les caractères d'espacement bizarres propres aux
        # tokenizers (ex: Ġ ou █)
        clean_token: str = token_str.replace('Ġ', ' ').replace(' ', ' ')

# Si le token est juste un espace et qu'on attend du texte, on l'autorise
        if len(clean_token) > 0 and clean_token.strip() == "":
            filter_score.append(token_id)
            continue

# Enleve les whitespace  a gauche des de clean
        match_token: str = clean_token.lstrip()

# si match_token n est pas vide et qu il commence comme le debut de
# l element alors ajoute le dans la liste des bon token
        if match_token and element.startswith(match_token):
            filter_score.append(token_id)

    return filter_score


def filter_list_str(prefix: str, elements: list[str]) -> list[str]:
    """Retourne tous les noms (clés ou fonctions) qui commencent par le
    préfixe."""
    return [element for element in elements if element.startswith(prefix)]


def keyword_search(json_str: str, word: str) -> str:
    """Isole la fin de la chaîne après le mot-clé recherché."""
    prefix: list[str] = json_str.split(word)

    return prefix[-1]


def filter_score(elements: list[str], prefix: str, vocab: dict,
                 scores: list[float]) -> list[float]:
    """Masque les scores pour ne garder que les tokens valides pour
    les éléments fournis."""

    rst: list[int] = []

    for element in elements:
        rst.extend(filter_vocab_by_prefix(element[len(prefix):], vocab))

    if len(rst) == 0:
        rst.append(vocab.get('"'))

    for index, _ in enumerate(scores):

        if index not in rst:
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

    # mask est une liste de float qui fait la longueur de vocab
    mask: list[float] = [float('inf')] * len(vocab)

    for token in allowed_token:

        if token is not None and token < len(mask):
            mask[token] = scores[token]

    return mask


def constrained_decoding(scores: list[float], json_tokens: list[int],
                         vocab: dict, list_function: list[FunctionsDefinition],
                         json_str: str) -> list[float]:
    """
    Analyse l'état actuel du JSON généré et applique des contraintes sur les
    scores des prochains tokens pour forcer le respect du schéma de la
    fonction.
    """

    # condition pour trouver le nom de la fonction
    if ('"name": "' in json_str and
        '"' not in keyword_search(json_str, '"name": "') and
       '"parameters": {' not in json_str):

        # liste de tous les nom de function dans le fichier function_definition
        list_name = [name.name for name in list_function]

        # recupere la string aui est apres '"name": "'
        prefix: str = keyword_search(json_str, '"name": "')

        # liste les potententielle bon nom de fonction via prefix
        names_func: list[str] = filter_list_str(prefix, list_name)

        # retourne les ptentiel prochain token valide
        new_scores: list[float] = filter_score(names_func, prefix, vocab,
                                               scores)

    # condition pour trouver les parameters
    elif '"name": "' in json_str and '"parameters": {' in json_str:

        before_params = json_str.split('"parameters"')[0]

        # recupere la string qui est apres '"name": "'
        prefix: str = keyword_search(before_params, '"name": "')

        # recupere mot entre les '"'
        find_word: str = prefix.split('"')[0]

        # stock la bonne fonction en cours
        function: FunctionsDefinition = (
            next((element for element in list_function
                  if element.name == find_word), None)
                  )

        if not function:
            raise ValueError('Function not found')

        # stock tring apres ' "parameters": {'
        param_prefix: str = keyword_search(json_str, '"parameters": {')

        # stock les argument si il en a plusieurs
        param = param_prefix.split(',')[-1]

        # lister les de parameters dans la fonction(nom des variables)
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

            # Si le dernier paramètre a reçu sa valeur (du contenu existe
            # après les derniers deux-points)
            if param.split(':', 1)[1].strip():

                close_bracket = [vocab.get('}')]

                if close_bracket is not None:
                    # mask est une liste de float qui fait la longueur de vocab
                    mask: list[float] = [float('inf')] * len(vocab)

                    mask[close_bracket] = scores[close_bracket]

                    return mask
            return scores

        # si l'ia a ecrit ':', elle doit fournir la valeur
        if ':' in param:
            parts: str = param.split(':', 1)
            key_name: str = parts[0].strip(' "')
            # print(f'key_name: {repr(key_name)}')

            if key_name in function.parameters:
                param_type: str = function.parameters[key_name]["type"]

                # S'il s'agit d'une chaîne de texte (string), on la laisse
                # ouvrir ses guillemets librement
                if param_type == "string":
                    if parts[1].count('"') < 2:
                        return scores

                # Si rien (ou juste des espaces) n'a encore été écrit après
                # les deux-points, on restreint au type attendu
                elif not parts[1].strip():
                    new_scores: list[float] = selection_type(param_type,
                                                             vocab,
                                                             scores)
                    return new_scores

            return scores

        # L'IA écrit un nom de CLÉ, on restreint le vocabulaire aux clés
        # restantes valides
        keys_list: list[str] = filter_list_str(param, list_unused_keys)

        new_scores: list[float] = filter_score(keys_list, param, vocab, scores)
    else:

        return scores
    
    return new_scores
