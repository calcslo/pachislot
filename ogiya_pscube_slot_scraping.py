import random
import time
from typing import Dict
import pandas as pd
import logging
import os
import subprocess
import re
import socket
import requests
import pickle
import queue
import json
import datetime
import sqlite3
import argparse
import sys
from playwright.sync_api import Page
from scrapling.fetchers import StealthyFetcher

class SVGTimeoutError(Exception):
    """SVGの待機タイムアウト時に発生する例外"""
    pass

class ProxyError(Exception):
    """プロキシ接続エラー時に発生する例外"""
    pass

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
# --- Site 1 Settings ---
SITE1_URL = "https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c759102/"
SITE1_SLOT_BTN = "body > div.nc-main > div.nc-box.nc-box-inset.nc-background-b.nc-border-a > table > tbody > tr:nth-child(1) > td:nth-child(2) > a"
SITE1_MODEL_LIST = "a.btn-ki"
SITE1_MACHINE_LINK = "a.btn-dai"

# --- プロキシ設定 (Dockerコンテナ用) ---
PROXY_SERVER = "http://localhost:8118"
CONTAINER_NAME = "vpngate-proxy"

# --- DB・進捗ファイル設定 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "slot_data.db")
PROGRESS_FILE = os.path.join(SCRIPT_DIR, "slot_scraping_progress.pkl")

