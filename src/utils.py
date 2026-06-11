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
