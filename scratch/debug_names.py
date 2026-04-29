from scrapling.fetchers import StealthyFetcher
from playwright.sync_api import Page
import pscube_calculator as calc

SITE1_URL = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/"
SITE1_MODEL_LIST = "ul#ulKI.nc-listview.nc-listview-kisyu div.nc-label"

def action_wrapper(page: Page):
    page.goto(SITE1_URL, wait_until="networkidle")
    # Click Pachinko button
    page.click("body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(1) > a > img")
    page.wait_for_load_state("networkidle")
    
    # Scroll to load all
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    import time
    time.sleep(2)
    
    model_elements = page.query_selector_all(SITE1_MODEL_LIST)
    site_models = [el.inner_text().strip() for el in model_elements]
    
    target_models = list(calc.BORDER_DICT.keys())
    
    print("Site Models found:", len(site_models))
    for sm in site_models:
        if "からくり" in sm or "Re:ｾﾞﾛ" in sm:
            print(f"Found on site: '{sm}' (hex: {sm.encode().hex()})")
            
    print("\nTarget Models in BORDER_DICT:")
    for tm in target_models:
        if "からくり" in tm or "Re:ｾﾞﾛ" in tm:
            print(f"In BORDER_DICT: '{tm}' (hex: {tm.encode().hex()})")
            
            if tm in site_models:
                print(f"MATCH: '{tm}' found on site.")
            else:
                print(f"NO MATCH: '{tm}' NOT found on site exactly.")
                # Check for similarities
                for sm in site_models:
                    if "からくり" in sm or "Re:ｾﾞﾛ" in sm:
                        if sm == tm:
                            print(f"Wait, sm == tm is true? but tm in site_models was false?")
                        else:
                            import difflib
                            diff = difflib.ndiff(tm, sm)
                            print(f"Diff with '{sm}': {''.join(diff)}")

StealthyFetcher.fetch(
    SITE1_URL,
    page_action=action_wrapper,
    headless=True,
    proxy="http://localhost:8118",
    locale="ja-JP"
)
