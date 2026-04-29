from scrapling.fetchers import StealthyFetcher
from playwright.sync_api import Page
import time

def action(page: Page):
    page.goto('https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/cgi-bin/nc-v06-001.php?model_id=1418&machine_no=0269')
    page.wait_for_load_state('networkidle')
    time.sleep(5)

    graph_paths = page.evaluate('''() => {
        const paths = document.querySelectorAll('.amcharts-graph-stroke');
        return Array.from(paths).map((p, i) => {
            const totalLen = p.getTotalLength();
            const lastPt = p.getPointAtLength(totalLen);
            const parent = p.parentElement;
            return {
                index: i,
                className: p.getAttribute('class'),
                parentClass: parent ? parent.getAttribute('class') : 'none',
                lastY: lastPt.y
            };
        });
    }''')
    print('=== Graph Paths ===')
    for p in graph_paths:
        print(f"Path {p['index']}: parent={p['parentClass']}, y={p['lastY']}")

StealthyFetcher.fetch(
    'https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/',
    page_action=action,
    headless=True
)
