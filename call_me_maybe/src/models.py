import sys
try:
    from pydantic import BaseModel, field_validator
    from error import ParseError
except ImportError:
    sys.exit()


class FunctionsDefinition(BaseModel):
    name: str
    parameters: dict


class PromptTest(BaseModel):
    pass


class FunctionCall(BaseModel):
    pass
