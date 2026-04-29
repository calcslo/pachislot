from scrapling.fetchers import StealthyFetcher
from playwright.sync_api import Page

SITE1_URL = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/"
SITE1_MODEL_LIST = "ul#ulKI.nc-listview.nc-listview-kisyu div.nc-label"

def action_wrapper(page: Page):
    page.goto(SITE1_URL, wait_until="networkidle")
    # Click Pachinko button
    try:
        page.click("body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(1) > a > img")
        page.wait_for_load_state("networkidle")
    except:
        pass
    
    # Wait for models to load
    page.wait_for_selector(SITE1_MODEL_LIST, timeout=10000)
    
    model_elements = page.query_selector_all(SITE1_MODEL_LIST)
    for el in model_elements:
        text = el.inner_text().strip()
        if "からくり" in text or "Re:ｾﾞﾛ" in text:
            print(f"SITE_NAME: {repr(text)} | HEX: {text.encode('utf-8').hex()}")

StealthyFetcher.fetch(
    SITE1_URL,
    page_action=action_wrapper,
    headless=True,
    proxy="http://localhost:8118",
    locale="ja-JP"
)
