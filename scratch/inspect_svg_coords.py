"""
SVG座標系調査スクリプト
ogiya_pscube_slot_scraping.py と完全に同じ手法でナビゲートし、
Y軸ラベルとグラフパスのズレを解析する
"""
import sys
import os
import time
import json
import random
import re
import subprocess
import socket
import requests
import logging

# ogiya_pscube_slot_scraping.py と同じ設定を流用
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import Page
from scrapling.fetchers import StealthyFetcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 設定値 (ogiya_pscube_slot_scraping.py と同じ)
SITE1_URL = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/"
SITE1_SLOT_BTN = "body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(2) > a"
SITE1_MODEL_LIST = "a.btn-ki"
SITE1_MACHINE_LINK = "a.btn-dai"
PROXY_SERVER = "http://localhost:8118"
CONTAINER_NAME = "vpngate-proxy"

# ===== ogiya_pscube_slot_scraping.py から流用 =====
def is_proxy_working():
    try:
        resp = requests.get("http://httpbin.org/ip",
                           proxies={"http": PROXY_SERVER, "https": PROXY_SERVER}, timeout=10)
        if resp.status_code == 200:
            logger.info(f"プロキシ動作確認OK: {resp.json().get('origin')}")
            return True
    except:
        pass
    return False

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def human_like_delay(min_sec=1.0, max_sec=3.0):
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_scroll(page: Page, wait_time=3.0, max_scrolls=10):
    previous_height = page.evaluate("document.body.scrollHeight")
    unchanged_count = 0
    for i in range(max_scrolls):
        scroll_amount = random.uniform(0.5, 1.0)
        page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {scroll_amount})")
        human_like_delay(0.5, 1.0)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        human_like_delay(0.5, 1.0)
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            unchanged_count += 1
            if unchanged_count >= 2:
                break
        else:
            unchanged_count = 0
        previous_height = new_height

def handle_interstitial(page: Page):
    try:
        selectors = ["text='閉じる'", "text='OK'", "div.nc-modal-close", "a.btn-main", ".nc-dialog-close"]
        for sel in selectors:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                logger.info(f"割り込み要素 '{sel}' を閉じます")
                btn.click()
                human_like_delay(0.5, 1.0)
                break
    except:
        pass
# =====================================================

JS_INSPECT = r"""
(chartDateId) => {
    const container = document.getElementById(chartDateId);
    if (!container) return JSON.stringify({error: `コンテナ不存在: ${chartDateId}`});

    const svg = container.querySelector('svg');
    if (!svg) return JSON.stringify({error: 'SVG不存在', chartId: chartDateId});

    // Y軸ラベル取得
    const allTextEls = Array.from(svg.querySelectorAll('text'));
    const labelInfo = [];
    for (const textEl of allTextEls) {
        const tspan = textEl.querySelector('tspan');
        if (!tspan) continue;
        const text = tspan.textContent.trim();
        if (!/^-?[\d,]+$/.test(text) || text.includes(':')) continue;

        // text.yとtspan.y
        const textY_attr = parseFloat(textEl.getAttribute('y') || '0');
        const tspanY_attr = parseFloat(tspan.getAttribute('y') || '0');
        // text自身のtransform
        const textOwnT = textEl.getAttribute('transform') || '';
        const textOwnMatch = textOwnT.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
        const textOwnTY = textOwnMatch ? parseFloat(textOwnMatch[2]) : 0;
        // 祖先のtranslate合計（text含む）
        let totalTY = 0;
        let el = textEl;
        while (el && el !== svg) {
            const t = el.getAttribute('transform') || '';
            const m = t.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
            if (m) totalTY += parseFloat(m[2]);
            el = el.parentElement;
        }
        // 祖先のみ（text自身を除く）
        const ancestorOnlyTY = totalTY - textOwnTY;

        // 旧計算: textY_attr + textOwnTY (+ labelBaseTranslateY=ancestorOnlyTY)
        const svgY_old = textY_attr + textOwnTY + ancestorOnlyTY;
        // 新計算: textY_attr + tspanY_attr + totalTY
        const svgY_new = textY_attr + tspanY_attr + totalTY;
        // 実レンダリング位置
        const rect = textEl.getBoundingClientRect();
        const svgRect = svg.getBoundingClientRect();
        const svgY_rendered = rect.top - svgRect.top;

        labelInfo.push({
            val: text,
            textY: textY_attr, tspanY: tspanY_attr,
            textOwnTY, ancestorOnlyTY, totalTY,
            svgY_old, svgY_new, svgY_rendered
        });
    }

    // グラフパスの最終点
    const graphPath = svg.querySelector('g[class*="amcharts-graph-"] path') ||
                      svg.querySelector('g.amcharts-graph-smoothedLine path') ||
                      svg.querySelector('g.amcharts-graph-line path');
    if (!graphPath) return JSON.stringify({error: 'グラフPath不存在', labelInfo});

    const d = graphPath.getAttribute('d') || '';
    const dummyIdx = d.search(/M\s*0[,\s]+0\s*L/);
    const dataPath = dummyIdx > 0 ? d.substring(0, dummyIdx).trim() : d;

    const allCoords = [];
    const mlPat = /[ML]\s*(-?[\d.]+)[,\s]+(-?[\d.]+)/gi;
    const qPat = /Q\s*-?[\d.]+[,\s]+-?[\d.]+[,\s]+(-?[\d.]+)[,\s]+(-?[\d.]+)/gi;
    let mc;
    while ((mc = mlPat.exec(dataPath)) !== null) allCoords.push({x: parseFloat(mc[1]), y: parseFloat(mc[2])});
    while ((mc = qPat.exec(dataPath)) !== null) allCoords.push({x: parseFloat(mc[1]), y: parseFloat(mc[2])});
    allCoords.sort((a,b) => a.x - b.x);
    const last = allCoords[allCoords.length - 1];

    let pathTransY = 0;
    let pel = graphPath.parentElement;
    while (pel && pel !== svg) {
        const t = pel.getAttribute('transform') || '';
        const m = t.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
        if (m) pathTransY += parseFloat(m[2]);
        pel = pel.parentElement;
    }
    const graphSvgY = last ? last.y + pathTransY : null;

    return JSON.stringify({
        chartId: chartDateId,
        labelInfo,
        graphSvgY,
        pathLastCoord: last,
        pathTransY,
        svgSize: {w: svg.getAttribute('width'), h: svg.getAttribute('height')},
        dummyCut: dummyIdx > 0
    }, null, 2);
}
"""

