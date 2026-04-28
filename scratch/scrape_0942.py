"""
0942番台（沖ﾄﾞｷ!BLACK）の4/26データを取得して DB に保存するスクリプト
ogiya_pscube_slot_scraping.py と全く同じ手法・修正済みJSを使用
"""
import sys, os, time, random, re, sqlite3, json, logging, requests, socket
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import Page
from scrapling.fetchers import StealthyFetcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SITE1_URL    = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/"
SLOT_BTN     = "body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(2) > a"
PROXY_SERVER = "http://localhost:8118"
DB_FILE      = "d:/PycharmProjects/pachislot/slot_data.db"

TARGET_MACHINE = "0942"
TARGET_DATE    = "2026-04-26"   # 4/28から見て2日前

def human_like_delay(a=1.0, b=3.0): time.sleep(random.uniform(a, b))

def handle_interstitial(page):
    for sel in ["text='閉じる'", "text='OK'", "div.nc-modal-close", "a.btn-main"]:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible(): btn.click(); human_like_delay(0.5,1.0); break
        except: pass

# ogiya_pscube_slot_scraping.py の修正済み JS（完全コピー）
JS_EXTRACT = r'''
    (chartDateId) => {
        const container = document.getElementById(chartDateId);
        if (!container) return `解析不能 (コンテナ不存在: ${chartDateId})`;
        const svg = container.querySelector('svg');
        if (!svg) return '解析不能 (SVG不存在)';

        // 1a. Y軸ラベルの数値とtranslateYを収集
        const allTextEls = Array.from(svg.querySelectorAll('text'));
        const labelCandidates = [];
        for (const textEl of allTextEls) {
            const tspan = textEl.querySelector('tspan');
            if (!tspan) continue;
            const text = tspan.textContent.trim();
            const rawText = text.replace(/[^-0-9]/g, '');
            if (!rawText || isNaN(parseInt(rawText, 10))) continue;
            const val = parseInt(rawText, 10);
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
        if (labelCandidates.length < 2) return '解析不能 (ラベル不存在)';

        // 1b. Y罫線(amcharts-axis-tick)の正確なSVG Y座標を使ってラベルと対応付け
        const tickPaths = Array.from(svg.querySelectorAll('path.amcharts-axis-tick'));
        const labelPoints = [];

        for (const tick of tickPaths) {
            const d = tick.getAttribute('d') || '';
            const mMatch = d.match(/M\s*[\d.]+\s*,\s*([\d.]+)/);
            if (!mMatch) continue;
            const localY = parseFloat(mMatch[1]);

            let tickAncestorTY = 0;
            let tel = tick.parentElement;
            while (tel && tel !== svg) {
                const t = tel.getAttribute('transform') || '';
                const tm = t.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
                if (tm) tickAncestorTY += parseFloat(tm[2]);
                tel = tel.parentElement;
            }
            const tickSvgY = localY + tickAncestorTY;

            let closest = null, minDist = Infinity;
            for (const lc of labelCandidates) {
                const dist = Math.abs(tickSvgY - lc.labelTransY);
                if (dist < minDist) { minDist = dist; closest = lc; }
            }
            if (!closest || minDist > 30) continue;

            const existing = labelPoints.find(lp => lp.val === closest.val);
            if (existing) {
                if (minDist < existing._dist) { existing.svgY = tickSvgY; existing._dist = minDist; }
            } else {
                labelPoints.push({ svgY: tickSvgY, val: closest.val, _dist: minDist });
            }
        }

        if (labelPoints.length < 2) {
            for (const lc of labelCandidates) labelPoints.push({ svgY: lc.labelTransY, val: lc.val });
        }
        if (labelPoints.length < 2) return '解析不能 (ラベル点不足)';
        labelPoints.sort((a,b) => a.svgY - b.svgY);

        // 2. グラフパスの最終点
        const graphPath = svg.querySelector('g[class*="amcharts-graph-"] path') ||
                          svg.querySelector('g.amcharts-graph-smoothedLine path') ||
                          svg.querySelector('g.amcharts-graph-line path') ||
                          svg.querySelector('g:nth-child(8) > g > g:nth-child(3) > path');
        if (!graphPath) return '解析不能 (グラフPath不存在)';

        const d = graphPath.getAttribute('d');
        if (!d) return '解析不能 (Path d属性なし)';

        let dataPath = d;
        const dummyIdx = d.search(/M\s*0[,\s]+0\s*L/);
        if (dummyIdx > 0) dataPath = d.substring(0, dummyIdx).trim();

        const allCoords = [];
        const mlPat = /[ML]\s*(-?[\d.]+)[,\s]+(-?[\d.]+)/gi;
        const qPat  = /Q\s*-?[\d.]+[,\s]+-?[\d.]+[,\s]+(-?[\d.]+)[,\s]+(-?[\d.]+)/gi;
        let mc;
        while ((mc = mlPat.exec(dataPath)) !== null) allCoords.push({x: parseFloat(mc[1]), y: parseFloat(mc[2])});
        while ((mc = qPat.exec(dataPath))  !== null) allCoords.push({x: parseFloat(mc[1]), y: parseFloat(mc[2])});
        allCoords.sort((a,b) => a.x - b.x);
        const last = allCoords[allCoords.length - 1];
        if (!last) return '解析不能 (有効Path座標抽出失敗)';

        let transY = 0;
        let el2 = graphPath.parentElement;
        while (el2 && el2 !== svg) {
            const t = el2.getAttribute('transform') || '';
            const tm = t.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
            if (tm) transY += parseFloat(tm[2]);
            el2 = el2.parentElement;
        }
        const graphSvgY = last.y + transY;

        const labels = [...labelPoints].sort((a,b) => a.svgY - b.svgY);

        let p1 = null, p2 = null;
        for (let i = 0; i < labels.length - 1; i++) {
            if (graphSvgY >= labels[i].svgY && graphSvgY <= labels[i+1].svgY) {
                p1 = labels[i]; p2 = labels[i+1]; break;
            }
        }
        if (!p1) {
            if (graphSvgY < labels[0].svgY) { p1 = labels[0]; p2 = labels[1]; }
            else { p1 = labels[labels.length-2]; p2 = labels[labels.length-1]; }
        }
        if (p1.svgY === p2.svgY) return p1.val;

        const ratio = (graphSvgY - p1.svgY) / (p2.svgY - p1.svgY);
        const finalVal = Math.round(p1.val + ratio * (p2.val - p1.val));
        const labelStr = labels.map(l => `${l.val}@${l.svgY.toFixed(1)}`).join(' ');
        return `[${finalVal}] gSvgY:${graphSvgY.toFixed(2)} p1:${p1.val}(y:${p1.svgY.toFixed(1)}) p2:${p2.val}(y:${p2.svgY.toFixed(1)}) tickN:${tickPaths.length} labels:[${labelStr}]`;
    }
'''

