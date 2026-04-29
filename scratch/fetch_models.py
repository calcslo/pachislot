from playwright.sync_api import sync_playwright

SITE1_URL = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SITE1_URL, wait_until="networkidle")
        
        # Click Pachinko button
        try:
            page.click("body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(1) > a > img")
            page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"Error clicking button: {e}")
            return
            
        page.wait_for_timeout(3000) # Give it time to load models
        
        # Scroll to load all
        for _ in range(5):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            
        elements = page.query_selector_all("ul#ulKI div.nc-label")
        
        with open("site_models.txt", "w", encoding="utf-8") as f:
            for el in elements:
                text = el.inner_text().strip()
                hex_str = text.encode('utf-8').hex()
                f.write(f"NAME: {repr(text)} | HEX: {hex_str}\n")
                
        print(f"Wrote {len(elements)} models to site_models.txt")
        browser.close()

if __name__ == "__main__":
    run()
