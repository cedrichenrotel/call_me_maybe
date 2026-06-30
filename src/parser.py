import sys
try:
    from pydantic import BaseModel, field_validator
    from pathlib import Path
except ImportError:
    sys.exit()


class Parser(BaseModel):

    input: Path
    output: Path
    functions_definition: Path

    """checks whether the files exist by verifying that the path is correct"""
    @field_validator('input', 'functions_definition')
    @classmethod
    def exit_path(cls, p: Path) -> Path:

        if not p.is_file():
            raise ValueError(f'The path to the {p} file does not exist')
        return p

    """checks whether the file type is .json"""
    @field_validator('input', 'functions_definition', 'output')
    @classmethod
    def valid_type_file(cls, p: Path) -> Path:

        if p.suffix != '.json':
            raise ValueError(f'{p}: Incorrect file format')
        return p
