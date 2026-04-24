import asyncio
from playwright.async_api import async_playwright
import re
import matplotlib.pyplot as plt
import json
import os

SITE_URL = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/cgi-bin/nc-v06-001.php?cd_dai=0845"

async def main():
    async with async_playwright() as p:
        # プロキシ設定を追加
        browser = await p.chromium.launch(
            headless=False,
            proxy={"server": "http://localhost:8118"}
        )
        page = await browser.new_page(locale="ja-JP")
        print("ページにアクセスしています...")
        await page.goto(SITE_URL, wait_until="networkidle")
        await page.wait_for_timeout(3000)

        print("スクロールしてグラフを読み込ませます...")
        await page.evaluate("window.scrollBy(0, window.innerHeight);")
        await page.wait_for_timeout(2000)
        
        # 割り込みモーダルを再度チェック
        selectors = ["text='閉じる'", "text='OK'", "text='確認'", "div.nc-modal-close", "a.btn-main", ".nc-dialog-close"]
        for sel in selectors:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(1000)

        print("グラフのSVGデータを抽出しています...")
        
        # 本日タブを選択
        tab_btn = await page.query_selector("#YMD-ul > li:nth-child(1)")
        if tab_btn:
            await tab_btn.click()
            await page.wait_for_timeout(3000)
            
        # スクリーンショットを取得
        try:
            container = await page.query_selector('.amcharts-main-div')
            if not container:
                container = await page.query_selector('svg')
            if container:
                orig_ss_path = os.path.join(os.path.dirname(__file__), 'original_graph.png')
                await container.screenshot(path=orig_ss_path)
                print(f"元グラフのスクリーンショットを保存しました: {orig_ss_path}")
        except Exception as e:
            print(f"スクリーンショットの取得に失敗しました: {e}")

        script = """
        () => {
            const containers = document.querySelectorAll('div[id^="CHART-"]');
            let html = "";
            for (let i = 0; i < containers.length; i++) {
                if (window.getComputedStyle(containers[i]).display !== 'none') {
                    html = containers[i].outerHTML;
                    break;
                }
            }
            return {html: html};
        }
        """
        data = await page.evaluate(script)
        await browser.close()

        if not data.get("html"):
            print("Container HTML not found!")
            return

        with open(os.path.join(os.path.dirname(__file__), 'graph_dom.html'), 'w', encoding='utf-8') as f:
            f.write(data["html"])
        print("DOMを保存しました: graph_dom.html")

if __name__ == '__main__':
    asyncio.run(main())