# JS_EXTRACT: table data
JS_TABLE = r'''() => {
    const table = document.querySelector('#tblDAb');
    const data = {'本日': {}, '1日前': {}, '2日前': {}};
    if (!table) return data;
    const rows = Array.from(table.querySelectorAll('tr'));
    const labelMap = [
        {target:'BONUS', key:'BONUS', exact:true},
        {target:'BIG',   key:'BIG',   exact:true},
        {target:'REG',   key:'REG',   exact:true},
        {target:'累計',  key:'累計ゲーム', exact:false}
    ];
    for (const row of rows) {
        const cells = Array.from(row.querySelectorAll('td, th'));
        if (cells.length < 2) continue;
        const rowLabel = cells[0].innerText.trim();
        for (const {target, key, exact} of labelMap) {
            const matched = exact ? (rowLabel === target) : rowLabel.includes(target);
            if (matched && cells.length >= 4) {
                data['本日'][key]  = cells[1].innerText.replace(/,/g,'').trim();
                data['1日前'][key] = cells[2].innerText.replace(/,/g,'').trim();
                data['2日前'][key] = cells[3].innerText.replace(/,/g,'').trim();
                break;
            }
        }
    }
    return data;
}'''

result_store = {}

def action(page: Page):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(SITE1_URL, wait_until="networkidle")
    human_like_delay(2, 3)

    # スロットボタン
    page.click(SLOT_BTN)
    page.wait_for_load_state("networkidle")
    human_like_delay(1.5, 2.5)
    logger.info(f"スロット一覧: {page.url}")

    # スクロールして機種一覧を読み込む
    for _ in range(5):
        prev_h = page.evaluate("document.body.scrollHeight")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        human_like_delay(0.5, 1.0)
        if page.evaluate("document.body.scrollHeight") == prev_h: break

    # 沖ﾄﾞｷ!BLACK ボタンを探す（機種名に"沖"を含むもの）
    model_btns = page.query_selector_all("a.btn-ki")
    target_btn = None
    for btn in model_btns:
        text = btn.inner_text()
        if "沖" in text and "BLACK" in text:
            target_btn = btn
            logger.info(f"機種発見: {text.split(chr(10))[0].strip()}")
            break
    # 見つからなければ21.7スロの最初
    if not target_btn:
        for btn in model_btns:
            if "21.7スロ" in btn.inner_text():
                target_btn = btn
                logger.info(f"代替機種: {btn.inner_text().split(chr(10))[0].strip()}")
                break
    if not target_btn:
        logger.error("機種ボタンが見つかりません")
        return

    target_btn.click()
    page.wait_for_load_state("networkidle")
    human_like_delay(1, 2)

    # スクロール
    for _ in range(5):
        prev_h = page.evaluate("document.body.scrollHeight")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        human_like_delay(0.5, 1.0)
        if page.evaluate("document.body.scrollHeight") == prev_h: break

    # 0942番台を探す
    machine_links = page.query_selector_all("a.btn-dai")
    target_machine = None
    for lk in machine_links:
        if lk.inner_text().strip() == TARGET_MACHINE:
            target_machine = lk
            break
    if not target_machine:
        logger.error(f"台番号 {TARGET_MACHINE} が見つかりません（全{len(machine_links)}台）")
        return

    logger.info(f"台番号 {TARGET_MACHINE} クリック")
    target_machine.click()
    page.wait_for_load_state("networkidle")
    human_like_delay(2, 3.5)
    handle_interstitial(page)

    # テーブルデータ取得
    table_data = page.evaluate(JS_TABLE)
    logger.info(f"テーブル 2日前: {table_data.get('2日前')}")

    # タブ確認
    tabs = page.query_selector_all("#YMD-ul > li")
    logger.info(f"タブ数: {len(tabs)}")
    for t in tabs:
        logger.info(f"  タブ: {t.get_attribute('data-ymd')}")

    # 4/26 (2日前) のタブをクリック
    target_ymd = TARGET_DATE.replace("-", "")  # "20260426"
    chart_id = f"CHART-{target_ymd}"
    tab_sel = f"#YMD-ul > li[data-ymd='{target_ymd}']"
    tab = page.query_selector(tab_sel)
    if not tab:
        logger.error(f"タブ {target_ymd} が見つかりません")
        return

    logger.info(f"タブ {target_ymd} クリック")
    tab.click()
    try:
        page.wait_for_selector(
            f"#{chart_id}[style*='display: block'], #{chart_id}:not([style*='display: none'])",
            timeout=8000
        )
        time.sleep(1.5)
        page.wait_for_selector(f"#{chart_id} svg", timeout=8000)
        logger.info("SVG確認")
    except Exception as e:
        logger.warning(f"SVG待機エラー: {e}")
    time.sleep(1.5)

    # グラフから差枚取得（修正済みコード）
    raw = page.evaluate(JS_EXTRACT, chart_id)
    logger.info(f"Graph Debug: {raw}")

    sasamai = None
    if isinstance(raw, str) and "[" in raw:
        m = re.search(r'\[(-?\d+)\]', raw)
        if m: sasamai = int(m.group(1))
    elif isinstance(raw, (int, float)):
        sasamai = int(raw)

    logger.info(f"4/26 最終差枚 = {sasamai}")

    # テーブルデータ
    d2 = table_data.get('2日前', {})
    bonus = int(d2.get('BONUS','0').replace(',','') or 0)
    big   = int(d2.get('BIG','0').replace(',','') or 0)
    reg   = int(d2.get('REG','0').replace(',','') or 0)
    games = int(d2.get('累計ゲーム','0').replace(',','') or 0)

    games_int = games if isinstance(games, int) else 0
    sasamai_final = sasamai if isinstance(sasamai, int) else 0
    if games_int == 0:
        sasamai_final = 0

    result_store['record'] = (TARGET_DATE, '沖ﾄﾞｷ!BLACK', TARGET_MACHINE,
                               bonus, big, reg, games_int, sasamai_final)
    logger.info(f"保存予定: {result_store['record']}")


def main():
    # プロキシ確認
    try:
        r = requests.get("http://httpbin.org/ip",
                         proxies={"http": PROXY_SERVER, "https": PROXY_SERVER}, timeout=10)
        logger.info(f"プロキシOK: {r.json().get('origin')}")
    except Exception as e:
        logger.error(f"プロキシエラー: {e}")
        return

    StealthyFetcher.fetch(
        SITE1_URL,
        page_action=action,
        headless=False,
        proxy=PROXY_SERVER,
        locale="ja-JP"
    )

    if 'record' not in result_store:
        logger.error("データ取得失敗")
        return

    rec = result_store['record']
    print(f"\n=== 取得結果 ===")
    print(f"日付: {rec[0]}, 機種: {rec[1]}, 台番号: {rec[2]}")
    print(f"BONUS={rec[3]}, BIG={rec[4]}, REG={rec[5]}, 累計ゲーム={rec[6]}, 最終差枚={rec[7]}")

    # DB保存
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO slot_data (日付, 機種名, 台番号, BONUS, BIG, REG, 累計ゲーム, 最終差枚)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', rec)
    conn.commit()
    conn.close()
    print(f"DB保存完了")

if __name__ == "__main__":
    main()
