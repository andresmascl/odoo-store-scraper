VENV ?= .venv
PYTHON := $(VENV)/bin/python
PLAYWRIGHT := $(VENV)/bin/playwright
IMAGE ?= odoo-store-scraper

.PHONY: venv clean run docker-build docker-run

venv: $(PYTHON)

$(PYTHON): requirements.txt
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -r requirements.txt
	$(PLAYWRIGHT) install-deps


clean:
	rm -rf $(VENV)

run: $(PYTHON)
	$(PYTHON) scraper/main.py

docker-build:
	docker build -t $(IMAGE) .

docker-run:
	docker run --rm -v $(PWD):/data -e CSV_PATH=/data/scraped_apps.csv $(IMAGE)
