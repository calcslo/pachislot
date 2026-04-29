from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 390, 'height': 844})
    page.goto('https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/', wait_until='networkidle')
    page.click('body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(1) > a > img')
    page.wait_for_load_state('networkidle')
    time.sleep(2)
    model_btn = page.query_selector("//div[contains(@class, 'nc-label') and text()='e魔法少女まどかﾏｷﾞｶ3LPM1']")
    model_btn.click()
    page.wait_for_load_state('networkidle')
    time.sleep(2)
    num_btn = page.query_selector("a.btn-dai:has-text('0269')")
    num_btn.click()
    page.wait_for_load_state('networkidle')
    time.sleep(2)
    with open('scratch/page.html', 'w', encoding='utf-8') as f:
        f.write(page.content())
    print("Page saved.")
    browser.close()