result_data = {}

def action(page: Page):
    global result_data

    # ogiya_pscube_slot_scraping.py の site1_action と全く同じ流れ
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(SITE1_URL, wait_until="networkidle")
    human_like_delay(2.0, 3.0)

    logger.info(f"URL: {page.url}")
    page.screenshot(path="d:/PycharmProjects/pachislot/scratch/ss_01_top.png")

    # スロットデータボタンをクリック
    logger.info("スロットボタンクリック")
    page.click(SITE1_SLOT_BTN)
    page.wait_for_load_state("networkidle")
    human_like_delay(1.5, 3.0)
    page.screenshot(path="d:/PycharmProjects/pachislot/scratch/ss_02_slot_list.png")
    logger.info(f"スロット一覧URL: {page.url}")

    # スクロールして機種一覧を読み込む
    human_like_scroll(page)

    # 21.7スロ機種を探す
    model_btn_elements = page.query_selector_all(SITE1_MODEL_LIST)
    target_model = None
    target_name = ""
    for el in model_btn_elements:
        text = el.inner_text().strip()
        if "21.7スロ" in text:
            target_model = el
            target_name = text.split('\n')[0].strip()
            break

    if not target_model and model_btn_elements:
        target_model = model_btn_elements[0]
        target_name = model_btn_elements[0].inner_text().split('\n')[0].strip()

    if not target_model:
        logger.error("機種ボタンが見つかりません")
        # デバッグ: ページのリンク一覧
        links = page.query_selector_all("a")
        for lk in links[:10]:
            logger.info(f"  link: {lk.inner_text().strip()[:30]} class={lk.get_attribute('class')}")
        return

    logger.info(f"機種: {target_name}")
    target_model.click()
    page.wait_for_load_state("networkidle")
    human_like_delay(1.0, 2.0)
    page.screenshot(path="d:/PycharmProjects/pachislot/scratch/ss_03_model.png")

    human_like_scroll(page)

    # 最初の台番号をクリック
    machine_links = page.query_selector_all(SITE1_MACHINE_LINK)
    logger.info(f"台番号数: {len(machine_links)}")
    if not machine_links:
        logger.error("台番号が見つかりません")
        return

    mn = machine_links[0].inner_text().strip()
    logger.info(f"台番号 {mn} をクリック")
    machine_links[0].click()
    page.wait_for_load_state("networkidle")
    human_like_delay(2.0, 3.5)

    handle_interstitial(page)
    page.screenshot(path="d:/PycharmProjects/pachislot/scratch/ss_04_machine.png")
    logger.info(f"台番号ページURL: {page.url}")

    # 日付タブを確認してクリック (ogiya_pscube_slot_scraping.py の extract_pscube_graph_data_all_days と同じ)
    tab_buttons = page.query_selector_all("#YMD-ul > li")
    logger.info(f"タブ数: {len(tab_buttons)}")
    for tb in tab_buttons:
        ymd = tb.get_attribute("data-ymd")
        logger.info(f"  タブ: {ymd}")

    if not tab_buttons:
        logger.error("タブが見つかりません")
        return

    # 最初のタブ（本日分）をクリック
    first_tab = tab_buttons[0]
    tab_ymd = first_tab.get_attribute("data-ymd")
    chart_id = f"CHART-{tab_ymd}"

    logger.info(f"タブ {tab_ymd} クリック → チャートID: {chart_id}")
    first_tab.click()
    try:
        page.wait_for_selector(
            f"#{chart_id}[style*='display: block'], #{chart_id}:not([style*='display: none'])",
            timeout=8000
        )
        time.sleep(1.5)
    except Exception as e:
        logger.warning(f"チャート表示待機エラー: {e}")

    # SVG待機
    try:
        page.wait_for_selector(f"#{chart_id} svg", timeout=8000)
        logger.info("SVG確認！")
    except Exception as e:
        logger.warning(f"SVG待機タイムアウト: {e}")

    time.sleep(1.5)
    page.screenshot(path="d:/PycharmProjects/pachislot/scratch/ss_05_chart.png")

    # SVG調査を実行
    logger.info(f"SVG座標を解析中... チャートID={chart_id}")
    raw = page.evaluate(JS_INSPECT, chart_id)

    try:
        result_data = json.loads(raw)
    except Exception as e:
        logger.error(f"JSON解析エラー: {e}")
        logger.error(f"生データ: {raw[:2000]}")


