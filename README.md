*This project has been created as part of the 42 curriculum by cehenrot*

# Call Me Maybe — Function Calling with Constrained Decoding

## Description

This project implements a **function calling tool** that translates natural language prompts into structured JSON function calls using a small language model (Qwen/Qwen3-0.6B). Instead of relying on the model to spontaneously produce valid JSON, the system uses **constrained decoding** to guide token selection at every step, guaranteeing 100% valid and schema-compliant output.

Given a prompt like `"What is the sum of 40 and 2?"`, the program outputs:

```json
{
    "prompt": "What is the sum of 40 and 2?",
    "name": "fn_add_numbers",
    "parameters": {"a": 40.0, "b": 2.0}
}
```

---

## Instructions

### Requirements

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) package manager

### Installation

```bash
uv sync
```

### Running the program

```bash
make run
```

Or directly:

```bash
uv run python -m src \
  --functions_definition data/input/functions_definition.json \
  --input data/input/function_calling_tests.json \
  --output data/output/function_calling_results.json
```

All three arguments are optional and default to the paths shown above.

### Other Makefile targets

| Command | Description |
|---|---|
| `make install` | Install dependencies |
| `make run` | Run the program |
| `make debug` | Run with Python debugger (pdb) |
| `make clean` | Remove caches and build artifacts |
| `make lint` | Run flake8 + mypy |
| `make lint-strict` | Run flake8 + mypy --strict |

### Input files

Place your input files in `data/input/`:

- **`function_calling_tests.json`** — array of natural language prompts: `[{"prompt": "..."}]`
- **`functions_definition.json`** — array of function schemas (name, parameters, types, description)

### Output

The result is written to `data/output/function_calling_results.json` — a JSON array where each entry contains `prompt`, `name`, and `parameters`.

---

## Algorithm Explanation

The generation pipeline works as follows:

1. **Prompt encoding**: The prompt and function definitions are combined into a text string, then encoded into token IDs by the LLM SDK.
2. **Token-by-token generation**: At each step, the model produces logits (raw probability scores) for every token in the vocabulary.
3. **Constrained decoding**: Before selecting the next token, the logits are filtered by `constrained_decoding()` based on the current state of the partial JSON string:
   - **Phase 1 — structure prefix**: Forces the output to begin with `{"name":"`.
   - **Phase 2 — function name**: Allows only tokens that continue a valid function name from `functions_definition.json`. Space-prefixed tokens are excluded to prevent names like `f n_greet`.
   - **Phase 3 — parameters**: For each parameter in order, forces the correct key name, then forces `:`, then constrains the value tokens to the declared type (`string`, `number`, `boolean`). For string values, closing quotes and repetition detection are enforced.
4. **Termination**: Generation stops as soon as the bracket validator detects a complete and balanced `{...}` JSON object, or when the token limit is reached.
5. **Type coercion**: After parsing, `number` fields are cast to `float` as required by the schema.

---

## Design Decisions

- **Vocabulary normalisation**: The Qwen tokenizer uses `Ġ` to represent a leading space (BPE artifact). The vocabulary is pre-processed to replace `Ġ` with a real space so that token matching works with plain strings.
- **Pydantic for all validation**: All input models (`FunctionsDefinition`, `PromptTest`, `FunctionCall`, `Parser`) use Pydantic v2 for strict validation with clear error messages.
- **Stateless constrained decoder**: `constrained_decoding()` takes the current JSON string as input and derives the current generation phase from it, making it easy to reason about and test independently.
- **Repetition detection**: A sliding-window `check_repetition()` function detects when the model enters an infinite loop (e.g. generating `([0-9]+)|([0-9]+)|...`) and forces a closing quote to break out.

---

## Performance Analysis

- **JSON validity**: 100% — constrained decoding guarantees every output is parseable and schema-compliant.
- **Function selection accuracy**: The LLM correctly identifies the right function for all standard test cases (add numbers, greet, reverse string).
- **Argument accuracy**: Number arguments are extracted and typed correctly. String arguments match the prompt content.
- **Speed**: All test prompts are processed in well under 5 minutes on standard CPU hardware.
- **Limitation**: For complex string values (regex patterns, special characters), the model may sometimes generate slightly redundant content before the repetition guard triggers. This is a model capacity limitation of the 0.6B parameter model, not a structural failure.

---

## Challenges Faced

- **Closing quote not recognized**: The `is_key_complete()` function initially only checked for `,` or `}` to detect a complete string value, causing an infinite loop. Fixed by also counting unescaped quotes (`>= 2` means the value is closed).
- **Space in function name**: The tokenizer produces tokens like `Ġn_greet` (with a leading space), which was being matched as a continuation of `fn_greet`. Fixed by filtering out space-prefixed tokens during function name generation.
- **Regex repetition**: The model tends to repeat patterns such as `([0-9]+)|` indefinitely. Solved with a sliding-window repetition detector that forces a closing `"` when a repeating suffix is detected.
- **mypy strict mode**: Getting all files to pass `mypy --strict` required fixing unparameterised generics (`dict` → `dict[str, Any]`), adding `@classmethod` to Pydantic validators, and configuring `pyproject.toml` to suppress unavoidable errors from missing third-party stubs.

---

## Testing Strategy

The implementation was validated by running the program against the provided test suite (`function_calling_tests.json`) and checking:

1. The output file is valid JSON (parseable by `json.load()`).
2. Each entry contains exactly `prompt`, `name`, and `parameters`.
3. The function name matches one of the definitions in `functions_definition.json`.
4. Parameter types match the declared schema (numbers are `float`, strings are `str`).
5. Edge cases tested: greeting with various names, number addition with different magnitudes, string reversal.

---

## Example Usage

```bash
$ make run
# Processes all prompts in data/input/function_calling_tests.json
# Writes results to data/output/function_calling_results.json
```

Example output (`data/output/function_calling_results.json`):

```json
[
    {
        "prompt": "What is the sum of 2 and 3?",
        "name": "fn_add_numbers",
        "parameters": {"a": 2.0, "b": 3.0}
    },
    {
        "prompt": "Greet john",
        "name": "fn_greet",
        "parameters": {"name": "john"}
    },
    {
        "prompt": "Reverse the string 'hello'",
        "name": "fn_reverse_string",
        "parameters": {"s": "hello"}
    }
]
```

---

## Resources

### Documentation & References

- [Qwen3 model — HuggingFace](https://huggingface.co/Qwen/Qwen3-0.6B)
- [Constrained Decoding — Outlines library (concept)](https://github.com/outlines-dev/outlines)
- [Pydantic v2 documentation](https://docs.pydantic.dev/latest/)
- [Python type hints — PEP 484](https://peps.python.org/pep-0484/)
- [PEP 257 — Docstring conventions](https://peps.python.org/pep-0257/)
- [JSON specification — RFC 8259](https://datatracker.ietf.org/doc/html/rfc8259)

### AI Usage

AI (Claude, via Claude Code) was used throughout this project for the following tasks:

- **Debugging**: Diagnosing the infinite loop in string value generation, and the `fn_greet` → `f n_greet` tokenization bug.
- **Type checking**: Resolving all `mypy --strict` errors across the codebase (unparameterised generics, missing `@classmethod` decorators, TypeVar issues).
- **Algorithm design discussion**: Understanding and explaining the sliding-window repetition detection approach used in `check_repetition()`.
- **Code review**: Auditing the project against subject requirements and identifying missing or non-conforming elements.

All AI-generated suggestions were reviewed, tested, and validated before integration. The core constrained decoding logic and algorithm design decisions were developed and understood by the author.
