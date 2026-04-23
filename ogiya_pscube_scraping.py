import random
import time
from typing import Dict
import pandas as pd
import pscube_calculator as calc
import logging
import os
import subprocess
import re
import socket
import requests
import pickle
import queue
from playwright.sync_api import Page
from scrapling.fetchers import StealthyFetcher
# ==========================================
# ログ設定
# ==========================================
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put({"type": "log", "message": msg, "level": record.levelname})
        except Exception:
            self.handleError(record)

# ==========================================
# 設定値
# ==========================================
# --- 機種設定 ---
TARGET_MODELS = list(calc.BORDER_DICT.keys())

# --- Site 1 Settings ---
SITE1_URL = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/"
SITE1_PACHINKO_BTN = "body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(1) > a > img"
SITE1_MODEL_LIST = "ul#ulKI.nc-listview.nc-listview-kisyu div.nc-label"
SITE1_MACHINE_LINK = "a.btn-dai"

# --- プロキシ設定 (Dockerコンテナ用) ---
PROXY_SERVER = "http://localhost:8118"
CONTAINER_NAME = "vpngate-proxy"
DOCKER_CMD = [
    "docker", "run", "--rm", "--name", CONTAINER_NAME,
    "--cap-add=NET_ADMIN", "--device=/dev/net/tun",
    "--dns=1.1.1.1", "--dns=8.8.8.8", "--dns=9.9.9.9",
    "-p", "8118:8118",
    "tantantanuki/ja-vpngate-proxy"
]

# ==========================================
# ユーティリティ関数（BOT検知回避用）
# ==========================================

