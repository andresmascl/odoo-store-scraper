import time
import logging
import pandas as pd
from playwright.sync_api import TimeoutError, sync_playwright
from tqdm import tqdm
import os

BASE_URL = (
    "https://apps.odoo.com/apps/modules/browse/"
    "page/{page}?price=Paid&order=Purchases"
)

DEFAULT_NAVIGATION_TIMEOUT_MS = 60_000
MAX_NAVIGATION_RETRIES = 3
RETRY_DELAY_SECONDS = 5

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
    page.set_default_navigation_timeout(DEFAULT_NAVIGATION_TIMEOUT_MS)
    page.goto(app_url)
    loc_tag = page.locator("span:has-text('Lines of Code')")
    lines_of_code = (
        loc_tag.locator("xpath=following-sibling::span").first.inner_text().strip()
    )
    page.close()
    return lines_of_code

def scrape_all_apps(headless: bool = True, csv_path: str = "scraped_apps.csv") -> pd.DataFrame:
    """Scrape summary information for all paid apps.

    Args:
        headless: Whether to run the browser in headless mode.
        csv_path: Path where results are incrementally written.
    """
    records: list[dict] = []

    # Start with a fresh file each run
    if os.path.exists(csv_path):
        os.remove(csv_path)

    # Launch Firefox in headless mode for environments without a display
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=headless)
        # Ignore HTTPS certificate issues that may appear in automated environments
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.set_default_navigation_timeout(DEFAULT_NAVIGATION_TIMEOUT_MS)

        total_pages = get_total_pages(page)

        with tqdm(total=total_pages, desc="Scraping pages") as pbar:
            for current_page in range(1, total_pages + 1):
                for _ in range(MAX_NAVIGATION_RETRIES):
                    try:
                        page.goto(BASE_URL.format(page=current_page))
                        break
                    except TimeoutError:
                        time.sleep(RETRY_DELAY_SECONDS)
                else:
                    logging.warning(
                        "Failed to load page %s after %s attempts. Skipping.",
                        current_page,
                        MAX_NAVIGATION_RETRIES,
                    )
                    pbar.update(1)
                    continue
                # Capture a screenshot on the first page to verify visibility
                if current_page == 1:
                    page.screenshot(path="page1.png")
                cards = page.locator("div.card.app")
                count = cards.count()

                page_records: list[dict] = []
                for i in range(count):
                    card = cards.nth(i)
                    info = parse_app_summary(card)
                    info["lines of code"] = get_lines_of_code(
                        info["app url"], context
                    )
                    records.append(info)
                    page_records.append(info)

                df_page = pd.DataFrame(page_records)
                file_exists = os.path.exists(csv_path)
                df_page.to_csv(
                    csv_path,
                    mode="a",
                    index=False,
                    header=not file_exists,
                )

                pbar.update(1)

        context.close()
        browser.close()

    return pd.DataFrame(records)

def main():
    df = scrape_all_apps()
    print(df)

if __name__ == "__main__":
    main()
