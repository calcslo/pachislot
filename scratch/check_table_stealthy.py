from scrapling.fetchers import StealthyFetcher
from playwright.sync_api import Page
import time

PROXY_SERVER = "http://localhost:8118"

result_data = {}

def action(page: Page):
    time.sleep(2)
    page.click('body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(1) > a > img')
    page.wait_for_load_state('networkidle')
    time.sleep(2)

    model_btn = page.query_selector("//div[contains(@class, 'nc-label') and text()='e魔法少女まどかﾏｷﾞｶ3LPM1']")
    if model_btn:
        model_btn.click()
        page.wait_for_load_state('networkidle')
        time.sleep(2)

    num_btn = page.query_selector("a.btn-dai:has-text('0269')")
    if num_btn:
        num_btn.click()
        page.wait_for_load_state('networkidle')
        time.sleep(5)

    # Dump all rows of #tblDAb
    rows = page.evaluate('''() => {
        const rows = Array.from(document.querySelectorAll("#tblDAb tr"));
        return rows.map((r, i) => {
            const cells = Array.from(r.querySelectorAll("td")).map(c => c.innerText.trim());
            return {row: i, cells};
        });
    }''')

    graph_info = page.evaluate('''() => {
        const labels = Array.from(document.querySelectorAll(".amcharts-value-axis .amcharts-axis-label"));
        const labelVals = labels.map(l => ({text: l.textContent.trim(), y: l.getBoundingClientRect().top}));
        const path = document.querySelector(".amcharts-graph-stroke");
        let lastVal = null;
        if (path) {
            const totalLen = path.getTotalLength();
            const lastPt = path.getPointAtLength(totalLen);
            const matrix = path.getScreenCTM();
            const screenPt = lastPt.matrixTransform(matrix);
            lastVal = {svgY: lastPt.y, screenY: screenPt.y};
        }
        return {axisLabels: labelVals, lastGraphPoint: lastVal};
    }''')

    result_data['rows'] = rows
    result_data['graph'] = graph_info
    page.screenshot(path='scratch/page_screenshot.png')

StealthyFetcher.fetch(
    'https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/',
    page_action=action,
    headless=False,
    locale='ja-JP'
)

print("=== #tblDAb rows ===")
for r in result_data.get('rows', []):
    print(f"Row {r['row']}: {r['cells']}")

print("\n=== Graph ===")
g = result_data.get('graph', {})
print("Y-axis labels:", g.get('axisLabels'))
print("Last graph point:", g.get('lastGraphPoint'))
