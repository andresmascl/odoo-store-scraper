# odoo-store-scraper

Tool for scraping the Odoo store. It might be helpful for vendors and developers who want to understand the shape of the Odoo apps marketplace.

## Requirements
- Python 3.8+
- Linux host machine

## Setup

Create a virtual environment and install dependencies.  **Note thsis will also install playwright dependencies on the host machine**:

```
make venv
```

## Running

Execute the scraper:

```
make run
```

While running, a file `scraped_apps.csv` is updated after each page so you can
inspect progress live. The script still prints the final pandas DataFrame to
stdout with columns:

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

