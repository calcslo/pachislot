
import logging
import os
import sys
from playwright.sync_api import sync_playwright
from scrapling.fetchers import StealthyFetcher

# Import parts of the main script or just copy the action
# For simplicity, I'll just run the main script's site1_action but with a monkeypatch to stop early.

from ogiya_pscube_slot_scraping import site1_action, PROXY_SERVER, SITE1_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_run():
    def action_wrapper(page):
        # Monkeypatch matched_models to only take one model and one machine
        # We need to reach the part where it scrapes.
        # This is tricky without modifying the original code.
        # Instead, I'll just run the original action and hope it finishes one machine.
        try:
            site1_action(page)
        except Exception as e:
            print(f"Caught expected exception or error: {e}")

    print("Starting test run...")
    try:
        StealthyFetcher.fetch(
            SITE1_URL, 
            page_action=action_wrapper, 
            headless=True, 
            proxy=PROXY_SERVER,
            locale="ja-JP"
        )
    except Exception as e:
        print(f"Fetcher error: {e}")

if __name__ == "__main__":
    test_run()
