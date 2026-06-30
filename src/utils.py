import sys

try:
    from typing import TypeVar, Any
    import torch
    import numpy
except ImportError:
    sys.exit()


T = TypeVar('T')


def convert_in_models(data: list[dict[str, Any]],
                      obj: type[T]) -> list[T]:

    result: list[T] = []
    for i in data:
        result.append(obj(**i))
    return result


def bracket_validator(s: str) -> bool:

    stock: list[str] = []
    ref: dict[str, str] = {'}': '{'}

    if not s or '{' not in s:
        return False

    for i in s:
        if i == '{':
            stock.append(i)
        elif i == '}':
            if not stock or stock[-1] != ref[i]:
                return False
            stock.pop()
    return len(stock) == 0


def build_input_ids(lst_token: torch.Tensor,
                    json_tokens: list[int]) -> list[int]:

    input_ids: list[int] = (
        [int(x) for x in lst_token[0].tolist()] + json_tokens
    )
    return input_ids


def select_best_token(json_tokens: list[int],
                      scores: list[float]) -> list[int]:

    best_token: int = int(numpy.argmax(scores))
    json_tokens.append(best_token)
    return json_tokens
