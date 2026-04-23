from playwright.sync_api import sync_playwright
import time
import os

def run():
    os.makedirs('scratch', exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 390, 'height': 844})
        page = context.new_page()
        page.goto('https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/')
        time.sleep(3)
        page.click('body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(2) > a')
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(2)
        page.click('div.nc-label:has-text("LニューキングハナハナV")')
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        page.click('a.btn-dai:has-text("0845")')
        page.wait_for_load_state('networkidle')
        time.sleep(5)
        html = page.content()
        with open('scratch/slot_detail.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Saved to scratch/slot_detail.html')
        browser.close()

if __name__ == '__main__':
    run()
