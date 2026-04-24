"""
SVGグラフ構造の詳細デバッグスクリプト
プロキシ経由でP's CUBEにアクセスし、スランプグラフのSVG構造を詳しく調査する
"""
import time
import json
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scrapling.fetchers import StealthyFetcher
from playwright.sync_api import Page

PROXY_SERVER = "http://localhost:8118"
SITE1_URL = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/"

def debug_action(page: Page):
    page.set_viewport_size({"width": 390, "height": 844})
    
    print("=== サイトへアクセス ===")
    page.goto(SITE1_URL, wait_until="networkidle")
    time.sleep(2)
    
    # スロットデータボタンをクリック
    slot_btn = "body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(2) > a"
    page.click(slot_btn)
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # 最初の機種をクリック
    first_model = page.query_selector("a.btn-ki")
    if first_model:
        first_model.click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)
    
    # 最初の台番号をクリック
    first_machine = page.query_selector("a.btn-dai")
    if first_machine:
        machine_num = first_machine.inner_text().strip()
        print(f"=== 台番号 {machine_num} を選択 ===")
        first_machine.click()
        page.wait_for_load_state("networkidle")
        time.sleep(3)
    
    # 各タブのデバッグ情報を取得
    for day_label, tab_idx in [("本日", 0), ("1日前", 1), ("2日前", 2)]:
        print(f"\n{'='*60}")
        print(f"=== {day_label} タブの調査 ===")
        
        # タブをクリック
        tab_buttons = page.query_selector_all("#YMD-ul > li")
        if tab_buttons and tab_idx < len(tab_buttons):
            tab_buttons[tab_idx].click()
            time.sleep(2)
        
        # スクリーンショット
        page.screenshot(path=f"scratch/debug_graph_{day_label}.png")
        print(f"スクリーンショット保存: scratch/debug_graph_{day_label}.png")
        
        # 詳細なSVG構造を取得
        result = page.evaluate(r'''
            (dayLabel) => {
                const debug = { dayLabel, svgs: [] };
                
                // アクティブなCHARTコンテナを探す
                const allCharts = document.querySelectorAll('[id^="CHART-"]');
                debug.allCharts = Array.from(allCharts).map(c => ({
                    id: c.id,
                    display: c.style.display,
                    height: c.offsetHeight
                }));
                
                const activeChart = Array.from(allCharts).find(c => 
                    c.style.display !== 'none' && c.offsetHeight > 0
                );
                debug.activeChartId = activeChart ? activeChart.id : 'NOT FOUND';
                
                if (!activeChart) return debug;
                
                const svg = activeChart.querySelector('svg');
                if (!svg) { debug.noSvg = true; return debug; }
                
                debug.svgInfo = {
                    width: svg.getAttribute('width'),
                    height: svg.getAttribute('height'),
                    viewBox: svg.getAttribute('viewBox')
                };
                
                // === Y軸ラベルの詳細調査 ===
                const texts = Array.from(svg.querySelectorAll('text'));
                debug.allTextElements = [];
                
                texts.forEach((t, idx) => {
                    const content = t.textContent.trim();
                    const tspan = t.querySelector('tspan');
                    const tspanContent = tspan ? tspan.textContent.trim() : '';
                    
                    // 全てのtext要素を記録（数値かどうかに関わらず）
                    const textInfo = {
                        idx,
                        content,
                        tspanContent,
                        isNumeric: /^-?[\d,]+$/.test(content),
                        ownX: t.getAttribute('x'),
                        ownY: t.getAttribute('y'),
                        ownTransform: t.getAttribute('transform'),
                        parentClass: t.parentElement ? t.parentElement.getAttribute('class') : ''
                    };
                    
                    // 親要素を遡ってtransformを集める
                    let el = t;
                    let totalTransY = 0;
                    const ancestorTransforms = [];
                    while (el && el !== svg) {
                        const tr = el.getAttribute('transform') || '';
                        const tm = tr.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
                        if (tm) {
                            const ty = parseFloat(tm[2]);
                            totalTransY += ty;
                            ancestorTransforms.push({
                                tag: el.tagName,
                                cls: el.getAttribute('class') || '',
                                transform: tr,
                                transY: ty
                            });
                        }
                        el = el.parentElement;
                    }
                    
                    textInfo.ancestorTransforms = ancestorTransforms;
                    textInfo.ownYNum = parseFloat(t.getAttribute('y') || '0');
                    const ownTMatch = (t.getAttribute('transform') || '').match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
                    textInfo.ownTransY = ownTMatch ? parseFloat(ownTMatch[2]) : 0;
                    textInfo.totalParentTransY = totalTransY;
                    textInfo.finalSvgY = textInfo.ownYNum + textInfo.ownTransY + totalTransY;
                    
                    debug.allTextElements.push(textInfo);
                });
                
                // === グラフPathの詳細調査 ===
                // amcharts-graphを持つg要素を全て列挙
                const graphGroups = Array.from(svg.querySelectorAll('g[class*="amcharts-graph"]'));
                debug.graphGroups = graphGroups.map(g => ({
                    class: g.getAttribute('class'),
                    childPaths: Array.from(g.querySelectorAll('path')).map(p => {
                        const d = p.getAttribute('d') || '';
                        
                        // M/Lコマンドで座標を全て抽出
                        const coordPattern = /[ML]\s*(-?[\d.]+)[,\s]+(-?[\d.]+)/gi;
                        const allCoords = [];
                        let m;
                        while ((m = coordPattern.exec(d)) !== null) {
                            allCoords.push([parseFloat(m[1]), parseFloat(m[2])]);
                        }
                        
                        // 親要素のtransformを集める
                        let el = p;
                        let pathTotalTransY = 0;
                        const pathAncestors = [];
                        while (el && el !== svg) {
                            const tr = el.getAttribute('transform') || '';
                            const tm = tr.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
                            if (tm) {
                                pathTotalTransY += parseFloat(tm[2]);
                                pathAncestors.push({
                                    tag: el.tagName,
                                    cls: el.getAttribute('class') || '',
                                    transform: tr
                                });
                            }
                            el = el.parentElement;
                        }
                        
                        return {
                            parentClass: p.parentElement ? p.parentElement.getAttribute('class') : '',
                            fill: p.getAttribute('fill'),
                            stroke: p.getAttribute('stroke'),
                            dLength: d.length,
                            dFirst200: d.substring(0, 200),
                            dLast200: d.substring(Math.max(0, d.length - 200)),
                            totalCoords: allCoords.length,
                            firstCoord: allCoords[0] || null,
                            lastCoord: allCoords[allCoords.length - 1] || null,
                            last5Coords: allCoords.slice(-5),
                            pathTotalTransY,
                            finalGraphSvgY: allCoords.length > 0 ? allCoords[allCoords.length - 1][1] + pathTotalTransY : null,
                            pathAncestors
                        };
                    })
                }));
                
                return debug;
            }
        ''', day_label)
        
        # 結果を整形して出力
        print(f"\n--- アクティブチャートID: {result.get('activeChartId')} ---")
        
        svg_info = result.get('svgInfo', {})
        print(f"SVGサイズ: width={svg_info.get('width')}, height={svg_info.get('height')}, viewBox={svg_info.get('viewBox')}")
        
        print(f"\n--- 数値ラベル一覧 ---")
        numeric_texts = [t for t in result.get('allTextElements', []) if t.get('isNumeric')]
        for t in numeric_texts:
            print(f"  値:{t['content']:>8} | ownY:{t['ownYNum']:>8.1f} | ownTransY:{t['ownTransY']:>8.1f} | parentTransY:{t['totalParentTransY']:>8.1f} | finalSvgY:{t['finalSvgY']:>8.1f}")
        
        print(f"\n--- グラフPath一覧 ---")
        for gg in result.get('graphGroups', []):
            print(f"\n  グループクラス: {gg['class']}")
            for pi, path in enumerate(gg.get('childPaths', [])):
                print(f"  Path[{pi}]: fill={path['fill']}, stroke={path['stroke']}, dLen={path['dLength']}, coords={path['totalCoords']}")
                print(f"    最初の座標: {path['firstCoord']}")
                print(f"    最後の座標: {path['lastCoord']}")
                print(f"    最後5座標: {path['last5Coords']}")
                print(f"    pathTotalTransY: {path['pathTotalTransY']}")
                print(f"    finalGraphSvgY: {path['finalGraphSvgY']}")
                print(f"    d最初200文字: {path['dFirst200']}")
                print(f"    d最後200文字: {path['dLast200']}")
                print(f"    祖先transforms: {path['pathAncestors']}")
        
        # グラフを再現する
        try:
            reconstruct_graph_from_svg(result, day_label)
        except Exception as e:
            print(f"グラフ再現エラー: {e}")
        
        json_path = f"scratch/debug_svg_{day_label}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nJSON保存: {json_path}")
    
    print("\n=== デバッグ完了 ===")


