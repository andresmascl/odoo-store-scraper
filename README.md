# odoo-store-scraper

Tool for scraping the Odoo store. It might be helpful for vendors and developers who want to understand the shape of the Odoo apps marketplace.

## Setup

Create a virtual environment and install dependencies:

```
make venv
```

## Running

Execute the scraper:

```
make run
```

The output is a pandas DataFrame printed to stdout with columns:

- app name
- app description
- app url
- app price
- units sold last month
- lines of code

Adjust CSS selectors (`select_one`, `select`) according to the actual HTML structure after inspecting the Odoo pages in a browser.

## Cleanup

Remove the virtual environment:

```
make clean
```

