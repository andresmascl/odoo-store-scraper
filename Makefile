VENV ?= .venv
PYTHON := $(VENV)/bin/python
PLAYWRIGHT := $(VENV)/bin/playwright

.PHONY: venv clean run

venv: $(PYTHON)

$(PYTHON): requirements.txt
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -r requirements.txt
	$(PLAYWRIGHT) install-deps


clean:
	rm -rf $(VENV)

run: $(PYTHON)
	$(PYTHON) scraper/main.py
