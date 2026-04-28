"""
0枚デバッグスクリプト
グラフの0罫線とグラフパスの最終点の座標差を直接計算して
strokeWidth補正が適切かを検証する
"""
import sys, os, time, random, re, logging, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import Page
from scrapling.fetchers import StealthyFetcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SITE1_URL    = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/"
SLOT_BTN     = "body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(2) > a"
PROXY_SERVER = "http://localhost:8118"
TARGET_MACHINE = "0942"
TARGET_DATE    = "2026-04-26"

# 0枚=0検証JS: グラフの0罫線とパス最終点の詳細を出力
JS_DEBUG_ZERO = r'''
(chartDateId) => {
    const container = document.getElementById(chartDateId);
    if (!container) return {error: 'no container'};
    const svg = container.querySelector('svg');
    if (!svg) return {error: 'no svg'};

    // 全axis-tickのY座標を取得
    const tickPaths = Array.from(svg.querySelectorAll('path.amcharts-axis-tick'));
    const ticks = [];
    for (const tick of tickPaths) {
        const d = tick.getAttribute('d') || '';
        const m = d.match(/M\s*[\d.]+\s*,\s*([\d.]+)/);
        if (!m) continue;
        const localY = parseFloat(m[1]);
        let ancestorTY = 0;
        let tel = tick.parentElement;
        while (tel && tel !== svg) {
            const t = tel.getAttribute('transform') || '';
            const tm = t.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
            if (tm) ancestorTY += parseFloat(tm[2]);
            tel = tel.parentElement;
        }
        ticks.push({ localY, ancestorTY, svgY: localY + ancestorTY });
    }
    ticks.sort((a,b) => a.svgY - b.svgY);

    // ラベル候補 (translateY)
    const allTextEls = Array.from(svg.querySelectorAll('text'));
    const labelCandidates = [];
    for (const textEl of allTextEls) {
        const tspan = textEl.querySelector('tspan');
        if (!tspan) continue;
        const text = tspan.textContent.trim();
        const rawText = text.replace(/[^-0-9]/g, '');
        if (!rawText || isNaN(parseInt(rawText,10))) continue;
        const val = parseInt(rawText,10);
        if (Math.abs(val) > 100000 || text.includes(':')) continue;
        let labelTransY = 0;
        let el = textEl;
        while (el && el !== svg) {
            const t = el.getAttribute('transform') || '';
            const tm = t.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
            if (tm) labelTransY += parseFloat(tm[2]);
            el = el.parentElement;
        }
        labelCandidates.push({ val, labelTransY });
    }

    // 0罫線を特定
    const zeroLabel = labelCandidates.find(lc => lc.val === 0);
    const zeroTick = zeroLabel 
        ? ticks.find(t => Math.abs(t.svgY - zeroLabel.labelTransY) < 30)
        : null;

    // グラフパス最終点
    const graphPath = svg.querySelector('g[class*="amcharts-graph-"] path') ||
                      svg.querySelector('g.amcharts-graph-smoothedLine path');
    let pathInfo = null;
    if (graphPath) {
        const d = graphPath.getAttribute('d') || '';
        const dummyIdx = d.search(/M\s*0[,\s]+0\s*L/);
        const dataPath = dummyIdx > 0 ? d.substring(0, dummyIdx).trim() : d;
        const allCoords = [];
        const mlPat = /[ML]\s*(-?[\d.]+)[,\s]+(-?[\d.]+)/gi;
        const qPat = /Q\s*-?[\d.]+[,\s]+-?[\d.]+[,\s]+(-?[\d.]+)[,\s]+(-?[\d.]+)/gi;
        let mc;
        while ((mc = mlPat.exec(dataPath)) !== null) allCoords.push({x:parseFloat(mc[1]),y:parseFloat(mc[2])});
        while ((mc = qPat.exec(dataPath)) !== null) allCoords.push({x:parseFloat(mc[1]),y:parseFloat(mc[2])});
        allCoords.sort((a,b) => a.x - b.x);
        const last = allCoords[allCoords.length - 1];

        let transY = 0;
        let el2 = graphPath.parentElement;
        while (el2 && el2 !== svg) {
            const t = el2.getAttribute('transform') || '';
            const tm = t.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
            if (tm) transY += parseFloat(tm[2]);
            el2 = el2.parentElement;
        }

        const sw = parseFloat(
            graphPath.getAttribute('stroke-width') ||
            window.getComputedStyle(graphPath).strokeWidth || '1'
        );

        pathInfo = {
            lastLocalY: last ? last.y : null,
            transY,
            gSvgY_center: last ? last.y + transY : null,
            gSvgY_bottom: last ? last.y + transY + sw/2 : null,
            strokeWidth: sw,
            strokeWidthAttr: graphPath.getAttribute('stroke-width'),
            strokeWidthComputed: window.getComputedStyle(graphPath).strokeWidth
        };
    }

    // 0ライン vs パス最終点
    const zeroTickSvgY = zeroTick ? zeroTick.svgY : null;
    const diffCenter = (pathInfo && zeroTickSvgY) ? pathInfo.gSvgY_center - zeroTickSvgY : null;
    const diffBottom = (pathInfo && zeroTickSvgY) ? pathInfo.gSvgY_bottom - zeroTickSvgY : null;

    return {
        ticks: ticks.map(t => ({svgY: t.svgY.toFixed(2), localY: t.localY})),
        labelCandidates: labelCandidates.map(l => ({val: l.val, labelTransY: l.labelTransY.toFixed(2)})),
        zeroLabel,
        zeroTickSvgY,
        pathInfo,
        diffCenter_from0line: diffCenter ? diffCenter.toFixed(4) : null,
        diffBottom_from0line: diffBottom ? diffBottom.toFixed(4) : null,
        interpretation: diffCenter !== null ? (
            `中心: 0ラインより${diffCenter > 0 ? '+' : ''}${(diffCenter/50*1000).toFixed(1)}枚ずれ, ` +
            `下縁: 0ラインより${diffBottom > 0 ? '+' : ''}${(diffBottom/50*1000).toFixed(1)}枚ずれ`
        ) : 'N/A'
    };
}
'''

