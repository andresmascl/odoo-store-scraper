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
# Keep page turns snappy to advance the progress bar
MAX_NAVIGATION_RETRIES = 3
RETRY_DELAY_SECONDS = 2
# Short waits for network idle and card visibility
NETWORK_IDLE_WAIT_MS = 1800
CARD_WAIT_MS = 1800
# Short locator timeout on detail pages for LOC
LOC_TIMEOUT_MS = 1000
ITEMS_PER_PAGE = 20
DESKTOP_UA = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
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
    """Extract app info from a listing card using current DOM structure.

    - Name: <h5 title="..."><b>...</b></h5>
    - Price: <span class="oe_currency_value">...</span>
    - Purchases: <span title="Total Purchases: X, Last month: Y"> X | Y </span>
    - URL: <a href="/apps/modules/...">...</a>
    """
    def safe_text(selector: str) -> str:
        loc = card.locator(selector).first
        try:
            if loc.count() > 0:
                return (loc.inner_text() or "").strip()
        except Exception:
            pass
        return ""

    def safe_attr(selector: str, attr: str) -> str:
        loc = card.locator(selector).first
        try:
            if loc.count() > 0:
                val = loc.get_attribute(attr)
                return val or ""
        except Exception:
            pass
        return ""

    # URL
    href = safe_attr("a[href*='/apps/modules/']", "href")
    url = href
    if url and url.startswith("/"):
        url = "https://apps.odoo.com" + url
    elif url and not url.startswith("http"):
        url = "https://apps.odoo.com" + ("/" if not url.startswith("/") else "") + url

    # Name (prefer the title attribute if present)
    name = safe_attr("h5[title]", "title") or safe_text("h5 b") or safe_text("h5")

    # Price
    price = safe_text("span.oe_currency_value")

    # Purchases (parse "total | last")
    purchases_text = safe_text("span[title^='Total Purchases']") or safe_text("span:has(.fa-shopping-cart)")
    last_month = ""
    if purchases_text:
        parts = [p.strip() for p in purchases_text.split("|")]
        if len(parts) >= 2:
            last_month = parts[1]

    # Description if available
    description = safe_text("p.app_description, .app_description")

    return {
        "app name": name,
        "app description": description,
        "app url": url,
        "app price": price,
        "units sold last month": last_month,
    }

def get_lines_of_code(app_url: str, context) -> str:
        """Visit app detail page and read 'Lines of code' from the details table.

        Uses a single robust locator and short timeout to avoid halts.
        """
        page = context.new_page()
        page.set_default_navigation_timeout(DEFAULT_NAVIGATION_TIMEOUT_MS)
        try:
                page.goto(app_url, wait_until="domcontentloaded")
                selector = (
                        "table.loempia_app_table tr:has(td b:has-text('Lines of code')) "
                        "td:nth-child(2) span"
                )
                loc = page.locator(selector).first
                try:
                        text = loc.text_content(timeout=LOC_TIMEOUT_MS)
                except Exception:
                        text = None
                return (text or "N/A").strip() or "N/A"
        finally:
                page.close()

