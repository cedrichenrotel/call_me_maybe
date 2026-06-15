import sys

try:
    from pydantic import BaseModel
except ImportError:
    sys.exit()


def convert_in_models(data: list[dict],
                      obj: type[BaseModel]) -> list[BaseModel]:

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
    return len(stock) == 0