result_store = {}

def action(page: Page):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(SITE1_URL, wait_until="networkidle")
    time.sleep(random.uniform(2,3))

    page.click(SLOT_BTN)
    page.wait_for_load_state("networkidle")
    time.sleep(random.uniform(1.5,2.5))

    for _ in range(5):
        prev_h = page.evaluate("document.body.scrollHeight")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(0.7)
        if page.evaluate("document.body.scrollHeight") == prev_h: break

    model_btns = page.query_selector_all("a.btn-ki")
    target_btn = None
    for btn in model_btns:
        text = btn.inner_text()
        if "沖" in text and "BLACK" in text:
            target_btn = btn; break
    if not target_btn and model_btns:
        target_btn = model_btns[0]
    if not target_btn: return

    target_btn.click()
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)

    for _ in range(5):
        prev_h = page.evaluate("document.body.scrollHeight")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(0.7)
        if page.evaluate("document.body.scrollHeight") == prev_h: break

    machine_links = page.query_selector_all("a.btn-dai")
    target_machine = None
    for lk in machine_links:
        if lk.inner_text().strip() == TARGET_MACHINE:
            target_machine = lk; break
    if not target_machine:
        logger.error(f"台番号 {TARGET_MACHINE} が見つかりません")
        return

    target_machine.click()
    page.wait_for_load_state("networkidle")
    time.sleep(random.uniform(2,3.5))

    target_ymd = TARGET_DATE.replace("-","")
    chart_id = f"CHART-{target_ymd}"
    tab = page.query_selector(f"#YMD-ul > li[data-ymd='{target_ymd}']")
    if not tab:
        logger.error("タブが見つかりません")
        return

    tab.click()
    try:
        page.wait_for_selector(f"#{chart_id} svg", timeout=8000)
    except: pass
    time.sleep(1.5)

    result = page.evaluate(JS_DEBUG_ZERO, chart_id)
    result_store['data'] = result


def main():
    try:
        r = requests.get("http://httpbin.org/ip",
                         proxies={"http": PROXY_SERVER, "https": PROXY_SERVER}, timeout=10)
        logger.info(f"プロキシOK: {r.json().get('origin')}")
    except Exception as e:
        logger.error(f"プロキシエラー: {e}")
        return

    StealthyFetcher.fetch(SITE1_URL, page_action=action,
                          headless=False, proxy=PROXY_SERVER, locale="ja-JP")

    import json
    data = result_store.get('data', {})
    print("\n" + "="*60)
    print("0枚デバッグ結果")
    print("="*60)

    if 'error' in data:
        print(f"エラー: {data['error']}")
        return

    print(f"\n--- axis-tick 座標一覧 ---")
    for t in data.get('ticks', []):
        print(f"  svgY={t['svgY']}  localY={t['localY']}")

    print(f"\n--- Y軸ラベル候補 ---")
    for l in data.get('labelCandidates', []):
        print(f"  val={l['val']:>7}  labelTransY={l['labelTransY']}")

    print(f"\n--- 0罫線情報 ---")
    print(f"  zeroLabel:    {data.get('zeroLabel')}")
    print(f"  zeroTickSvgY: {data.get('zeroTickSvgY')}")

    print(f"\n--- グラフパス情報 ---")
    pi = data.get('pathInfo', {})
    print(f"  lastLocalY:          {pi.get('lastLocalY')}")
    print(f"  transY:              {pi.get('transY')}")
    print(f"  strokeWidth(attr):   {pi.get('strokeWidthAttr')}")
    print(f"  strokeWidth(comp):   {pi.get('strokeWidthComputed')}")
    print(f"  strokeWidth(used):   {pi.get('strokeWidth')}")
    print(f"  gSvgY(中心):         {pi.get('gSvgY_center')}")
    print(f"  gSvgY(下縁+sw/2):   {pi.get('gSvgY_bottom')}")

    print(f"\n--- 0ラインとのズレ ---")
    print(f"  中心基準: {data.get('diffCenter_from0line')}px")
    print(f"  下縁基準: {data.get('diffBottom_from0line')}px")
    print(f"  解釈: {data.get('interpretation')}")

if __name__ == "__main__":
    main()