def scrape_all_apps(headless: bool = True, csv_path: str = "scraped_apps.csv") -> pd.DataFrame:
        """Scrape summary information for all paid apps.

        Args:
                headless: Whether to run the browser in headless mode.
                csv_path: Path where results are incrementally written.
        """
        records: list[dict] = []

        start_page = 1
        # Sidecar progress file lives next to the CSV and is named 'scrape.next'
        sidecar_path = os.path.join(os.path.dirname(os.path.abspath(csv_path)), "scrape.next")

        def _read_start_page() -> int:
                # Only use sidecar file. If missing or invalid, start from 1.
                if os.path.exists(sidecar_path):
                        try:
                                with open(sidecar_path, "r", encoding="utf-8") as f:
                                        txt = (f.read() or "").strip()
                                if txt.isdigit():
                                        return int(txt)
                        except Exception as e:
                                logging.warning("Failed reading sidecar %s: %s", sidecar_path, e)
                return 1

        start_page = _read_start_page()

        def _write_sidecar(page_no: int) -> None:
                """Atomically write next page number to sidecar file."""
                tmp = sidecar_path + ".tmp"
                try:
                        with open(tmp, "w", encoding="utf-8") as f:
                                f.write(str(page_no).strip() + "\n")
                        os.replace(tmp, sidecar_path)
                finally:
                        try:
                                if os.path.exists(tmp):
                                        os.remove(tmp)
                        except Exception:
                                pass

        # Launch Firefox
        with sync_playwright() as playwright:
                        engine = getattr(playwright, "firefox")
                        browser = engine.launch(headless=headless)
                        # Ignore HTTPS issues and mimic a normal desktop browser to avoid bot heuristics
                        context = browser.new_context(
                                ignore_https_errors=True,
                                user_agent=DESKTOP_UA,
                                locale="en-US",
                                timezone_id="UTC",
                                viewport={"width": 1366, "height": 768},
                                device_scale_factor=1,
                                color_scheme="light",
                                extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
                        )
                        page = context.new_page()
                        page.set_default_navigation_timeout(DEFAULT_NAVIGATION_TIMEOUT_MS)

                        total_pages = get_total_pages(page)

                        with tqdm(total=total_pages, desc="Scraping pages") as pbar:
                                for current_page in range(start_page, total_pages + 1):
                                        existing_file = os.path.exists(csv_path)
                                        url = BASE_URL.format(page=current_page)
                                        success = False
                                        for attempt in range(1, MAX_NAVIGATION_RETRIES + 1):
                                                try:
                                                        # Navigate and wait for DOM content, then a brief idle
                                                        page.goto(url, wait_until="domcontentloaded")
                                                        try:
                                                                page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_WAIT_MS)
                                                        except Exception:
                                                                pass
                                                                # Small scroll to trigger lazy rendering
                                                                try:
                                                                        page.evaluate("window.scrollBy(0, 200)")
                                                                except Exception:
                                                                        pass
                                                        sel = "div.loempia_app_entry.loempia_app_card[data-publish='on']"
                                                        try:
                                                                page.wait_for_selector(sel, state="visible", timeout=CARD_WAIT_MS)
                                                                success = True
                                                                break
                                                        except Exception:
                                                                logging.warning(
                                                                        "No cards detected on page %s after %s attempts. Skipping.",
                                                                        current_page,
                                                                        MAX_NAVIGATION_RETRIES,
                                                                        )                                                                                                
                                                                continue
                                                except TimeoutError:
                                                        pass
                                                        time.sleep(RETRY_DELAY_SECONDS)
                                        # Prefer new loempia app card classes, with fallbacks
                                        cards = page.locator(
                                                "div.loempia_app_entry.loempia_app_card[data-publish='on']"
                                        )
                                        count = cards.count()
                                        if count == 0:
                                                logging.warning(
                                                        "No app cards found on page %s. Capturing screenshot.",
                                                        current_page,
                                                )
                                                try:
                                                        page.screenshot(path=f"page_{current_page}_empty.png", full_page=True)
                                                except Exception:
                                                                pass
                                                pbar.update(1)
                                                continue

                                        page_records: list[dict] = []
                                        for i in range(count):
                                                card = cards.nth(i)
                                                info = parse_app_summary(card)
                                                try:
                                                        info["lines of code"] = get_lines_of_code(
                                                                info["app url"], context
                                                        )
                                                except Exception as e:
                                                        logging.warning(
                                                                        "Failed to parse lines of code for %s: %s",
                                                                        info["app url"],
                                                                        e,
                                                                )
                                                        info["lines of code"] = "N/A"
                                                records.append(info)
                                                page_records.append(info)

                                        df_page = pd.DataFrame(page_records)
                                        # Write with a context manager to ensure the file closes after each save
                                        with open(csv_path, "a", encoding="utf-8", newline="") as f:
                                                df_page.to_csv(
                                                        f,
                                                        index=False,
                                                        header=(current_page == start_page == 1 and not existing_file),
                                                )
                                        _write_sidecar(current_page + 1)
                                        pbar.update(1)

                        context.close()
                        browser.close()

        return pd.DataFrame(records)

def main():
        headless = os.environ.get("HEADLESS", "1") != "0"
        csv_path = os.environ.get("CSV_PATH", "scraped_apps.csv")
        df = scrape_all_apps(headless=headless, csv_path=csv_path)

if __name__ == "__main__":
        main()
