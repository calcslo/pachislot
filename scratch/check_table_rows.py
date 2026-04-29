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
    time.sleep(3)

    # Dump all rows of #tblDAb
    result = page.evaluate('''() => {
        const rows = Array.from(document.querySelectorAll("#tblDAb tr"));
        return rows.map((r, i) => {
            const cells = Array.from(r.querySelectorAll("td")).map(c => c.innerText.trim());
            return {row: i, cells};
        });
    }''')
    print("=== #tblDAb rows ===")
    for r in result:
        print(f"Row {r['row']}: {r['cells']}")

    # Also get Y-axis labels from the amcharts graph
    graph_info = page.evaluate('''() => {
        const labels = Array.from(document.querySelectorAll(".amcharts-value-axis .amcharts-axis-label"));
        const labelVals = labels.map(l => l.textContent.trim());
        const path = document.querySelector(".amcharts-graph-stroke");
        let lastVal = null;
        if (path) {
            const totalLen = path.getTotalLength();
            const lastPt = path.getPointAtLength(totalLen);
            const matrix = path.getScreenCTM();
            const screenPt = lastPt.matrixTransform(matrix);
            lastVal = {svgX: lastPt.x, svgY: lastPt.y, screenY: screenPt.y};
        }
        return {axisLabels: labelVals, lastGraphPoint: lastVal};
    }''')
    print("\n=== Graph axis labels ===")
    print("Y-axis labels:", graph_info['axisLabels'])
    print("Last graph point:", graph_info['lastGraphPoint'])

    browser.close()
