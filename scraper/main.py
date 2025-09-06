import pandas as pd
from playwright.sync_api import sync_playwright

BASE_URL = (
    "https://apps.odoo.com/apps/modules/browse/"
    "page/{page}?price=Paid&order=Purchases"
)

def get_total_pages(page) -> int:
    """Fetch first page and read pagination for total page count."""
    page.goto(BASE_URL.format(page=1))
    last_page_link = page.locator("ul.pagination li:last-child a")
    total_pages = int(last_page_link.inner_text().strip())
    return total_pages

def parse_app_summary(card) -> dict:
    """Extract app info from a listing card on the catalog page."""
    name = card.locator("h3 a").inner_text().strip()
    url = "https://apps.odoo.com" + card.locator("h3 a").get_attribute("href")
    description = card.locator("p.app_description").inner_text().strip()
    price = card.locator("span.price").inner_text().strip()
    units_last_month = card.locator("span.badge.sales").inner_text().strip()
    return {
        "app name": name,
        "app description": description,
        "app url": url,
        "app price": price,
        "units sold last month": units_last_month,
    }

def get_lines_of_code(app_url: str, context) -> str:
    """Visit app detail page and scrape lines-of-code metric."""
    page = context.new_page()
    page.goto(app_url)
    loc_tag = page.locator("span:has-text('Lines of Code')")
    lines_of_code = (
        loc_tag.locator("xpath=following-sibling::span").first.inner_text().strip()
    )
    page.close()
    return lines_of_code

def scrape_all_apps() -> pd.DataFrame:
    records = []
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        total_pages = get_total_pages(page)

        for current_page in range(1, total_pages + 1):
            page.goto(BASE_URL.format(page=current_page))
            cards = page.locator("div.card.app")
            count = cards.count()

            for i in range(count):
                card = cards.nth(i)
                info = parse_app_summary(card)
                info["lines of code"] = get_lines_of_code(info["app url"], context)
                records.append(info)

        context.close()
        browser.close()

    return pd.DataFrame(records)

def main():
    df = scrape_all_apps()
    print(df)

if __name__ == "__main__":
    main()
