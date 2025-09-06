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

## Docker

Build the image:

```
make docker-build
```

Run the scraper in a container, writing results to `scraped_apps.csv` in the current directory:

```
make docker-run
```

You can customize the behavior with environment variables. For example, to run with a visible browser and save to a different file:

```
docker run --rm -e HEADLESS=0 -e CSV_PATH=/data/apps.csv -v $(pwd):/data odoo-store-scraper
```

## Cleanup

Remove the virtual environment:

```
make clean
```

