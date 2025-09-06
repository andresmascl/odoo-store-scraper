import pandas as pd
from playwright.sync_api import sync_playwright

BASE_URL = (
    "https://apps.odoo.com/apps/modules/browse/"
    "page/{page}?price=Paid&order=Purchases"
)

def get_total_pages(page) -> int:
    """Fetch first page and read pagination for total page count."""
    page.goto(BASE_URL.format(page=1))
    # The last pagination entry is usually "Next", so grab the second to last
    page.wait_for_selector("ul.pagination li:nth-last-child(2) a")
    last_page_link = page.locator("ul.pagination li:nth-last-child(2) a")
    text = last_page_link.inner_text().strip()
    total_pages = int("".join(filter(str.isdigit, text)))
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
    # Launch Firefox in headless mode for environments without a display
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True)
        # Ignore HTTPS certificate issues that may appear in automated environments
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        total_pages = get_total_pages(page)

        for current_page in range(1, total_pages + 1):
            page.goto(BASE_URL.format(page=current_page))
            # Capture a screenshot on the first page to verify visibility
            if current_page == 1:
                page.screenshot(path="page1.png")
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
