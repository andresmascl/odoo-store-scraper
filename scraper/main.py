import math
import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = (
    "https://apps.odoo.com/apps/modules/browse/"
    "page/{page}?price=Paid&order=Purchases"
)

def get_total_pages() -> int:
    """Fetch first page and read pagination for total page count."""
    resp = requests.get(BASE_URL.format(page=1), timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Adjust selector to match pagination link that contains the last page number.
    last_page_link = soup.select_one("ul.pagination li:last-child a")
    total_pages = int(last_page_link.text.strip())
    return total_pages

def parse_app_summary(card) -> dict:
    """Extract app info from a listing card on the catalog page."""
    name = card.select_one("h3 a").text.strip()
    url = "https://apps.odoo.com" + card.select_one("h3 a")["href"]
    description = card.select_one("p.app_description").text.strip()
    price = card.select_one("span.price").text.strip()
    units_last_month = card.select_one("span.badge.sales").text.strip()
    return {
        "app name": name,
        "app description": description,
        "app url": url,
        "app price": price,
        "units sold last month": units_last_month,
    }

def get_lines_of_code(app_url: str) -> str:
    """Visit app detail page and scrape lines-of-code metric."""
    resp = requests.get(app_url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Selector depends on page layout; adjust after inspecting actual HTML.
    loc_tag = soup.select_one("span:contains('Lines of Code')")
    lines_of_code = loc_tag.find_next("span").text.strip()
    return lines_of_code

def scrape_all_apps() -> pd.DataFrame:
    total_pages = get_total_pages()
    records = []

    for page in range(1, total_pages + 1):
        resp = requests.get(BASE_URL.format(page=page), timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.card.app")

        for card in cards:
            info = parse_app_summary(card)
            info["lines of code"] = get_lines_of_code(info["app url"])
            records.append(info)

    return pd.DataFrame(records)

def main():
    df = scrape_all_apps()
    print(df)

if __name__ == "__main__":
    main()
