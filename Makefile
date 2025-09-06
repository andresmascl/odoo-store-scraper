VENV ?= .venv
PYTHON := $(VENV)/bin/python

.PHONY: venv clean run

venv: $(PYTHON)

$(PYTHON): requirements.txt
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -r requirements.txt

clean:
	rm -rf $(VENV)

run: $(PYTHON)
	$(PYTHON) scraper/main.py
