import sys

try:
    from pydantic import BaseModel
    from typing import TypeVar
    import torch
    import numpy
except ImportError:
    sys.exit()


T = TypeVar('T', BOUND=BaseModel)


def convert_in_models(data: list[dict],
                      obj: type[T]) -> list[T]:

    obj_model: list[BaseModel] = []

    for i in data:
        obj_model.append(obj(**i))

    return obj_model


def bracket_validator(s: str) -> bool:

    stock: list[str] = []
    ref: dict = {'}': '{'}

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
                    json_tokens: list[int]) -> list[float]:

    input_ids: list[float] = lst_token[0].tolist() + json_tokens
    return input_ids


def select_best_token(json_tokens: list[int],
                      scores: list[float]) -> list[int]:

    best_token: int = int(numpy.argmax(scores))
    json_tokens.append(best_token)
    return json_tokens
