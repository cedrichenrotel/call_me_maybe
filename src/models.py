import sys
try:
    from pydantic import BaseModel
    from typing import Any
except ImportError:
    sys.exit()


class FunctionsDefinition(BaseModel):
    name: str
    parameters: dict


class PromptTest(BaseModel):
    prompt: str


class FunctionCall(BaseModel):
    name: str
    parameters: dict[str, Any]
