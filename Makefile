PYTHON := python3
UV := uv
VENV := .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
FILE := src/main.py

.PHONY: install run debug clean lint lint-strict build

$(VENV)/bin/activate:
	$(UV) venv $(VENV)
	$(PIP) install --upgrade pip
	touch $(VENV)/bin/activate

venv: $(VENV)/bin/activate

install: venv
	$(PIP) install -r requirements.txt

run: venv
	@PYTHONPATH=src $(PY) -W ignore src/main.py $(MAP)

debug: venv
	$(PY) -m pdb $(FILE)

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache .uv_cache
	rm -rf dist build *.egg-info
	find . -name "*.pyc" -delete

lint: venv
	$(PY) -m flake8 . --exclude=$(VENV)
	$(PY) -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports\
		--disallow-untyped-defs --check-untyped-defs

lint-strict: venv
	$(PY) -m flake8 . --exclude=$(venv)
	$(PY) -m mypy . --strict --exclude=$(VENV)

build: venv
	$(UV) pip install build
	$(PY) -m build --outdir .
	rm -rf *.egg-info