def main():
    global result_data

    # プロキシ確認
    if is_port_in_use(8118) and is_proxy_working():
        logger.info("既存プロキシが動作中です。")
    else:
        logger.error("プロキシ(8118)が動作していません。先にDockerコンテナを起動してください。")
        return

    # ogiya_pscube_slot_scraping.py と全く同じ方法でフェッチ
    StealthyFetcher.fetch(
        SITE1_URL,
        page_action=action,
        headless=False,
        proxy=PROXY_SERVER,
        locale="ja-JP"
    )

    # 結果表示
    print("\n" + "="*60)
    print("SVG座標解析結果")
    print("="*60)

    if 'error' in result_data:
        print(f"エラー: {result_data['error']}")
        return

    print(f"チャートID: {result_data.get('chartId')}")
    print(f"SVGサイズ: {result_data.get('svgSize')}")
    print(f"dummyCut: {result_data.get('dummyCut')}")

    print(f"\n--- グラフ最終点 ---")
    print(f"  最終座標: {result_data.get('pathLastCoord')}")
    print(f"  pathTransY: {result_data.get('pathTransY')}")
    print(f"  graphSvgY: {result_data.get('graphSvgY')}")

    print(f"\n--- Y軸ラベル ---")
    print(f"  {'val':>8}  {'textY':>7}  {'tspanY':>7}  {'textOwnTY':>9}  {'ancestorTY':>10}  {'svgY_old':>8}  {'svgY_new':>8}  {'rendered':>8}")
    for lbl in result_data.get('labelInfo', []):
        print(f"  {lbl['val']:>8}  {lbl['textY']:>7.2f}  {lbl['tspanY']:>7.2f}  "
              f"{lbl['textOwnTY']:>9.2f}  {lbl['ancestorOnlyTY']:>10.2f}  "
              f"{lbl['svgY_old']:>8.2f}  {lbl['svgY_new']:>8.2f}  {lbl['svgY_rendered']:>8.2f}")

    # 補間結果を旧/新ロジックで比較
    labels_old = sorted([(l['svgY_old'], int(l['val'].replace(',',''))) for l in result_data.get('labelInfo', [])], key=lambda x: x[0])
    labels_new = sorted([(l['svgY_new'], int(l['val'].replace(',',''))) for l in result_data.get('labelInfo', [])], key=lambda x: x[0])
    graph_svgY = result_data.get('graphSvgY')

    if graph_svgY and len(labels_old) >= 2:
        def interpolate(labels, gY):
            p1 = p2 = None
            for i in range(len(labels)-1):
                if labels[i][0] <= gY <= labels[i+1][0]:
                    p1, p2 = labels[i], labels[i+1]
                    break
            if not p1:
                if gY < labels[0][0]:
                    p1, p2 = labels[0], labels[1]
                else:
                    p1, p2 = labels[-2], labels[-1]
            if p1[0] == p2[0]:
                return p1[1]
            ratio = (gY - p1[0]) / (p2[0] - p1[0])
            return round(p1[1] + ratio * (p2[1] - p1[1]))

        val_old = interpolate(labels_old, graph_svgY)
        val_new = interpolate(labels_new, graph_svgY)
        print(f"\n--- 補間結果比較 (graphSvgY={graph_svgY:.2f}) ---")
        print(f"  旧ロジック: {val_old} 枚")
        print(f"  新ロジック: {val_new} 枚")
        print(f"  差分: {val_new - val_old:+d} 枚")

if __name__ == "__main__":
    main()
