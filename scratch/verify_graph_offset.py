"""
グラフY軸が+30オフセットしているか検証するスクリプト。
P's Cubeサイトで既知データのある台のSVGを解析し、
ラベル値とグラフ線の位置関係を詳細ログで確認する。
プロキシなし・ヘッドレスなしで直接実行。
"""
import re
import sys
import datetime
import sqlite3
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright

# P's Cube の台詳細ページURL（直接指定）
# オーギヤ半田店のURLから特定台を直接開く
SITE_ROOT = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/"
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "slot_data.db")


def get_known_machines():
    """DBから累計ゲーム>1000かつ差枚が±1000以上の「確認しやすい台」を数件取得"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    # 直近の日付から、ゲーム数が多く差枚が明確な台を取得
    c.execute("""
        SELECT 日付, 機種名, 台番号, BONUS, BIG, REG, 累計ゲーム, 最終差枚
        FROM slot_data
        WHERE 日付 >= date('now', '-2 days')
          AND 累計ゲーム >= 2000
          AND abs(最終差枚) >= 500
        ORDER BY abs(最終差枚) DESC
        LIMIT 5
    """)
    rows = c.fetchall()
    conn.close()
    return rows


def extract_graph_debug(page, chart_date_id: str):
    """SVGグラフから最終差枚を抽出（詳細デバッグ付き）"""
    try:
        page.wait_for_selector(f"#{chart_date_id} svg", timeout=10000)
    except Exception as e:
        return f"SVGタイムアウト: {e}"

    result = page.evaluate(r'''
        (chartDateId) => {
            const container = document.getElementById(chartDateId);
            if (!container) return `解析不能 (コンテナ不存在: ${chartDateId})`;
            const svg = container.querySelector('svg');
            if (!svg) return '解析不能 (SVG不存在)';

            const allTextEls = Array.from(svg.querySelectorAll('text'));
            const tspans = [];
            for (const textEl of allTextEls) {
                const tspan = textEl.querySelector('tspan');
                if (!tspan) continue;
                const text = tspan.textContent.trim();
                if (/^-?[\d,]+$/.test(text) && !text.includes(':')) {
                    tspans.push(tspan);
                }
            }
            if (tspans.length === 0) return '解析不能 (ラベル不存在)';

            const labelPoints = [];
            for (const tspan of tspans) {
                const textEl = tspan.parentElement;
                const text = tspan.textContent.trim();
                const rawText = text.replace(/[^-0-9]/g, '');
                if (!rawText || isNaN(parseInt(rawText, 10))) continue;
                const val = parseInt(rawText, 10);
                if (Math.abs(val) > 100000) continue;
                if (text.includes(':')) continue;
                const transform = textEl.getAttribute('transform') || '';
                let textY = parseFloat(textEl.getAttribute('y') || '0');
                const tMatch = transform.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
                if (tMatch) textY += parseFloat(tMatch[2]);
                labelPoints.push({ svgY: textY, val: val });
            }
            if (labelPoints.length < 2) return '解析不能 (ラベル点不足)';
            labelPoints.sort((a, b) => a.svgY - b.svgY);

            const graphPath = svg.querySelector('g[class*="amcharts-graph-"] path') ||
                              svg.querySelector('g.amcharts-graph-smoothedLine path') ||
                              svg.querySelector('g.amcharts-graph-line path');
            if (!graphPath) return '解析不能 (グラフPath不存在)';
            const d = graphPath.getAttribute('d');
            if (!d) return '解析不能 (Path d属性なし)';

            let dataPath = d;
            const dummyIdx = d.search(/M\s*0[,\s]+0\s*L/);
            if (dummyIdx > 0) dataPath = d.substring(0, dummyIdx).trim();

            const allCoords = [];
            const mlPattern = /[ML]\s*(-?[\d.]+)[,\s]+(-?[\d.]+)/gi;
            const qPattern = /Q\s*-?[\d.]+[,\s]+-?[\d.]+[,\s]+(-?[\d.]+)[,\s]+(-?[\d.]+)/gi;
            let mc;
            while ((mc = mlPattern.exec(dataPath)) !== null)
                allCoords.push({ x: parseFloat(mc[1]), y: parseFloat(mc[2]) });
            while ((mc = qPattern.exec(dataPath)) !== null)
                allCoords.push({ x: parseFloat(mc[1]), y: parseFloat(mc[2]) });
            allCoords.sort((a, b) => a.x - b.x);
            const lastCoord = allCoords[allCoords.length - 1];
            if (!lastCoord) return '解析不能 (座標なし)';

            let translateY = 0;
            let el = graphPath.parentElement;
            while (el && el !== svg) {
                const t = el.getAttribute('transform') || '';
                const tm = t.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
                if (tm) translateY += parseFloat(tm[2]);
                el = el.parentElement;
            }
            const graphSvgY = lastCoord.y + translateY;

            const firstTextEl = tspans[0].parentElement;
            let labelBaseTranslateY = 0;
            let labelEl = firstTextEl.parentElement;
            while (labelEl && labelEl !== svg) {
                const t = labelEl.getAttribute('transform') || '';
                const tm = t.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
                if (tm) labelBaseTranslateY += parseFloat(tm[2]);
                labelEl = labelEl.parentElement;
            }

            const adjustedLabels = labelPoints.map(lp => ({
                svgY: lp.svgY + labelBaseTranslateY, val: lp.val
            }));
            adjustedLabels.sort((a, b) => a.svgY - b.svgY);

            let p1 = null, p2 = null;
            for (let i = 0; i < adjustedLabels.length - 1; i++) {
                if (graphSvgY >= adjustedLabels[i].svgY && graphSvgY <= adjustedLabels[i+1].svgY) {
                    p1 = adjustedLabels[i]; p2 = adjustedLabels[i+1]; break;
                }
            }
            if (!p1) {
                if (graphSvgY < adjustedLabels[0].svgY) {
                    p1 = adjustedLabels[0]; p2 = adjustedLabels[1];
                } else {
                    p1 = adjustedLabels[adjustedLabels.length - 2];
                    p2 = adjustedLabels[adjustedLabels.length - 1];
                }
            }

            const ratio = (graphSvgY - p1.svgY) / (p2.svgY - p1.svgY);
            const finalVal = Math.round(p1.val + ratio * (p2.val - p1.val));

            const labelStr = adjustedLabels.map(l => `${l.val}@y=${l.svgY.toFixed(1)}`).join(', ');
            return `RESULT=${finalVal} | graphSvgY=${graphSvgY.toFixed(2)} | lastCoord=(x:${lastCoord.x.toFixed(1)},y:${lastCoord.y.toFixed(1)}) | translateY=${translateY.toFixed(2)} | p1=${p1.val}(y=${p1.svgY.toFixed(1)}) p2=${p2.val}(y=${p2.svgY.toFixed(1)}) | ratio=${ratio.toFixed(4)} | labels=[${labelStr}]`;
        }
    ''', chart_date_id)
    return result


def run_verification():
    known = get_known_machines()
    if not known:
        print("DB内に検証用データが見つかりません。")
        return

    print("=== 検証対象（DB記録値） ===")
    for r in known:
        print(f"  {r[0]} {r[1]} 台{r[2]}: ゲーム={r[6]}, DB差枚={r[7]}")

    print("\nブラウザを起動して検証します...\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            locale="ja-JP",
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        )
        page = context.new_page()

        # トップ→スロットページへ
        print("P's Cubeにアクセス中...")
        page.goto(SITE_ROOT, wait_until="networkidle", timeout=30000)

        # スロットボタンクリック
        slot_btn = "body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(2) > a"
        try:
            page.click(slot_btn, timeout=10000)
            page.wait_for_load_state("networkidle")
        except:
            print("スロットボタンが見つかりません。URLを直接試みます。")

        for row in known:
            date_str, model_name, machine_num, bonus, big, reg, games, db_sasamai = row
            print(f"\n{'='*60}")
            print(f"台番号: {machine_num}  機種: {model_name}")
            print(f"DB記録値: ゲーム={games}, 差枚={db_sasamai}")

            try:
                # 機種ボタンをクリック
                model_btn = page.query_selector(f"a.btn-ki:has-text('{model_name.split()[0]}')")
                if model_btn:
                    model_btn.click()
                    page.wait_for_load_state("networkidle")
                else:
                    print(f"  機種ボタンが見つかりません: {model_name}")
                    continue

                # 台番号ボタンをクリック
                import time
                time.sleep(1)
                # スクロールして全台を読み込む
                for _ in range(5):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(0.5)

                num_btn = page.query_selector(f"a.btn-dai:has-text('{machine_num}')")
                if not num_btn:
                    print(f"  台番号ボタンが見つかりません: {machine_num}")
                    page.go_back(wait_until="networkidle")
                    continue

                num_btn.click()
                page.wait_for_load_state("networkidle")
                time.sleep(2)

                # 対象日付のチャートIDを計算
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                chart_id = f"CHART-{dt.strftime('%Y%m%d')}"
                tab_ymd = dt.strftime('%Y%m%d')

                # タブをクリック
                tab_sel = f"#YMD-ul > li[data-ymd='{tab_ymd}']"
                tab_btn = page.query_selector(tab_sel)
                if tab_btn:
                    tab_btn.click()
                    time.sleep(2)
                else:
                    print(f"  タブが見つかりません: {tab_ymd}")

                debug_result = extract_graph_debug(page, chart_id)
                print(f"  グラフ解析結果: {debug_result}")

                # RESULT= から抽出した値とDB値を比較
                m = re.search(r'RESULT=(-?\d+)', str(debug_result))
                if m:
                    graph_val = int(m.group(1))
                    diff = graph_val - db_sasamai
                    print(f"  グラフ値={graph_val}, DB値={db_sasamai}, 差={diff:+d}")
                    if diff == 30:
                        print(f"  ⚠ +30オフセット確認！グラフが常に30多い可能性")
                    elif diff == 0:
                        print(f"  ✓ 一致。オフセットなし")
                    else:
                        print(f"  ? 差={diff}（誤差の可能性あり）")

                page.go_back(wait_until="networkidle")
                time.sleep(1)
                page.go_back(wait_until="networkidle")
                time.sleep(1)

            except Exception as e:
                print(f"  エラー: {e}")
                try:
                    page.go_back(wait_until="networkidle")
                except:
                    pass

        browser.close()
        print("\n=== 検証完了 ===")


if __name__ == "__main__":
    run_verification()
