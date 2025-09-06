# odoo-store-scraper
Tool for scraping the Odoo store.  It might be helpful for vendors and developers who want to understand the shape of the Odoo apps marketplace

## Running locally
Install dependencies:

pip install -r requirements.txt
Execute the script:

python scraper/main.py
The output will be a pandas DataFrame printed to stdout with columns:

app name

app description

app url

app price

units sold last month

lines of code

Adjust CSS selectors (select_one, select) according to the actual HTML structure after inspecting the Odoo pages in a browser.