PYTHON := python3
UV := uv
FILE := src/__main__.py

.PHONY: install run debug clean lint lint-strict

install:
	$(UV) sync

run:
	$(UV) run python -m src \
		--functions_definition data/input/functions_definition.json \
		--input data/input/function_calling_tests.json \
		--output data/output/function_calling_results.json

debug:
	$(UV) run python -m pdb $(FILE)

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache .uv_cache
	rm -rf dist build *.egg-info
	find . -name "*.pyc" -delete

lint:
	$(UV) run flake8 .
	$(UV) run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs --exclude llm_sdk

lint-strict:
	$(UV) run flake8 .
	$(UV) run mypy . --strict