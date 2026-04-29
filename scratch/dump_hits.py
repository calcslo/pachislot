from scrapling.fetchers import StealthyFetcher
from playwright.sync_api import Page
import time

def action(page: Page):
    # Direct navigation to the machine page
    page.goto('https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/cgi-bin/nc-v06-001.php?model_id=1418&machine_no=0269')
    page.wait_for_load_state('networkidle')
    time.sleep(5)

    # Get the hit history table rows and their payout cells
    hits = page.evaluate('''() => {
        const results = [];
        const items = document.querySelectorAll('td[class*="toku-"], div[class*="toku-"]');
        items.forEach((item, i) => {
            if (i < 30) {
                results.push({
                    index: i,
                    text: item.innerText.trim(),
                });
            }
        });
        return results;
    }''')
    print("=== Hit History Items ===")
    for h in hits:
        print(f"Hit {h['index']}: {h['text'].replace('\\n', ' | ')}")

StealthyFetcher.fetch(
    'https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/',
    page_action=action,
    headless=True
)
