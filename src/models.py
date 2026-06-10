import sys
try:
    from pydantic import BaseModel, field_validator, BaseModel
    from error import ParseError
except ImportError:
    sys.exit()


class FunctionsDefinition(BaseModel):
    name: str
    parameters: dict

    
