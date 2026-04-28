"""
ページ状態確認スクリプト - スクリーンショット保存
"""
import time
from playwright.sync_api import sync_playwright

MACHINE_URL = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/cgi-bin/nc-v06-001.php?cd_dai=0942"
TOP_URL = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        
        # まずトップページ
        print("トップページアクセス...", flush=True)
        page.goto(TOP_URL, wait_until="networkidle", timeout=30000)
        time.sleep(2)
        page.screenshot(path="d:/PycharmProjects/pachislot/scratch/ss_top.png")
        print(f"URL: {page.url}", flush=True)
        print(f"Title: {page.title()}", flush=True)
        
        # スロットボタンをクリック
        try:
            slot_btn = "body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(2) > a"
            page.click(slot_btn, timeout=5000)
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            page.screenshot(path="d:/PycharmProjects/pachislot/scratch/ss_slot_list.png")
            print(f"スロット一覧URL: {page.url}", flush=True)
        except Exception as e:
            print(f"スロットボタンエラー: {e}", flush=True)
            # 代替: スロットリンクを探す
            links = page.query_selector_all("a")
            for lk in links[:20]:
                txt = lk.inner_text().strip()
                href = lk.get_attribute("href") or ""
                if txt:
                    print(f"  link: {txt[:30]} -> {href[:60]}", flush=True)
        
        # 機種一覧から最初の21.7スロを探す
        model_btns = page.query_selector_all("a.btn-ki")
        print(f"機種ボタン数: {len(model_btns)}", flush=True)
        target_btn = None
        for btn in model_btns:
            text = btn.inner_text()
            if "21.7スロ" in text:
                target_btn = btn
                print(f"機種発見: {text.split(chr(10))[0].strip()}", flush=True)
                break
        
        if not target_btn and model_btns:
            target_btn = model_btns[0]
            print(f"最初の機種を使用: {model_btns[0].inner_text().split(chr(10))[0].strip()}", flush=True)
        
        if target_btn:
            target_btn.click()
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            page.screenshot(path="d:/PycharmProjects/pachislot/scratch/ss_model.png")
            
            # 最初の台番号
            machine_links = page.query_selector_all("a.btn-dai")
            print(f"台番号数: {len(machine_links)}", flush=True)
            if machine_links:
                mn = machine_links[0].inner_text().strip()
                print(f"台番号 {mn} クリック", flush=True)
                machine_links[0].click()
                page.wait_for_load_state("networkidle")
                time.sleep(3)
                
                # スクロール
                page.evaluate("window.scrollTo(0, 300)")
                time.sleep(2)
                
                page.screenshot(path="d:/PycharmProjects/pachislot/scratch/ss_machine.png")
                print(f"台番号ページURL: {page.url}", flush=True)
                print(f"台番号ページTitle: {page.title()}", flush=True)
                
                # チャートとSVGの状況
                chart_count = page.evaluate("document.querySelectorAll('[id^=\"CHART-\"]').length")
                svg_count = page.evaluate("document.querySelectorAll('svg').length")
                print(f"CHART要素数: {chart_count}, SVG数: {svg_count}", flush=True)
        
        browser.close()
        print("完了", flush=True)

if __name__ == "__main__":
    main()
