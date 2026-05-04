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
import threading
from playwright.sync_api import Page
from scrapling.fetchers import StealthyFetcher
# ==========================================
# ログ設定
# ==========================================
# ログ設定は main.py で一括管理
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
TARGET_MODELS = list({**calc.OGIYA_BORDER_DICT, **calc.SUMIYOSHI_KITA_BORDER_DICT}.keys())

# --- Site 1 Settings ---
SITE1_URL = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c733211/"
SITE1_PACHINKO_BTN = "a[href*='cd_ps=1']"

# 住吉北店の機種名表記ゆれマッピング（住吉北店の表記 -> BORDER_DICT の表記）
SUMIYOSHI_KITA_NAME_MAP = {
    # 住吉北店表記: BORDER_DICT表記
    "P大海物語5 MTE2": "P大海物語5",
    "Pまどか☆ﾏｷﾞｶ3 LM3": "P 魔法少女まどか☆マギカ3",
    "e東京ﾘﾍﾞﾝｼﾞｬｰｽﾞGFEC": "e 東京リベンジャーズ",
}
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
        res = subprocess.run(["docker", "version"], capture_output=True, text=True)
        if res.returncode == 0:
            logger.info("Docker Desktopは既に起動しています。")
            return True
    except:
        pass

    logger.info("Docker Desktopを起動します...")
    docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if os.path.exists(docker_path):
        subprocess.Popen([docker_path], shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        logger.error(f"Docker Desktopが見つかりません: {docker_path}")
        return False

    # 起動を待機 (最大30秒)
    for i in range(6):
        time.sleep(5)
        logger.info(f"Dockerの起動を待機中... ({ (i+1)*5 }秒経過)")
        res = subprocess.run(["docker", "version"], capture_output=True, text=True)
        if res.returncode == 0:
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
            pids = set()
            for line in result.stdout.strip().split('\n'):
                if "LISTENING" in line and f":{port}" in line:
                    parts = line.split()
                    pids.add(parts[-1])
            
            for pid in pids:
                logger.info(f"ポート {port} を使用中のプロセス (PID: {pid}) を終了します...")
                subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                time.sleep(1) # 終了を待機

    except Exception as e:
        logger.error(f"ポート {port} の解放中にエラー: {e}")

def is_proxy_working() -> bool:
    """Check whether the local HTTP proxy is usable."""
    try:
        resp = requests.get(
            "http://httpbin.org/ip",
            proxies={"http": PROXY_SERVER, "https": PROXY_SERVER},
            timeout=10
        )
        if resp.status_code == 200:
            logger.info(f"Proxy is working: {resp.json().get('origin')}")
            return True
    except Exception as e:
        logger.debug(f"Proxy check failed: {e}")
    return False

def is_port_in_use(port: int) -> bool:
    """Return True when localhost:port accepts TCP connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0

def is_port_owner_docker(port: int) -> bool:
    """Return True when Docker publishes the specified host port."""
    try:
        res = subprocess.run(
            ["docker", "ps", "--filter", f"publish={port}", "--format", "{{.ID}}"],
            capture_output=True,
            text=True,
            timeout=15
        )
        return bool(res.stdout.strip())
    except Exception as e:
        logger.debug(f"Failed to inspect Docker port owner: {e}")
        return False

def restart_proxy() -> bool:
    """
    Dockerコンテナを停止→Docker Desktop再起動→コンテナ再起動を行い、
    プロキシIPを切り替える。
    """
    logger.info("=== Docker再起動・プロキシ切替を開始します ===")
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
    stop_docker_desktop()
    time.sleep(15)

    if not ensure_docker_desktop_running():
        logger.error("Docker Desktopを再起動できませんでした。")
        return False

    return setup_docker_proxy(force_restart_docker=True)

def setup_docker_proxy(force_restart_docker: bool = False) -> bool:
    """
    VPN Gate Proxyコンテナを起動し、IPが切り替わったことを確認する。
    force_restart_docker: Trueの場合、無条件でDocker Desktopの再起動から行う。
    """
    if not force_restart_docker:
        # すでにポートが占有されている場合のチェック
        if is_port_in_use(8118):
            if is_port_owner_docker(8118):
                logger.info("ポート 8118 は既にDockerコンテナによって使用されています。接続確認を行います...")
                if is_proxy_working():
                    logger.info("既存のプロキシコンテナが正常に動作しています。")
                    return True
                else:
                    logger.warning("既存のプロキシコンテナが動作していません。フルリセットを行います。")
                    return restart_proxy()
            else:
                logger.warning("ポート 8118 がDocker以外のプロセスによって占有されています。解放を試みます。")
                kill_process_on_port(8118)

    max_retries = 10
    for attempt in range(max_retries):
        logger.info(f"Dockerコンテナ起動試行中 ({attempt + 1}/{max_retries})...")

        # コンテナのクリーンアップ
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)

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
            while True:
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

                match = re.search(r"before=([\d\.]+) after=([\d\.]+)", line)
                if not pattern_found and match:
                    before_ip = match.group(1)
                    after_ip = match.group(2)
                    if before_ip == after_ip:
                        logger.error(f"IPが変わっていません: before={before_ip} after={after_ip}")
                        break

                    logger.info("ログに接続成功パターンが見つかりました。静止を待ちます...")
                    pattern_found = True
                    start_wait = time.time()
                    while time.time() - start_wait < 10:
                        time.sleep(1)
                        if time.time() - last_log_time >= 5:
                            logger.info("5秒間のログ静止を確認しました。")
                            success = True
                            break
                    if success:
                        break

                if time.time() - last_log_time > 180:
                    logger.error("コンテナ起動タイムアウト")
                    break

            if success:
                if is_proxy_working():
                    return True
                else:
                    logger.warning("コンテナは起動しましたが、プロキシが正常に動作していません。")

        except Exception as e:
            logger.error(f"監視中にエラーが発生しました: {e}")

        logger.warning("起動に失敗しました。コンテナを破棄して再試行します。")
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
        process.terminate()
        time.sleep(5)
        
    logger.error("コンテナ起動の試行回数が上限に達しました。Docker Desktopの再起動を行います。")
    return restart_proxy()

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

def extract_pscube_graph_data(page: Page) -> dict | str:
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

            const totalLength = path.getTotalLength();
            const matrix = path.getScreenCTM();
            
            function getYValue(ptY) {
                let p1, p2;
                for (let i = 0; i < points.length - 1; i++) {
                    if (ptY >= points[i].y && ptY <= points[i+1].y) {
                        p1 = points[i];
                        p2 = points[i+1];
                        break;
                    }
                }
                if (!p1) {
                    if (ptY < points[0].y) { p1 = points[0]; p2 = points[1]; }
                    else { p1 = points[points.length - 2]; p2 = points[points.length - 1]; }
                }
                if (p1.y === p2.y) return p1.val;
                return p1.val + (ptY - p1.y) * (p2.val - p1.val) / (p2.y - p1.y);
            }

            let upwardSum = 0;
            let prevVal = null;
            
            // パス全体の長さから、十分な解像度でサンプリングする（最低1000点または0.5px間隔）
            let pathPoints = [];
            const step = Math.min(0.5, totalLength / 1000);
            for (let l = 0; l <= totalLength; l += step) {
                pathPoints.push(path.getPointAtLength(l));
            }
            // 最後の点も確実に追加
            pathPoints.push(path.getPointAtLength(totalLength));

            for (const ptLocal of pathPoints) {
                const ptScreen = ptLocal.matrixTransform(matrix);
                const ptY = ptScreen.y; 
                const currentVal = getYValue(ptY);
                if (prevVal !== null) {
                    const diff = currentVal - prevVal;
                    if (diff > 0) {
                        upwardSum += diff; // 傾きが正（出玉増加）の部分を足し合わせる
                    }
                }
                prevVal = currentVal;
            }

            const lastPointLocal = path.getPointAtLength(totalLength);
            const lastPointScreen = lastPointLocal.matrixTransform(matrix);
            const lastY = lastPointScreen.y + 0.5;
            const finalValue = Math.round(getYValue(lastY));

            return {
                final_diff: finalValue,
                upward_sum: Math.round(upwardSum)
            };
        }''')
        
        if isinstance(result, str) and "解析不能" in result:
            logger.warning(f"Graph解析エラー: {result}")
            
        return result
    except Exception as e:
        return f"解析エラー: {e}"

def site1_action(page: Page, target_models: list = None, specific_machines: list = None, result_queue: queue.Queue = None, stop_event: threading.Event = None) -> dict:
    """Site1 の具体的なページ操作ロジック"""
    data = {}
    
    if target_models is None:
        target_models = TARGET_MODELS
    try:
        # ユーザー要望: Site1はスマホ向けなので縦長にする
        page.set_viewport_size({"width": 390, "height": 844})
        
        # ページはStealthyFetcherにより既に開かれているが、念の為アクセス
        page.goto(SITE1_URL, wait_until="domcontentloaded")
        human_like_delay(2.0, 3.0)

        logger.debug("Site 1: パチンコデータボタンをクリック")
        # ボタンが表示されるのを待ってからクリック
        page.wait_for_selector(SITE1_PACHINKO_BTN, timeout=10000)
        page.click(SITE1_PACHINKO_BTN)
        
        # 機種一覧が表示されるのを待機
        page.wait_for_selector("ul#ulKI", timeout=20000)
        human_like_delay(1.5, 3.0)

        logger.debug("Site 1: 機種一覧の読み込みのためスクロール")
        human_like_scroll(page)

        logger.debug("Site 1: 機種名の特定処理")
        model_elements = page.query_selector_all(SITE1_MODEL_LIST)
        
        matched_models = []
        # OGIYA_BORDER_DICTキー + 住吉北店固有表記の両方をノーマライズして照合
        norm_targets = {calc.normalize_machine_name(m): m for m in target_models}
        # 住吉北店表記 -> BORDER_DICT表記 の逆引きも追加
        for sumiyoshi_name, ogiya_name in SUMIYOSHI_KITA_NAME_MAP.items():
            norm_targets[calc.normalize_machine_name(sumiyoshi_name)] = ogiya_name
        for el in model_elements:
            text = el.inner_text().strip()
            norm_text = calc.normalize_machine_name(text)
            if norm_text in norm_targets:
                matched_models.append((text, norm_targets[norm_text]))  # (サイト表記, BORDER_DICT表記)

        
        logger.info(f"Site 1: 対象機種が {len(matched_models)} 件見つかりました。")

        for site_model_name, calc_model_name in matched_models:
            logger.debug(f"Site 1: 対象機種 '{site_model_name}' (計算用: '{calc_model_name}') を探してクリックします")
            
            model_btn = page.query_selector(f"//div[contains(@class, 'nc-label') and text()='{site_model_name}']")
            if not model_btn:
                logger.warning(f"Site 1: 機種 '{site_model_name}' のボタンが見つかりません。")
                continue
            
            model_btn.click()
            page.wait_for_load_state("domcontentloaded")
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
            
            logger.info(f"Site 1: '{site_model_name}' で {len(machine_numbers)} 件の台番号を取得。")

            for idx, machine_num in enumerate(machine_numbers):
                if stop_event and stop_event.is_set():
                    logger.info("停止信号を検知しました。スクレイピングを中断します。")
                    return data
                logger.debug(f"Site 1: [{idx+1}/{len(machine_numbers)}] 台番号 {machine_num} のデータ取得を開始")
                try:
                    # 台番号リンクを特定してクリック（より厳密なXPathを使用）
                    xpath_selector = f"//a[contains(@class, 'btn-dai') and normalize-space()='{machine_num}']"
                    num_btn = page.query_selector(xpath_selector)
                    
                    if not num_btn:
                        # 画面外（遅延読み込み）の可能性があるためスクロールして再検索
                        logger.debug(f"Site 1: 台番号 {machine_num} が見つからないためスクロールします...")
                        human_like_scroll(page, max_scrolls=10)
                        num_btn = page.query_selector(xpath_selector)

                    if num_btn:
                        num_btn.click()
                        page.wait_for_load_state("domcontentloaded")
                        human_like_delay(2.0, 3.5) # ロードを待機

                        # --- 詳細データの取得 ---
                        
                        # 1. 累計スタートの取得
                        total_start_elem = page.query_selector('#tblDAbv2 > tr > td > div > table > tbody > tr > td:nth-child(2) > div > table > tbody > tr > td:nth-child(1) > div:nth-child(6) > div')
                        
                        total_start_val = 0
                        final_start_val = 0
                        if total_start_elem:
                            text = (total_start_elem.inner_text()).strip().replace(',', '')
                            total_start_val = int(text) if text.isdigit() else 0

                        # 累計スタートが0ならスキップ
                        if total_start_val == 0:
                            logger.info(f"Site 1: 台番号 {machine_num} は累計スタート0のためスキップします。")
                            if page.query_selector("a#php_v052"):
                                page.click("a#php_v052")
                                page.wait_for_load_state("domcontentloaded")
                            else:
                                page.go_back(wait_until="domcontentloaded")
                            continue

                        # 2. グラフから最終差玉を取得
                        graph_data = extract_pscube_graph_data(page)
                        if isinstance(graph_data, dict):
                            final_diff = graph_data.get("final_diff", 0)
                            upward_sum = graph_data.get("upward_sum", 0)
                        else:
                            final_diff = graph_data if isinstance(graph_data, (int, float)) else 0
                            upward_sum = 0
                        
                        # 3. 大当たり履歴のスクレイピング (詳細テーブル構造に対応)
                        start_list = []
                        shubetu_list = []
                        dedama_list = []
                        
                        # 履歴テーブル tblHISTb を特定
                        history_table = page.query_selector('#tblHISTb')

                        if history_table:
                            hit_elements = history_table.query_selector_all('tr')
                            
                            for hit in hit_elements:
                                tds = hit.query_selector_all('td')
                                if len(tds) >= 4:
                                    s_text = tds[2].inner_text().strip().replace(',', '')
                                    t_text = tds[3].inner_text().strip()
                                    d_text = "0"
                                    
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

                        # 最終スタートの計算（累計スタート - 履歴スタートの合計）
                        history_starts_sum = sum(int(s) for s in start_list if str(s).isdigit())
                        final_start_val = total_start_val - history_starts_sum
                        if final_start_val < 0: final_start_val = 0

                        # 4. 期待値計算の実行（計算にBORDER_DICT表記を使用）
                        calc_results = calc.calculate_expected_value(
                            start_list, dedama_list, shubetu_list, final_start_val, calc_model_name, final_diff, upward_sum=upward_sum
                        )
                        med_res = calc_results.get("med", (0, 0, 0))
                        kaitensuu, saishusadama, kitaichi = med_res

                        data[machine_num] = {
                            "機種名": site_model_name,
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
                            with open("scraping_data_sumiyoshi_kita.pkl", "wb") as f:
                                pickle.dump(data, f)
                        except Exception as e:
                            logger.error(f"pickle保存エラー: {e}")
                            
                        # キューに進捗を送信
                        if result_queue:
                            result_queue.put({"type": "progress", "data": data.copy()})
                        
                        if page.query_selector("a#php_v052"):
                            page.click("a#php_v052")
                            page.wait_for_load_state("domcontentloaded")
                        else:
                            page.go_back(wait_until="domcontentloaded")
                        human_like_delay(1.0, 2.0)
                        
                        
                except Exception as e:
                    logger.error(f"Site 1: 台番号 {machine_num} 処理中にエラー: {e}")
                    page.screenshot(path=f"error_site1_machine_{machine_num}.png")

            page.goto(SITE1_URL, wait_until="domcontentloaded")
            # パチンコボタンを再度クリックして機種一覧に戻る
            page.wait_for_selector(SITE1_PACHINKO_BTN, timeout=10000)
            page.click(SITE1_PACHINKO_BTN)
            page.wait_for_selector("ul#ulKI", timeout=20000)
            human_like_delay(1.0, 2.0)

    except Exception as e:
        logger.error(f"Site 1: 全体処理でエラーが発生しました: {e}")
        page.screenshot(path="error_site1_main.png")
    
    return data

def scrape_site1_scrapling(target_models: list = None, specific_machines: list = None, result_queue: queue.Queue = None, stop_event: threading.Event = None) -> Dict[str, dict]:
    """scraplingのStealthyFetcherを用いてSite1をスクレイピング"""
    logger.info("Site 1: scrapling (StealthyFetcher) を使用して実行します")
    
    # scraped_data の初期化
    scraped_data = {}
    
    def action_wrapper(page: Page):
        # 実際の操作ロジックを呼び出し、取得データをscraped_dataに格納
        result = site1_action(page, target_models, specific_machines, result_queue, stop_event)
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