# ==========================================
# データ管理
# ==========================================
def init_db():
    logger.info(f"DB初期化を開始します: {DB_FILE}")
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS slot_data (
                日付 TEXT,
                機種名 TEXT,
                台番号 TEXT,
                BONUS INTEGER,
                BIG INTEGER,
                REG INTEGER,
                累計ゲーム INTEGER,
                最終差枚 INTEGER,
                PRIMARY KEY (日付, 機種名, 台番号)
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("DB初期化が正常に完了しました。")
    except Exception as e:
        logger.error(f"DB初期化中にエラーが発生しました: {e}")
        raise e

def migrate_csv_to_db():
    csv_file = "slot_scraping_results.csv"
    if os.path.exists(csv_file):
        try:
            logger.info("既存のCSVファイルからDBへのマイグレーションを開始します...")
            df = pd.read_csv(csv_file)
            conn = sqlite3.connect(DB_FILE)
            df.to_sql("temp_slot_data", conn, if_exists="replace", index=False)
            c = conn.cursor()
            c.execute('''
                INSERT OR IGNORE INTO slot_data (日付, 機種名, 台番号, BONUS, BIG, REG, 累計ゲーム, 最終差枚)
                SELECT 日付, 機種名, 台番号, BONUS, BIG, REG, 累計ゲーム, 最終差枚 FROM temp_slot_data
            ''')
            c.execute('DROP TABLE temp_slot_data')
            conn.commit()
            conn.close()
            os.rename(csv_file, f"slot_scraping_results_backup_{int(time.time())}.csv")
            logger.info("CSVからDBへのマイグレーションが完了しました。")
        except Exception as e:
            logger.error(f"マイグレーション中にエラーが発生しました: {e}")

def get_completed_dates_for_machine(model_name: str, machine_num: str) -> list:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # パフォーマンス向上のため、過去5日分程度の履歴のみを検索対象とする
    min_date = (datetime.datetime.now() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
    
    c.execute('SELECT 日付 FROM slot_data WHERE 機種名=? AND 台番号=? AND 日付 >= ?', (model_name, machine_num, min_date))
    dates = [row[0] for row in c.fetchall()]
    conn.close()
    return dates

def save_data_to_db(data_list):
    if not data_list:
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.executemany('''
        INSERT OR IGNORE INTO slot_data 
        (日付, 機種名, 台番号, BONUS, BIG, REG, 累計ゲーム, 最終差枚) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [(d['日付'], d['機種名'], d['台番号'], d['BONUS'], d['BIG'], d['REG'], d['累計ゲーム'], d['最終差枚']) for d in data_list])
    conn.commit()
    conn.close()

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "rb") as f:
                return pickle.load(f)
        except:
            pass
    return {"scraped_machines": [], "data": []}

def save_progress(progress):
    with open(PROGRESS_FILE, "wb") as f:
        pickle.dump(progress, f)

def clear_progress():
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

# ==========================================
# ユーティリティ関数（BOT検知回避用）
# ==========================================

def ensure_docker_desktop_running():
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

    for i in range(24):
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
    """Docker Desktopを終了する。"""
    logger.info("Docker Desktopを終了しています...")
    processes = ["Docker Desktop.exe", "com.docker.backend.exe", "com.docker.proxy.exe"]
    for proc in processes:
        subprocess.run(f'taskkill /F /IM "{proc}" /T', shell=True, capture_output=True)

def is_proxy_working() -> bool:
    """プロキシが正常に動作しているか確認する。"""
    try:
        resp = requests.get(
            "http://httpbin.org/ip",
            proxies={"http": PROXY_SERVER, "https": PROXY_SERVER},
            timeout=10
        )
        if resp.status_code == 200:
            logger.info(f"プロキシ動作確認OK: {resp.json().get('origin')}")
            return True
    except Exception:
        pass
    return False


def is_port_in_use(port: int) -> bool:
    """指定ポートが使用中か確認する。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def is_port_owner_docker(port: int) -> bool:
    """指定ポートを使用しているのがDockerコンテナか確認する。"""
    try:
        res = subprocess.run(
            ["docker", "ps", "--filter", f"publish={port}", "--format", "{{.ID}}"],
            capture_output=True, text=True
        )
        return bool(res.stdout.strip())
    except Exception:
        return False


def kill_process_on_port(port: int):
    """指定ポートを使用しているプロセスを強制終了する。"""
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if "LISTENING" in line and f":{port}" in line:
                    parts = line.split()
                    pid = parts[-1]
                    logger.info(f"ポート {port} を使用中のプロセス (PID: {pid}) を終了します...")
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                    time.sleep(1)
    except Exception as e:
        logger.error(f"ポート {port} の解放中にエラー: {e}")


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
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

def human_like_scroll(page: Page, wait_time: float = 3.0, max_scrolls: int = 30):
    logger.debug("スクロールを開始します...")
    previous_height = page.evaluate("document.body.scrollHeight")
    unchanged_count = 0
    
    for i in range(max_scrolls):
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

def _get_active_chart_svg(page: Page, date_id: str) -> str | None:
    """
    指定した日付ID（例: 'CHART-20260423'）に対応するアクティブなチャートコンテナのCSSセレクタを返す。
    表示状態（display: block）のul要素の中にあるSVGを対象とする。
    """
    selector = f"#{date_id} svg"
    try:
        page.wait_for_selector(selector, timeout=5000)
        return selector
    except Exception:
        return None


def handle_interstitial(page: Page):
    """
    「ご存意」などの割り込みダイアログやモーダルが表示されている場合に閉じる。
    「ご存意」などの割り込みモーダルを閉じる。
    """
    try:
        # P's Cube でよく出る割り込み要素のセレクタ
        selectors = [
            "text='閉じる'", 
            "text='OK'", 
            "text='確認'", 
            "div.nc-modal-close",
            "a.btn-main", # 通知画面のボタン
            ".nc-dialog-close",
            "text='機種データページ'" # 別のパターンのボタン
        ]
        for sel in selectors:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                logger.info(f"割り込み要素 '{sel}' を検知しました。クリックして閉じます。")
                btn.click()
                human_like_delay(0.5, 1.0)
                break
    except Exception as e:
        logger.debug(f"割り込み要素の処理中にエラー（無視可能）: {e}")

def check_page_health(page: Page):
    """
    プロキシエラーなどの異常画面が表示されていないか確認する。
    ERR_PROXY_CONNECTION_FAILED などの文字列が見つかった場合、ProxyError を投げる。
    """
    try:
        # Chromiumの標準的なエラー画面テキストをチェック
        # page.content() は重い場合があるため、まずは inner_text で軽くチェックを試みる
        # ただし、エラー画面では inner_text が空に近い場合があるため content も併用
        
        # 1. ページタイトルをチェック
        title = page.title()
        if "No internet" in title or "Proxy" in title:
            logger.error(f"異常なページタイトルを検知しました: {title}")
            raise ProxyError(f"Detected error page via title: {title}")

        # 2. ページ内のエラーコードをチェック
        content = page.content()
        error_codes = ["ERR_PROXY_CONNECTION_FAILED", "ERR_CONNECTION_REFUSED", "ERR_TUNNEL_CONNECTION_FAILED"]
        for code in error_codes:
            if code in content:
                logger.error(f"プロキシエラーコードを検知しました: {code}")
                raise ProxyError(f"Detected proxy error code: {code}")
        
        # 3. 特定のメッセージをチェック (画像にある日本語メッセージなど)
        if "proxy server" in content or "プロキシ" in content:
            if "something wrong" in content or "問題があります" in content:
                 logger.error("プロキシサーバーの問題に関するメッセージを検知しました。")
                 raise ProxyError("Detected proxy error message on page")

    except ProxyError as pe:
        raise pe
    except Exception as e:
        # ページの状態取得自体に失敗する場合（ブラウザがクラッシュしている等）
        logger.warning(f"ページ状態の確認中にエラー（無視可能か確認）: {e}")


def _extract_last_diff_from_active_chart(page: Page, chart_date_id: str) -> int | str:
    """
    指定した日付のチャートコンテナ（例: id='CHART-20260423'）内のスランプグラフから
    最終差枚を抽出して返す。
    """
    try:
        page.wait_for_selector(f"#{chart_date_id} svg", timeout=8000)
    except Exception as e:
        logger.error(f"SVG待機タイムアウト検知: {chart_date_id}")
        raise SVGTimeoutError(f"SVG待機タイムアウト: {e}")

    result = page.evaluate(r'''
        (chartDateId) => {
            const container = document.getElementById(chartDateId);
            if (!container) return `解析不能 (コンテナ不存在: ${chartDateId})`;

            const svg = container.querySelector('svg');
            if (!svg) return '解析不能 (SVG不存在)';

            // ラベルが含まれるグループをより柔軟に探す
            // text > tspan を持ち、かつそのテキストが数値であるものを探す
            const allTextEls = Array.from(svg.querySelectorAll('text'));
            const tspans = [];
            
            for (const textEl of allTextEls) {
                const tspan = textEl.querySelector('tspan');
                if (!tspan) continue;
                
                const text = tspan.textContent.trim();
                // 数値（カンマ、マイナス含む）かどうか判定
                if (/^-?[\d,]+$/.test(text)) {
                    // X軸ラベル（時間 09:00など）と区別するため、コロンを含まないものを優先
                    if (!text.includes(':')) {
                        tspans.push(tspan);
                    }
                }
            }
            
            // ---- 1a. Y軸ラベルの数値と大まかな位置（translateY）を収集 ----
            const labelCandidates = [];
            for (const textEl of allTextEls) {
                const tspan = textEl.querySelector('tspan');
                if (!tspan) continue;
                const text = tspan.textContent.trim();
                const rawText = text.replace(/[^-0-9]/g, '');
                if (!rawText || isNaN(parseInt(rawText, 10))) continue;
                const val = parseInt(rawText, 10);
                if (Math.abs(val) > 100000 || text.includes(':')) continue;

                // ラベル要素自身を含む全祖先のtranslateY合計（近傍マッチング用）
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

            // ---- 1b. Y罫線(amcharts-axis-tick)の正確なSVG Y座標を取得 ----
            // 罫線の path d="M0.5,285.5 L5.5,285.5" のY値が正確な座標
            // ラベルのtranslateY(283)より罫線のd属性Y(285.5)の方が精確
            const tickPaths = Array.from(svg.querySelectorAll('path.amcharts-axis-tick'));
            const labelPoints = [];

            for (const tick of tickPaths) {
                const d = tick.getAttribute('d') || '';
                // "M0.5,285.5 L..." からY座標を抽出
                const mMatch = d.match(/M\s*[\d.]+\s*,\s*([\d.]+)/);
                if (!mMatch) continue;
                const localY = parseFloat(mMatch[1]);

                // 罫線の祖先translateY（通常Y方向のtranslateは0だが念のため加算）
                let tickAncestorTY = 0;
                let tel = tick.parentElement;
                while (tel && tel !== svg) {
                    const t = tel.getAttribute('transform') || '';
                    const tm = t.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
                    if (tm) tickAncestorTY += parseFloat(tm[2]);
                    tel = tel.parentElement;
                }
                const tickSvgY = localY + tickAncestorTY;

                // この罫線Y座標に最も近いラベルを探す（近傍マッチング）
                let closest = null;
                let minDist = Infinity;
                for (const lc of labelCandidates) {
                    const dist = Math.abs(tickSvgY - lc.labelTransY);
                    if (dist < minDist) { minDist = dist; closest = lc; }
                }
                // 距離が離れすぎ（30px超）の場合は除外
                if (!closest || minDist > 30) continue;

                // 重複排除（同じval が既にある場合はより近いものを優先）
                const existing = labelPoints.find(lp => lp.val === closest.val);
                if (existing) {
                    if (minDist < existing._dist) {
                        existing.svgY = tickSvgY;
                        existing._dist = minDist;
                    }
                } else {
                    labelPoints.push({ svgY: tickSvgY, val: closest.val, _dist: minDist });
                }
            }

            // axis-tick が取得できなかった場合は従来のtranslateY方式にフォールバック
            if (labelPoints.length < 2) {
                for (const lc of labelCandidates) {
                    labelPoints.push({ svgY: lc.labelTransY, val: lc.val });
                }
            }

            if (labelPoints.length < 2) return '解析不能 (ラベル点不足)';
            labelPoints.sort((a, b) => a.svgY - b.svgY);


            // ---- 2. グラフPathの最終点を取得 ----
            // amcharts-graph-smoothedLine または amcharts-graph-line を汎用的に探す
            const graphPath = svg.querySelector('g[class*="amcharts-graph-"] path') ||
                              svg.querySelector('g.amcharts-graph-smoothedLine path') ||
                              svg.querySelector('g.amcharts-graph-line path') ||
                              svg.querySelector('g:nth-child(8) > g > g:nth-child(3) > path');
            
            if (!graphPath) return '解析不能 (グラフPath不存在)';

            const d = graphPath.getAttribute('d');
            if (!d) return '解析不能 (Path d属性なし)';

            // amchartsのsmoothedLineは末尾に "M0,0 L0,0" というダミーパスが付く。
            // 実データ部分のみを抽出するため、最初のMコマンド以降で
            // "M0,0" または "M 0,0" が現れる前の部分を使う。
            // 例: "M0,149 Q1,149... Q288,185 M0,0 L0,0"
            //     → "M0,149 Q1,149... Q288,185" の部分のみを対象とする
            let dataPath = d;
            // 末尾のダミーパス "M0[, ]0" を除去
            const dummyIdx = d.search(/M\s*0[,\s]+0\s*L/);
            if (dummyIdx > 0) {
                dataPath = d.substring(0, dummyIdx).trim();
            }

            // Q (二次ベジエ曲線) の終端座標も含めて全座標を抽出
            // Q cx,cy x,y → 終端は x,y
            // M x,y / L x,y → そのまま
            const allCoordsFromData = [];
            const mlPattern = /[ML]\s*(-?[\d.]+)[,\s]+(-?[\d.]+)/gi;
            const qPattern = /Q\s*-?[\d.]+[,\s]+-?[\d.]+[,\s]+(-?[\d.]+)[,\s]+(-?[\d.]+)/gi;
            let mc;
            while ((mc = mlPattern.exec(dataPath)) !== null) {
                allCoordsFromData.push({ x: parseFloat(mc[1]), y: parseFloat(mc[2]), cmd: mc[0][0] });
            }
            while ((mc = qPattern.exec(dataPath)) !== null) {
                allCoordsFromData.push({ x: parseFloat(mc[1]), y: parseFloat(mc[2]), cmd: 'Q' });
            }
            // x座標でソートして最後（最大x）の点を取得
            allCoordsFromData.sort((a, b) => a.x - b.x);
            
            const debugCoordCount = allCoordsFromData.length;
            const lastValidCoord = allCoordsFromData.length > 0 ? allCoordsFromData[allCoordsFromData.length - 1] : null;
            const last5Coords = allCoordsFromData.slice(-5);

            if (!lastValidCoord) return '解析不能 (有効Path座標抽出失敗)';

            const pathLocalY = lastValidCoord.y;
            let translateY = 0;
            let el = graphPath.parentElement;
            while (el && el !== svg) {
                const t = el.getAttribute('transform') || '';
                const tm = t.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
                if (tm) translateY += parseFloat(tm[2]);
                el = el.parentElement;
            }
            // ---- 0.5px補正 ----
            // amchartsのaxis-tickは半ピクセル座標(427.5等)で描画されるが、
            // グラフパスの座標は整数(427等)のため常に0.5px上にずれる。
            // +0.5でaxis-tick座標系と一致させ、値=0のときに0枚と読める。
            const graphSvgY = pathLocalY + translateY + 0.5;

            // ---- 修正: labelBaseTranslateYは不要（各ラベルで個別計算済み） ----
            // labelPointsのsvgYはすでにSVG座標系に変換済み
            const adjustedLabels = labelPoints.map(lp => ({
                svgY: lp.svgY,
                val: lp.val
            }));
            adjustedLabels.sort((a, b) => a.svgY - b.svgY);

            // graphSvgYに最も近い2点を探して補間
            let p1 = null, p2 = null;
            for (let i = 0; i < adjustedLabels.length - 1; i++) {
                if (graphSvgY >= adjustedLabels[i].svgY && graphSvgY <= adjustedLabels[i+1].svgY) {
                    p1 = adjustedLabels[i];
                    p2 = adjustedLabels[i+1];
                    break;
                }
            }
            // 範囲外の場合はクランプ
            if (!p1) {
                if (graphSvgY < adjustedLabels[0].svgY) {
                    p1 = adjustedLabels[0];
                    p2 = adjustedLabels[1];
                } else {
                    p1 = adjustedLabels[adjustedLabels.length - 2];
                    p2 = adjustedLabels[adjustedLabels.length - 1];
                }
            }

            if (p1.svgY === p2.svgY) return p1.val;

            const ratio = (graphSvgY - p1.svgY) / (p2.svgY - p1.svgY);
            const interpolated = p1.val + ratio * (p2.val - p1.val);
            const finalVal = Math.round(interpolated);
            
            // デバッグログ用に詳細情報を返す
            const last5Str = last5Coords.map(c => `(x:${c.x.toFixed(1)},y:${c.y.toFixed(1)})`).join(' ');
            const labelStr = adjustedLabels.map(l => `${l.val}@${l.svgY.toFixed(1)}`).join(' ');
            return `[${finalVal}] pathLocalY:${pathLocalY.toFixed(2)} transY:${translateY.toFixed(2)} gSvgY:${graphSvgY.toFixed(2)} | p1:${p1.val}(y:${p1.svgY.toFixed(1)}) p2:${p2.val}(y:${p2.svgY.toFixed(1)}) | coordN:${debugCoordCount} last5:${last5Str} | labels:[${labelStr}] | dummyCut:${dummyIdx > 0}`;
        }
    ''', chart_date_id)

    if isinstance(result, str) and "[" in result:
        logger.info(f"Graph Debug: {result}")  # オフセット検証のためINFOに昇格
        # 数値だけ抽出
        match = re.search(r'\[(-?\d+)\]', result)
        if match: return int(match.group(1))
    elif isinstance(result, str):
        logger.warning(f"Graph解析エラー: {result}")
    
    return result


def extract_pscube_graph_data_all_days(page: Page, today_date_str: str) -> dict:
    """
    スランプグラフから本日・1日前・2日前の最終差枚を取得して辞書で返す。

    Returns:
        {
            '本日': <int | str>,
            '1日前': <int | str>,
            '2日前': <int | str>,
        }
    """
    today_dt = datetime.datetime.strptime(today_date_str, "%Y-%m-%d")
    day1_dt = today_dt - datetime.timedelta(days=1)
    day2_dt = today_dt - datetime.timedelta(days=2)

    # チャートコンテナのIDは「CHART-YYYYMMDD」形式
    chart_ids = {
        '本日':  f"CHART-{today_dt.strftime('%Y%m%d')}",
        '1日前': f"CHART-{day1_dt.strftime('%Y%m%d')}",
        '2日前': f"CHART-{day2_dt.strftime('%Y%m%d')}",
    }

    # タブボタンのdata-ymd属性も同形式
    tab_ymds = {
        '本日':  today_dt.strftime('%Y%m%d'),
        '1日前': day1_dt.strftime('%Y%m%d'),
        '2日前': day2_dt.strftime('%Y%m%d'),
    }

    results = {}

    for day_label in ['本日', '1日前', '2日前']:
        chart_id = chart_ids[day_label]
        tab_ymd  = tab_ymds[day_label]

        # タブボタンをクリック（li[data-ymd='YYYYMMDD'] in #YMD-ul）
        try:
            tab_selector = f"#YMD-ul > li[data-ymd='{tab_ymd}']"
            tab_btn = page.query_selector(tab_selector)
            if tab_btn:
                tab_btn.click()
                logger.debug(f"タブ '{day_label}' ({tab_ymd}) をクリックしました。")
                # チャートコンテナが display:block になるまで待機
                page.wait_for_selector(
                    f"#{chart_id}[style*='display: block'], #{chart_id}:not([style*='display: none'])",
                    timeout=8000
                )
                time.sleep(1.5)  # グラフ再描画の余裕を持たせる
            else:
                logger.warning(f"タブボタンが見つかりません: {tab_selector}")
        except Exception as e:
            logger.warning(f"タブ '{day_label}' のクリック中にエラー: {e}")

        # 各タブの切り替え後にもチェック
        check_page_health(page)

        # グラフから最終差枚を抽出
        sasamai = _extract_last_diff_from_active_chart(page, chart_id)
        logger.info(f"{day_label} ({chart_id}): 最終差枚 = {sasamai}")
        results[day_label] = sasamai

    return results

def get_today_date(page: Page) -> str:
    text = page.inner_text("body")
    match = re.search(r"(\d{4}/\d{2}/\d{2})\s+(\d{2}:\d{2})\s*更新", text)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M")
        if 0 <= dt.hour < 8:
            today_dt = dt - datetime.timedelta(days=1)
        else:
            today_dt = dt
        return today_dt.strftime("%Y-%m-%d")
    else:
        now = datetime.datetime.now()
        if now.hour < 8:
            now -= datetime.timedelta(days=1)
        return now.strftime("%Y-%m-%d")

def extract_slot_table(page: Page) -> dict:
    """
    ユーザー指定のセレクタ (#tblDAb) からデータを抽出する。
    1行目: BONUS, 2行目: BIG, 3行目: REG, 9行目: 累計ゲーム
    各行の td(1):本日, td(2):1日前, td(3):2日前
    """
    return page.evaluate(r'''() => {
        const table = document.querySelector('#tblDAb');
        const data = { '本日': {}, '1日前': {}, '2日前': {} };
        if (!table) return data;
        
        const rows = Array.from(table.querySelectorAll('tr'));
        
        // 項目名（ラベル）によるマッピング
        // exactMatch: trueの項目は完全一致、falseは部分一致
        // ※ BIG/REGはincludes()だと「BIG確率」「REG確率」にもマッチし
        //   確率値(1/xxx)で上書きされてしまうため完全一致にする
        const labelMap = [
            { target: 'BONUS',  key: 'BONUS',    exactMatch: true },
            { target: 'BIG',    key: 'BIG',      exactMatch: true },
            { target: 'REG',    key: 'REG',      exactMatch: true },
            { target: '累計', key: '累計ゲーム', exactMatch: false }
        ];

        for (const row of rows) {
            const cells = Array.from(row.querySelectorAll('td, th'));
            if (cells.length < 2) continue;

            const rowLabel = cells[0].innerText.trim();
            
            for (const {target, key, exactMatch} of labelMap) {
                const matched = exactMatch ? (rowLabel === target) : rowLabel.includes(target);
                if (matched) {
                    // 数値セル（本日, 1日前, 2日前）を取得
                    // cells[0]はラベルなので、数値はcells[1]〜cells[3]
                    if (cells.length >= 4) {
                        data['本日'][key] = cells[1].innerText.replace(/,/g, '').trim();
                        data['1日前'][key] = cells[2].innerText.replace(/,/g, '').trim();
                        data['2日前'][key] = cells[3].innerText.replace(/,/g, '').trim();
                    } else if (cells.length === 3) {
                        // 2日前までしかない場合の予備
                        data['本日'][key] = cells[0].innerText.replace(/,/g, '').trim();
                        data['1日前'][key] = cells[1].innerText.replace(/,/g, '').trim();
                        data['2日前'][key] = cells[2].innerText.replace(/,/g, '').trim();
                    }
                    break; // 1行は1ラベルにのみマッチさせる
                }
            }
        }
        return data;
    }''')

def get_expected_machines_from_layout():
    """layout.jsonから期待される台番号のリストを取得する"""
    layout_path = os.path.join(SCRIPT_DIR, "docs", "layout.json")
    if not os.path.exists(layout_path):
        logger.warning(f"layout.jsonが見つかりません: {layout_path}")
        return set()
    
    try:
        with open(layout_path, "r", encoding="utf-8") as f:
            layout = json.load(f)
        
        machines = set()
        for row in layout:
            for cell in row:
                if cell is not None and str(cell).strip() != "":
                    # 数値のみを抽出
                    val = str(cell).strip()
                    if val.isdigit():
                        machines.add(val)
        return machines
    except Exception as e:
        logger.error(f"layout.jsonの解析中にエラー: {e}")
        return set()

def check_missing_machines(expected_machines):
    """DBをチェックし、期待される台番号の中でデータが欠けているものを返す"""
    if not expected_machines:
        return []
        
    now = datetime.datetime.now()
    if 0 <= now.hour < 8:
        now -= datetime.timedelta(days=1)
    
    target_dates = [
        now.strftime("%Y-%m-%d"),
        (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
        (now - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
    ]
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    missing = []
    for m in expected_machines:
        c.execute("SELECT COUNT(*) FROM slot_data WHERE 台番号=? AND 日付 IN (?, ?, ?)", (m, *target_dates))
        if c.fetchone()[0] < 3:
            missing.append(m)
    conn.close()
    return missing


# ==========================================
# スクレイピング ロジック
# ==========================================

def site1_action(page: Page) -> None:
    progress = load_progress()

    try:
        page.set_viewport_size({"width": 390, "height": 844})
        
        page.goto(SITE1_URL, wait_until="networkidle")
        check_page_health(page)
        human_like_delay(2.0, 3.0)

        logger.debug("Site 1: スロットデータボタンをクリック")
        page.click(SITE1_SLOT_BTN)
        page.wait_for_load_state("networkidle")
        check_page_health(page)
        human_like_delay(1.5, 3.0)

        logger.debug("Site 1: 機種一覧の読み込みのためスクロール")
        human_like_scroll(page)
        check_page_health(page)

        logger.debug("Site 1: 機種名の特定処理")
        # Find all machine models
        model_elements = page.query_selector_all("div.nc-label")
        model_names = []
        for el in model_elements:
            text = el.inner_text().strip()
            if text and text not in ["MENU"]: # Exclude non-model labels if any
                model_names.append(text)
                
        # Actually a.btn-ki contains the label, so let's use that
        model_btn_elements = page.query_selector_all(SITE1_MODEL_LIST)
        matched_models = []
        for el in model_btn_elements:
            text = el.inner_text().strip()
            if text and "21.7スロ" in text:
                # 最初の行だけを機種名とする (改行によるセレクタエラーを防ぐ)
                first_line = text.split('\n')[0].strip()
                matched_models.append(first_line)
                
        # Remove duplicates while preserving order
        matched_models = list(dict.fromkeys(matched_models))
        logger.info(f"Site 1: 全 {len(matched_models)} 機種が見つかりました。")

        # === DEBUG MARKER: あとで消す（デバッグ用 最初の3機種のみ） ===
        #matched_models = matched_models[:3]
        # ==============================================================

        for model_name in matched_models:
            logger.debug(f"Site 1: 機種 '{model_name}' を探してクリックします")
            model_btn = page.query_selector(f"//div[contains(@class, 'nc-label') and text()='{model_name}']")
            if not model_btn:
                # 念のためa.btn-ki経由でも探す
                model_btn = page.query_selector(f"a.btn-ki:has-text('{model_name}')")
                if not model_btn:
                    logger.warning(f"Site 1: 機種 '{model_name}' のボタンが見つかりません。")
                    continue
            
            model_btn.click()
            page.wait_for_load_state("networkidle")
            check_page_health(page)
            human_like_delay(1.0, 2.0)
            
            human_like_scroll(page)
            check_page_health(page)
            
            machine_links = page.query_selector_all(SITE1_MACHINE_LINK)
            machine_numbers = []
            for m_link in machine_links:
                num_text = m_link.inner_text().strip()
                if num_text:
                    machine_numbers.append(num_text)
            
            logger.info(f"Site 1: '{model_name}' で {len(machine_numbers)} 件の台番号を取得。")

            # === DEBUG MARKER: あとで消す（デバッグ用 最初の3台のみ） ===
            #machine_numbers = machine_numbers[:3]
            # ============================================================

            for idx, machine_num in enumerate(machine_numbers):
                # --- 修正箇所: ここから (深夜早朝0-8時の実行時は1日ずらす) ---
                now = datetime.datetime.now()
                if 0 <= now.hour < 8:
                    now -= datetime.timedelta(days=1)
                
                expected_today = now.strftime("%Y-%m-%d")
                expected_day1 = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                expected_day2 = (now - datetime.timedelta(days=2)).strftime("%Y-%m-%d")

                completed_dates = get_completed_dates_for_machine(model_name, machine_num)
                if expected_today in completed_dates and expected_day1 in completed_dates and expected_day2 in completed_dates:
                    logger.debug(f"Site 1: 台番号 {machine_num} は本日、1日前、2日前のデータがDBに揃っているためスキップ。")
                    continue

                # 何月の何の機種かをログに表示
                logger.info(f"--- 【{now.month}月】{model_name} (台番号: {machine_num}) スクレイピング中 ---")
                logger.debug(f"Site 1: [{idx+1}/{len(machine_numbers)}] 台番号 {machine_num} のデータ取得を開始")
                try:
                    num_btn = page.query_selector(f"a.btn-dai:has-text('{machine_num}')")
                    if num_btn:
                        num_btn.click()
                        page.wait_for_load_state("networkidle")
                        check_page_health(page)
                        human_like_delay(2.0, 3.5)
                        
                        # 割り込み要素（ご存意ダイアログ等）のチェック
                        handle_interstitial(page)
                        check_page_health(page)

                        today_date_str = get_today_date(page)
                        today_dt = datetime.datetime.strptime(today_date_str, "%Y-%m-%d")
                        day1_str = (today_dt - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                        day2_str = (today_dt - datetime.timedelta(days=2)).strftime("%Y-%m-%d")

                        completed_dates_for_machine = get_completed_dates_for_machine(model_name, machine_num)

                        dates_to_scrape = {}
                        if today_date_str not in completed_dates_for_machine: dates_to_scrape['本日'] = today_date_str
                        if day1_str not in completed_dates_for_machine: dates_to_scrape['1日前'] = day1_str
                        if day2_str not in completed_dates_for_machine: dates_to_scrape['2日前'] = day2_str

                        if not dates_to_scrape:
                            logger.info(f"Site 1: 台番号 {machine_num} の全日付が記録済みのためスキップします。")
                            page.go_back(wait_until="networkidle")
                            human_like_delay(1.0, 2.0)
                            continue

                        table_data = extract_slot_table(page)

                        # 本日→1日前→2日前の順にタブを切り替えながら最終差枚を一括取得
                        graph_results = extract_pscube_graph_data_all_days(page, today_date_str)

                        for day_label, actual_date in dates_to_scrape.items():
                            sasamai = graph_results.get(day_label, "取得失敗")

                            # DB保存
                            conn_local = sqlite3.connect(DB_FILE)
                            cursor_local = conn_local.cursor()
                            try:
                                bonus = table_data.get(day_label, {}).get("BONUS", 0)
                                big = table_data.get(day_label, {}).get("BIG", 0)
                                reg = table_data.get(day_label, {}).get("REG", 0)
                                games = table_data.get(day_label, {}).get("累計ゲーム", 0)

                                games_int = int(str(games).replace(',','')) if str(games).replace(',','').isdigit() else 0

                                # 累計ゲーム=0の台はグラフが存在しない（未稼働）ため
                                # SVG補間が誤値（例: 30）を返すケースがある。
                                # 0ゲームの場合は差枚も必ず0として保存する。
                                if games_int == 0:
                                    sasamai_final = 0
                                    if isinstance(sasamai, (int, float)) and sasamai != 0:
                                        logger.warning(
                                            f"Site 1: 台番号 {machine_num} ({actual_date}) "
                                            f"累計ゲーム=0 のため、グラフ読み取り値 {sasamai} を 0 に補正します。"
                                        )
                                else:
                                    sasamai_final = sasamai if isinstance(sasamai, (int, float)) else 0

                                record_tuple = (
                                    actual_date, model_name, machine_num,
                                    int(str(bonus).replace(',','')) if str(bonus).replace(',','').isdigit() else 0,
                                    int(str(big).replace(',','')) if str(big).replace(',','').isdigit() else 0,
                                    int(str(reg).replace(',','')) if str(reg).replace(',','').isdigit() else 0,
                                    games_int,
                                    sasamai_final
                                )
                                
                                cursor_local.execute('''
                                    INSERT OR REPLACE INTO slot_data (日付, 機種名, 台番号, BONUS, BIG, REG, 累計ゲーム, 最終差枚)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                ''', record_tuple)
                                conn_local.commit()
                                logger.info(f"Site 1: 台番号 {machine_num} ({actual_date}) 保存成功")
                            finally:
                                conn_local.close()

                        # 記録完了
                        logger.info(f"Site 1: 台番号 {machine_num} のデータ取得完了。")
                        
                        page.go_back(wait_until="networkidle")
                        check_page_health(page)
                        human_like_delay(1.0, 2.0)
                        
                except Exception as e:
                    error_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    logger.error(f"Site 1: 台番号 {machine_num} 処理中にエラー: {e}")
                    screenshot_path = f"error_slot_site1_machine_{machine_num}_{error_time}.png"
                    try:
                        page.screenshot(path=screenshot_path)
                    except Exception as ss_e:
                        logger.error(f"スクリーンショット保存失敗: {ss_e}")
                    
                    with open(os.path.join(SCRIPT_DIR, "error_log.txt"), "a", encoding="utf-8") as f:
                        f.write(f"[{error_time}] 台番号: {machine_num}, エラー原因: {e}, スクリーンショット: {screenshot_path}\n")
                        
                    raise e # 外側のループでリトライさせるために例外を投げる

            page.go_back(wait_until="networkidle")
            check_page_health(page)
            human_like_delay(1.0, 2.0)

    except Exception as e:
        error_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        logger.error(f"Site 1: 全体処理でエラーが発生しました: {e}")
        screenshot_path = f"error_slot_site1_main_{error_time}.png"
        try:
            page.screenshot(path=screenshot_path)
        except:
            pass
            
        with open(os.path.join(SCRIPT_DIR, "error_log.txt"), "a", encoding="utf-8") as f:
            f.write(f"[{error_time}] 全体処理エラー, エラー原因: {e}, スクリーンショット: {screenshot_path}\n")
            
        raise e

def scrape_site1_scrapling():
    logger.info("Site 1: scrapling (StealthyFetcher) を使用して実行します (プロキシなしテスト)")
    
    def action_wrapper(page: Page):
        site1_action(page)

    StealthyFetcher.fetch(
        SITE1_URL, 
        page_action=action_wrapper, 
        headless=False, 
        proxy=PROXY_SERVER,
        locale="ja-JP"
    )

def export_and_upload_to_github():
    # データのエクスポート処理とGitHubへの自動アップロード
    # （現在は都度DBに保存しているため、無条件でエクスポートとアップロードを実行する）
    logger.info("docsディレクトリへのJSONデータエクスポートを開始します...")
    try:
        subprocess.run([sys.executable, "export_slot_data.py"], check=True)
        logger.info("JSONデータのエクスポートが完了しました。")
        
        logger.info("GitHub Pagesへのアップロードを開始します...")
        subprocess.run(["git", "add", "docs/"], check=True)
        
        commit_res = subprocess.run(
            ["git", "commit", "-m", f"Auto update slot data {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
            capture_output=True, text=True
        )
        if "nothing to commit" in commit_res.stdout or "nothing added to commit" in commit_res.stdout:
            logger.info("変更がないため、コミット・プッシュはスキップします。")
        else:
            subprocess.run(["git", "push"], check=True)
            logger.info("GitHub Pagesへのアップロードが完了しました。")
    except Exception as e:
        logger.error(f"データエクスポートまたはGitHubへのアップロード中にエラーが発生しました: {e}")

def main(skip_scraping: bool = False):
    logger.info("=== スロット スクレイピング開始 ===")
    init_db()
    migrate_csv_to_db()
    
    if not skip_scraping:
        # 期待される台番号を取得しておく
        expected_machines = get_expected_machines_from_layout()
        if expected_machines:
            logger.info(f"島図より {len(expected_machines)} 台の台番号をロードしました。")

        # 処理ループ (エラー時のリトライ付き)
        max_restarts = 10
        for attempt in range(max_restarts):
            try:
                # 初回以外は強制的にDocker Desktop再起動から試みる（ループ回避）
                force_reset = (attempt > 0)
                if not ensure_docker_desktop_running():
                    logger.error("Docker Desktopが起動できなかったため、処理を中止します。")
                    break
                
                if not setup_docker_proxy(force_restart_docker=force_reset):
                    logger.error("Dockerプロキシのセットアップに失敗しました。再試行します。")
                    continue
                
                # 島図レイアウトを最新にするためにエクスポートを実行
                logger.info("島図レイアウトの最新化のため export_slot_data.py を実行します...")
                try:
                    subprocess.run([sys.executable, "export_slot_data.py"], check=True)
                except Exception as e:
                    logger.warning(f"export_slot_data.py の実行に失敗しました（既存のlayout.jsonを使用します）: {e}")

                # メインのスクレイピング実行
                scrape_site1_scrapling()
                
                # 成功してここに来た場合、島図（layout.json）と照合して欠損がないか確認
                expected = get_expected_machines_from_layout()
                if expected:
                    logger.info(f"島図より {len(expected)} 台の台番号をロードしました。完了確認を開始します。")
                    
                    for retry_i in range(3):
                        missing = check_missing_machines(expected)
                        if not missing:
                            logger.info("島図の全台のデータが揃っていることを確認しました（整合性OK）。")
                            break
                        
                        logger.warning(f"データ欠損を確認しました (残り {len(missing)} 台): {missing}")
                        logger.info(f"欠損データの再取得を開始します (追加試行 {retry_i + 1}/3)...")
                        
                        # IPを切り替えてから再試行（IPブロック対策）
                        if not setup_docker_proxy(force_restart_docker=True):
                            logger.warning("プロキシの切り替えに失敗しましたが、続行します。")
                        
                        scrape_site1_scrapling()
                    
                    # 最終チェック
                    final_missing = check_missing_machines(expected)
                    if not final_missing:
                        logger.info("全機種のスクレイピングが正常に完了しました。")
                        break
                    else:
                        logger.error(f"3回の追加試行後も以下のデータが不足しています: {final_missing}")
                        # 次の全体 attempt に回す
                        raise Exception("Incomplete data after additional retries")
                else:
                    logger.info("期待される台番号リストが空のため、完了確認をスキップして終了します。")
                    break
                
            except Exception as e:
                logger.error(f"スクレイピング中に致命的なエラーが発生しました (試行 {attempt+1}/{max_restarts}): {e}")
                if attempt < max_restarts - 1:
                    logger.info("Docker Desktopとコンテナを再起動してリトライします...")
                    if not restart_proxy():
                        logger.warning("プロキシ再起動に失敗。15秒後に再試行します。")
                        time.sleep(15)
                else:
                    logger.error("最大リトライ回数に達したため、処理を終了します。")
    else:
        logger.info("スクレイピング処理をスキップし、データのエクスポートとアップロードのみ行います。")
    
    # GitHubアップロード実行
    export_and_upload_to_github()
    
    logger.info("=== 全処理終了 ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P's Cube Slot Scraper")
    parser.add_argument("--cron", action="store_true", help="Cron mode: Only run between 3:00 and 5:00 AM")
    args = parser.parse_args()

    skip_scraping = False
    if args.cron:
        now = datetime.datetime.now()
        if not (3 <= now.hour < 5):
            logger.info(f"Cron mode: 現在の時刻({now.strftime('%H:%M')})は実行時間(3:00-5:00)外のため、スクレイピングをスキップしてGitHubアップロードのみ行います。")
            skip_scraping = True

    try:
        main(skip_scraping=skip_scraping)
    finally:
        logger.info("クリーンアップ処理を開始します...")
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
        stop_docker_desktop()
        
        # 定期実行(--cron)の場合は処理終了後にPCをシャットダウンする
        if args.cron:
            logger.info("タスクが完了しました。1分後にPCをシャットダウンします。")
            subprocess.run(["shutdown", "/s", "/t", "60"])
