import sys
try:
    from pydantic import BaseModel, field_validator
    from error import ParseError
    from pathlib import Path
except ImportError:
    sys.exit()


class Parser(BaseModel):

    input: Path
    output: Path
    functions_definition: Path

    """verifie si les fichier exit en verifiant si le chemin est correct"""
    @field_validator('input', 'functions_definition')
    def exit_path(cls, p: Path) -> Path:

        if not p.is_file():
            raise FileNotFoundError(f'The path to the {p} file does not exist')
        return p

    """verifie si le type de fichier est .json"""
    @field_validator('input', 'functions_definition', 'output')
    def valid_type_file(cls, p: Path) -> None:

        if p.suffix != '.json':
            raise ParseError(f'{p}: Incorrect file format')