def reconstruct_graph_from_svg(result, day_label):
    """SVGデータからグラフを再現して出力する"""
    print(f"\n--- グラフ再現: {day_label} ---")
    
    svg_info = result.get('svgInfo', {})
    svg_height = float(svg_info.get('height') or 400)
    
    # Y軸ラベル取得（数値のみ）
    numeric_texts = [t for t in result.get('allTextElements', []) if t.get('isNumeric')]
    if not numeric_texts:
        print("  数値ラベルなし → スキップ")
        return
    
    # finalSvgYでソート（SVGは上が小さいY値）
    numeric_texts.sort(key=lambda x: x['finalSvgY'])
    
    print(f"  Y軸ラベル (SVY昇順):")
    for t in numeric_texts:
        val = int(t['content'].replace(',', '').replace('-', '')) * (-1 if '-' in t['content'] else 1)
        print(f"    svgY={t['finalSvgY']:.1f} → 枚数={val}")
    
    # グラフPathを探す（最も長いpathを使う）
    best_path = None
    best_path_group = None
    max_coords = 0
    for gg in result.get('graphGroups', []):
        for path in gg.get('childPaths', []):
            if path['totalCoords'] > max_coords:
                max_coords = path['totalCoords']
                best_path = path
                best_path_group = gg['class']
    
    if not best_path:
        print("  グラフPathなし → スキップ")
        return
    
    print(f"  使用Path: グループ={best_path_group}, coords={best_path['totalCoords']}, transY={best_path['pathTotalTransY']}")
    
    # SVGの座標をグラフ値に変換するための校正関数を作る
    # Y軸ラベルから: svgY → 実際の枚数値
    label_svgY = []
    label_vals = []
    for t in numeric_texts:
        content = t['content'].replace(',', '')
        try:
            val = int(content)
            label_svgY.append(t['finalSvgY'])
            label_vals.append(val)
        except:
            pass
    
    if len(label_svgY) < 2:
        print("  ラベル点不足 → スキップ")
        return
    
    # 線形回帰でSVGY→枚数の変換係数を求める
    # svgY が増えると枚数が減る（SVGは上が0）
    label_svgY = np.array(label_svgY)
    label_vals = np.array(label_vals)
    
    # 最小二乗法
    coeffs = np.polyfit(label_svgY, label_vals, 1)
    slope, intercept = coeffs
    print(f"  校正: 枚数 = {slope:.4f} * svgY + {intercept:.2f}")
    
    # last5coords で最終値を確認
    last5 = best_path.get('last5Coords', [])
    trans_y = best_path['pathTotalTransY']
    print(f"  最後5座標 (pathLocal + transY = svgY → 枚数):")
    for coord in last5:
        svg_y = coord[1] + trans_y
        val = slope * svg_y + intercept
        print(f"    pathY={coord[1]:.1f} + transY={trans_y:.1f} = svgY={svg_y:.1f} → {val:.0f}枚")
    
    # 最終点
    last_coord = best_path.get('lastCoord')
    if last_coord:
        final_svg_y = last_coord[1] + trans_y
        final_val = slope * final_svg_y + intercept
        print(f"  ★ 最終差枚推定値: {final_val:.0f}枚 (svgY={final_svg_y:.1f})")
    
    # matplotlibでグラフを描く（スクリーンショットとの比較用）
    # pathのd属性から全座標を取る
    d_full = None
    # JSONには dFirst200 と dLast200 しか保存していないのでここでは概算
    # 実際には別途フルdを取る必要があるが、デバッグ用として最後5点を使う
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 左: 校正プロット
    ax = axes[0]
    ax.scatter(label_svgY, label_vals, color='blue', s=100, zorder=5, label='Y軸ラベル')
    x_range = np.linspace(min(label_svgY)-20, max(label_svgY)+20, 100)
    ax.plot(x_range, slope * x_range + intercept, 'r--', label=f'校正線 slope={slope:.2f}')
    if last_coord:
        final_svg_y = last_coord[1] + trans_y
        final_val = slope * final_svg_y + intercept
        ax.axvline(x=final_svg_y, color='green', linestyle=':', label=f'最終svgY={final_svg_y:.1f}')
        ax.axhline(y=final_val, color='green', linestyle=':', label=f'最終差枚={final_val:.0f}')
        ax.scatter([final_svg_y], [final_val], color='green', s=200, zorder=6, marker='*')
    ax.set_xlabel('SVG Y座標')
    ax.set_ylabel('枚数')
    ax.set_title(f'{day_label}: Y軸校正')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.invert_xaxis()  # SVGはY軸が逆なので
    
    # 右: 最後5点のプロット
    ax2 = axes[1]
    if last5:
        xs = list(range(len(last5)))
        ys_svg = [c[1] + trans_y for c in last5]
        ys_val = [slope * sy + intercept for sy in ys_svg]
        ax2.plot(xs, ys_val, 'yo-', label='最後5点', markersize=10)
        ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
        for xi, (sy, v) in enumerate(zip(ys_svg, ys_val)):
            ax2.annotate(f'{v:.0f}枚\n(svgY={sy:.1f})', (xi, v), textcoords='offset points', xytext=(5, 5), fontsize=7)
    ax2.set_title(f'{day_label}: 最後5点の差枚値')
    ax2.set_ylabel('枚数')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.suptitle(f'{day_label} スランプグラフ再現分析', fontsize=14)
    plt.tight_layout()
    
    out_path = f"scratch/reconstructed_{day_label}.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print(f"  再現グラフ保存: {out_path}")


def main():
    print("=== SVGグラフ構造デバッグ開始 ===")
    print(f"プロキシ: {PROXY_SERVER}")
    
    def action_wrapper(page: Page):
        debug_action(page)
    
    StealthyFetcher.fetch(
        SITE1_URL,
        page_action=action_wrapper,
        headless=False,
        proxy=PROXY_SERVER,
        locale="ja-JP"
    )


if __name__ == "__main__":
    main()