def ensure_docker_desktop_running():
    """Docker Desktopが起動しているか確認し、起動していなければ起動する"""
    logger.info("Docker Desktopの起動状態を確認しています...")
    try:
        # docker versionが成功するか確認
        res = subprocess.run(["docker", "version"], capture_output=True, text=True)
        if res.returncode == 0:
            logger.info("Docker Desktopは既に起動しています。")
            return True
    except:
        pass

    logger.info("Docker Desktopを起動します...")
    # Docker Desktopのパス (標準的な場所)
    docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if os.path.exists(docker_path):
        # startコマンドを使って非同期で起動
        subprocess.Popen([docker_path], shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        logger.error(f"Docker Desktopが見つかりません: {docker_path}")
        return False

    # 起動を待機 (最大120秒)
    for i in range(24):
        time.sleep(5)
        logger.info(f"Dockerの起動を待機中... ({ (i+1)*5 }秒経過)")
        res = subprocess.run(["docker", "version"], capture_output=True, text=True)
        if res.returncode == 0:
            # 念のためもう少し待つ
            time.sleep(5)
            logger.info("Docker Desktopが正常に起動しました。")
            return True
            
    logger.error("Docker Desktopの起動タイムアウトです。")
    return False

def stop_docker_desktop():
    """Docker Desktop関連のプロセスを終了する"""
    logger.info("Docker Desktopを終了しています...")
    # 主なプロセスを順番にキル
    processes = ["Docker Desktop.exe", "com.docker.backend.exe", "com.docker.proxy.exe"]
    for proc in processes:
        subprocess.run(f'taskkill /F /IM "{proc}" /T', shell=True, capture_output=True)

def kill_process_on_port(port: int):
    """指定されたポートを使用しているプロセスを強制終了する(Windows用)"""
    try:
        # ポートを使用しているプロセスのPIDを取得
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            # 行をパースしてPID（最後の列）を取得
            for line in result.stdout.strip().split('\n'):
                if "LISTENING" in line and f":{port}" in line:
                    parts = line.split()
                    pid = parts[-1]
                    logger.info(f"ポート {port} を使用中のプロセス (PID: {pid}) を終了します...")
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                    time.sleep(1) # 終了を待機
    except Exception as e:
        logger.error(f"ポート {port} の解放中にエラー: {e}")

def setup_docker_proxy():
    """Dockerコンテナを起動し、ログと接続を確認する"""
    max_retries = 3
    for attempt in range(max_retries):
        logger.info(f"Dockerコンテナ起動試行中 ({attempt + 1}/{max_retries})...")
        
        # ポート 8118 を占有しているプロセスがあれば終了させる
        kill_process_on_port(8118)
        
        # 既存のコンテナがあれば停止
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
        
        # コンテナを起動 (-itはsubprocessでは-iのみ、または無しで実行)
        process = subprocess.Popen(
            ["docker", "run", "--rm", "--name", CONTAINER_NAME,
             "--cap-add=NET_ADMIN", "--device=/dev/net/tun",
             "--dns=1.1.1.1", "--dns=8.8.8.8", "--dns=9.9.9.9",
             "-p", "8118:8118",
             "tantantanuki/ja-vpngate-proxy"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        success = False
        pattern_found = False
        last_log_time = time.time()
        
        try:
            # ログ監視ループ
            while True:
                # 非ブロッキングで1行読み込むためにtimeout付きで待機したいが、
                # Pythonのreadlineはブロッキングなので、selectや低レベルな仕組みが必要。
                # ここでは簡易的に、一定時間待ってから読み込むか、別のスレッドで監視する。
                # または、単純に一定時間内にログが出なければ成功とするロジックにする。
                
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        logger.error("Dockerプロセスが終了しました。")
                        break
                    continue
                
                line = line.strip()
                if line:
                    logger.debug(f"Docker: {line}")
                    last_log_time = time.time()
                
                # パターン確認
                match = re.search(r"before=([\d\.]+) after=([\d\.]+)", line)
                if not pattern_found and match:
                    before_ip = match.group(1)
                    after_ip = match.group(2)
                    if before_ip == after_ip:
                        logger.error(f"IPが変わっていません: before={before_ip} after={after_ip}")
                        break
                    
                    logger.info("ログに接続成功パターンが見つかりました。静止を待ちます...")
                    pattern_found = True
                    # パターンが見つかったら、そこから5秒間ログが止まるのを待つ
                    start_wait = time.time()
                    while time.time() - start_wait < 10: # 最大10秒待機
                        # ここでも非ブロッキング読み込みが必要。
                        # Windowsでも動くように、短いスリープとpollを組み合わせる。
                        time.sleep(1)
                        if time.time() - last_log_time >= 5:
                            logger.info("5秒間のログ静止を確認しました。")
                            success = True
                            break
                    if success:
                        break

                # タイムアウト (3分)
                if time.time() - last_log_time > 180:
                    logger.error("コンテナ起動タイムアウト")
                    break
            
            if success:
                # 導通確認
                logger.info("localhost:8118 でプロキシの導通確認を行います...")
                try:
                    # 実際にプロキシ経由でアクセス
                    resp = requests.get("http://httpbin.org/ip", 
                                        proxies={"http": PROXY_SERVER, "https": PROXY_SERVER}, 
                                        timeout=10)
                    if resp.status_code == 200:
                        logger.info(f"プロキシ接続成功: {resp.json().get('origin')}")
                        return True
                    else:
                        logger.warning(f"導通確認失敗 (ステータスコード: {resp.status_code})")
                except Exception as e:
                    logger.warning(f"導通確認中にエラー: {e}")
            
        except Exception as e:
            logger.error(f"監視中にエラーが発生しました: {e}")
        
        # 失敗した場合はクリーンアップしてリトライ
        logger.warning("起動に失敗しました。再起動します。")
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
        process.terminate()
        time.sleep(5)
        
    logger.error("最大試行回数を超えました。")
    return False

def human_like_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """人間らしいランダム待機（一様分布）"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

def human_like_scroll(page: Page, wait_time: float = 3.0, max_scrolls: int = 30):
    """ページ下部までスクロール（人間らしさを加味したSPA対策）"""
    logger.debug("スクロールを開始します...")
    previous_height = page.evaluate("document.body.scrollHeight")
    unchanged_count = 0
    
    for i in range(max_scrolls):
        # 画面の半分や一部だけランダムにスクロールする
        scroll_amount = random.uniform(0.5, 1.0)
        page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {scroll_amount})")
        human_like_delay(0.5, 1.5)
        
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        human_like_delay(0.5, 1.5)
        
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            unchanged_count += 1
            if unchanged_count >= 2:
                logger.debug("新規要素の読み込みが完了しました。")
                break
        else:
            unchanged_count = 0
        previous_height = new_height
    logger.debug("スクロール終了。")

def extract_pscube_graph_data(page: Page) -> float | str:
    """Site 1 (P's Cube) の amCharts グラフから最終差玉を取得する"""
    try:
        # SVGのロードを待機
        page.wait_for_selector(".amcharts-graph-stroke", timeout=5000)
        
        result = page.evaluate('''() => {
            // 以前のデバッグ用マーカーを削除
            const oldMarkers = document.querySelectorAll('.debug-marker');
            oldMarkers.forEach(m => m.remove());

            const labels = Array.from(document.querySelectorAll('.amcharts-value-axis .amcharts-axis-label'));
            const path = document.querySelector('.amcharts-graph-stroke');
            if (!labels.length || !path) return "解析不能 (要素不足)";

            // ラベルの座標と数値を取得
            const points = labels.map(l => {
                const rect = l.getBoundingClientRect();
                return {
                    y: rect.top + rect.height / 2,
                    val: parseInt(l.textContent.replace(/[^-0-9]/g, ''), 10)
                };
            }).filter(p => !isNaN(p.val));

            if (points.length < 2) return "解析不能 (ラベル不足)";
            points.sort((a, b) => a.y - b.y);

            // グラフの最終地点のスクリーン座標を取得
            const totalLength = path.getTotalLength();
            const lastPointLocal = path.getPointAtLength(totalLength);
            const matrix = path.getScreenCTM();
            const lastPointScreen = lastPointLocal.matrixTransform(matrix);
            const lastY = lastPointScreen.y;

            // 線形補間
            let p1, p2;
            for (let i = 0; i < points.length - 1; i++) {
                if (lastY >= points[i].y && lastY <= points[i+1].y) {
                    p1 = points[i];
                    p2 = points[i+1];
                    break;
                }
            }
            
            if (!p1) {
                if (lastY < points[0].y) { p1 = points[0]; p2 = points[1]; }
                else { p1 = points[points.length - 2]; p2 = points[points.length - 1]; }
            }

            const value = p1.val + (lastY - p1.y) * (p2.val - p1.val) / (p2.y - p1.y);

            // デバッグ視覚化：計算地点に赤いドット、使用ラベルに黄色の枠
            const marker = document.createElement('div');
            marker.className = 'debug-marker';
            Object.assign(marker.style, {
                position: 'fixed', left: (lastPointScreen.x - 5) + 'px', top: (lastPointScreen.y - 5) + 'px',
                width: '10px', height: '10px', backgroundColor: 'red', borderRadius: '50%',
                zIndex: '10000', pointerEvents: 'none', border: '1px solid white'
            });
            document.body.appendChild(marker);
            
            labels.forEach(l => l.style.outline = '2px solid yellow');

            return Math.round(value);
        }''')
        return result
    except Exception as e:
        return f"解析エラー: {e}"

# ==========================================
# スクレイピング ロジック (scrapling StealthyFetcher を利用)
# ==========================================

def site1_action(page: Page, target_models: list = None, specific_machines: list = None, result_queue: queue.Queue = None) -> dict:
    """Site1 の具体的なページ操作ロジック"""
    data = {}
    
    if target_models is None:
        target_models = TARGET_MODELS
    try:
        # ユーザー要望: Site1はスマホ向けなので縦長にする
        page.set_viewport_size({"width": 390, "height": 844})
        
        # ページはStealthyFetcherにより既に開かれているが、念の為アクセス
        page.goto(SITE1_URL, wait_until="networkidle")
        human_like_delay(2.0, 3.0)

        logger.debug("Site 1: パチンコデータボタンをクリック")
        page.click(SITE1_PACHINKO_BTN)
        page.wait_for_load_state("networkidle")
        human_like_delay(1.5, 3.0)

        logger.debug("Site 1: 機種一覧の読み込みのためスクロール")
        human_like_scroll(page)

        logger.debug("Site 1: 機種名の特定処理")
        model_elements = page.query_selector_all(SITE1_MODEL_LIST)
        
        matched_models = []
        for el in model_elements:
            text = el.inner_text()
            if text.strip() in target_models:
                matched_models.append(text.strip())
        
        logger.info(f"Site 1: 対象機種が {len(matched_models)} 件見つかりました。")

        for model_name in matched_models:
            logger.debug(f"Site 1: 対象機種 '{model_name}' を探してクリックします")
            
            model_btn = page.query_selector(f"//div[contains(@class, 'nc-label') and text()='{model_name}']")
            if not model_btn:
                logger.warning(f"Site 1: 機種 '{model_name}' のボタンが見つかりません。")
                continue
            
            model_btn.click()
            page.wait_for_load_state("networkidle")
            human_like_delay(1.0, 2.0)
            
            human_like_scroll(page)
            
            machine_links = page.query_selector_all(SITE1_MACHINE_LINK)
            machine_numbers = []
            for m_link in machine_links:
                num_text = m_link.inner_text().strip()
                if specific_machines:
                    if num_text in specific_machines:
                        machine_numbers.append(num_text)
                else:
                    machine_numbers.append(num_text)
            
            logger.info(f"Site 1: '{model_name}' で {len(machine_numbers)} 件の台番号を取得。")

            for idx, machine_num in enumerate(machine_numbers):
                logger.debug(f"Site 1: [{idx+1}/{len(machine_numbers)}] 台番号 {machine_num} のデータ取得を開始")
                try:
                    # 台番号リンクを特定してクリック（btn-dai クラスを持つ要素を指定）
                    num_btn = page.query_selector(f"a.btn-dai:has-text('{machine_num}')")
                    if num_btn:
                        num_btn.click()
                        page.wait_for_load_state("networkidle")
                        human_like_delay(2.0, 3.5) # ロードを待機

                        # --- 詳細データの取得 ---
                        
                        # 1. 累計スタートと最終スタートの取得
                        total_start_elem = page.query_selector('#tblDAb > tr:nth-child(7) > td:nth-child(2)')
                        final_start_elem = page.query_selector('#tblDAb > tr:nth-child(8) > td:nth-child(2)')
                        
                        total_start_val = 0
                        final_start_val = 0
                        if total_start_elem:
                            text = (total_start_elem.inner_text()).strip().replace(',', '')
                            total_start_val = int(text) if text.isdigit() else 0
                        if final_start_elem:
                            text = (final_start_elem.inner_text()).strip().replace(',', '')
                            final_start_val = int(text) if text.isdigit() else 0

                        # 累計スタートが0ならスキップ
                        if total_start_val == 0:
                            logger.info(f"Site 1: 台番号 {machine_num} は累計スタート0のためスキップします。")
                            page.go_back(wait_until="networkidle")
                            continue

                        # 2. グラフから最終差玉を取得
                        final_diff = extract_pscube_graph_data(page)
                        
                        # 3. 大当たり履歴のスクレイピング (詳細テーブル構造に対応)
                        start_list = []
                        shubetu_list = []
                        dedama_list = []
                        
                        # 履歴テーブル (IDが -table で終わる要素) を特定
                        history_table = page.query_selector('table[id$="-table"]')
                        if not history_table:
                            history_table = page.query_selector('div[id$="-table"]')

                        if history_table:
                            # 各当たりのカラム（クラス名に "toku-" を含む td または div）を取得
                            hit_elements = history_table.query_selector_all('td[class*="toku-"], div[class*="toku-"]')
                            
                            for hit in hit_elements:
                                # 12番目: スタート, 13番目: 種別, 14番目: 出玉
                                s_elem = hit.query_selector('div:nth-child(12) > div')
                                t_elem = hit.query_selector('div:nth-child(13) div span')
                                if not t_elem: t_elem = hit.query_selector('div:nth-child(13) > div')
                                d_elem = hit.query_selector('div:nth-child(14) > div')
                                
                                if s_elem and t_elem:
                                    s_text = s_elem.inner_text().strip()
                                    t_text = t_elem.inner_text().strip()
                                    d_text = d_elem.inner_text().strip() if d_elem else "0"
                                    
                                    if s_text and s_text != "-":
                                        # 種別変換 (初当たり / 継続)
                                        if "初当たり" in t_text or "初当り" in t_text: t_text = "大当"
                                        elif "継続" in t_text or "確変" in t_text: t_text = "確変"
                                        
                                        start_list.append(s_text)
                                        shubetu_list.append(t_text)
                                        dedama_list.append(d_text)

                        # リストを時系列順（古い順）に反転
                        start_list.reverse()
                        shubetu_list.reverse()
                        dedama_list.reverse()

                        # 4. 期待値計算の実行
                        calc_results = calc.calculate_expected_value(
                            start_list, dedama_list, shubetu_list, final_start_val, model_name, final_diff if isinstance(final_diff, (int, float)) else 0
                        )
                        med_res = calc_results.get("med", (0, 0, 0))
                        kaitensuu, saishusadama, kitaichi = med_res

                        data[machine_num] = {
                            "機種名": model_name,
                            "累計スタート": total_start_val,
                            "最終スタート": final_start_val,
                            "最終差玉": saishusadama,
                            "回転率(med)": kaitensuu,
                            "ボーダー差(med)": kitaichi,
                            "回転率(min)": calc_results["min"][0],
                            "ボーダー差(min)": calc_results["min"][2],
                            "回転率(max)": calc_results["max"][0],
                            "ボーダー差(max)": calc_results["max"][2],
                            "履歴_スタート": start_list,
                            "履歴_種別": shubetu_list,
                            "履歴_出玉": dedama_list
                        }
                        print(data[machine_num])
                        
                        logger.info(f"Site 1: 台番号 {machine_num} 取得完了 - 回転率(med): {kaitensuu}, ボーダー差(med): {kitaichi}")
                        
                        # 毎回pickleに保存
                        try:
                            with open("scraping_data.pkl", "wb") as f:
                                pickle.dump(data, f)
                        except Exception as e:
                            logger.error(f"pickle保存エラー: {e}")
                            
                        # キューに進捗を送信
                        if result_queue:
                            result_queue.put({"type": "progress", "data": data.copy()})
                        
                        page.go_back(wait_until="networkidle")
                        human_like_delay(1.0, 2.0)
                        
                        
                except Exception as e:
                    logger.error(f"Site 1: 台番号 {machine_num} 処理中にエラー: {e}")
                    page.screenshot(path=f"error_site1_machine_{machine_num}.png")

            page.go_back(wait_until="networkidle")
            human_like_delay(1.0, 2.0)

    except Exception as e:
        logger.error(f"Site 1: 全体処理でエラーが発生しました: {e}")
        page.screenshot(path="error_site1_main.png")
    
    return data

def scrape_site1_scrapling(target_models: list = None, specific_machines: list = None, result_queue: queue.Queue = None) -> Dict[str, dict]:
    """scraplingのStealthyFetcherを用いてSite1をスクレイピング"""
    logger.info("Site 1: scrapling (StealthyFetcher) を使用して実行します")
    
    # scraped_data の初期化
    scraped_data = {}
    
    def action_wrapper(page: Page):
        # 実際の操作ロジックを呼び出し、取得データをscraped_dataに格納
        result = site1_action(page, target_models, specific_machines, result_queue)
        scraped_data.update(result)

    # scraplingのfetchを呼び出す（headlessとproxyを指定）
    StealthyFetcher.fetch(
        SITE1_URL, 
        page_action=action_wrapper, 
        headless=False, 
        proxy=PROXY_SERVER,
        locale="ja-JP"
    )
    logger.info("Site 1: 処理終了")
    return scraped_data

def main():
    logger.info("=== スクレイピング開始 ===")
    
    # SITE1のみ実行
    results = scrape_site1_scrapling()
    
    # データの保存
    if results:
        df = pd.DataFrame.from_dict(results, orient='index')
        df.index.name = "台番号"
        df.to_csv("scraping_results.csv", encoding='utf-8-sig')
        logger.info(f"合計 {len(results)} 台のデータを scraping_results.csv に保存しました。")
    else:
        logger.warning("取得データがありませんでした。")
    
    logger.info("=== 全処理終了 ===")

if __name__ == "__main__":
    try:
        if ensure_docker_desktop_running():
            if setup_docker_proxy():
                main()
            else:
                logger.error("プロキシの準備ができなかったため、処理を中止します。")
        else:
            logger.error("Docker Desktopが起動できなかったため、処理を中止します。")
    finally:
        # 終了時にコンテナを停止
        logger.info("クリーンアップ処理を開始します...")
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
        # Docker Desktopを終了
        stop_docker_desktop()
