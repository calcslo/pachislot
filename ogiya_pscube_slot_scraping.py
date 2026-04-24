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
    logger.info("Docker Desktopを終了しています...")
    processes = ["Docker Desktop.exe", "com.docker.backend.exe", "com.docker.proxy.exe"]
    for proc in processes:
        subprocess.run(f'taskkill /F /IM "{proc}" /T', shell=True, capture_output=True)

def kill_process_on_port(port: int):
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

def setup_docker_proxy():
    max_retries = 20
    for attempt in range(max_retries):
        logger.info(f"Dockerコンテナ起動試行中 ({attempt + 1}/{max_retries})...")
        kill_process_on_port(8118)
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
                logger.info("localhost:8118 でプロキシの導通確認を行います...")
                try:
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
        
        logger.warning("起動に失敗しました。再起動します。")
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
        process.terminate()
        time.sleep(5)
        
    logger.error("最大試行回数を超えました。")
    return False

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
                
                // text要素のtransform属性から translateY を取得し、y属性があれば足し合わせる
                const transform = textEl.getAttribute('transform') || '';
                let textY = parseFloat(textEl.getAttribute('y') || '0');
                
                const tMatch = transform.match(/translate\(([^,\s]+)[,\s]+([^)]+)\)/);
                if (tMatch) {
                    textY += parseFloat(tMatch[2]);
                }
                
                labelPoints.push({ svgY: textY, val: val });
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
            const graphSvgY = pathLocalY + translateY;

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
                svgY: lp.svgY + labelBaseTranslateY,
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
        logger.debug(f"Graph Debug: {result}")
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

# ==========================================
# スクレイピング ロジック
# ==========================================

def site1_action(page: Page) -> None:
    progress = load_progress()

    try:
        page.set_viewport_size({"width": 390, "height": 844})
        
        page.goto(SITE1_URL, wait_until="networkidle")
        human_like_delay(2.0, 3.0)

        logger.debug("Site 1: スロットデータボタンをクリック")
        page.click(SITE1_SLOT_BTN)
        page.wait_for_load_state("networkidle")
        human_like_delay(1.5, 3.0)

        logger.debug("Site 1: 機種一覧の読み込みのためスクロール")
        human_like_scroll(page)

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
            human_like_delay(1.0, 2.0)
            
            human_like_scroll(page)
            
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
                # 本日、1日前、2日前の想定日付を計算
                now = datetime.datetime.now()
                if now.hour < 8:
                    now -= datetime.timedelta(days=1)
                expected_today = now.strftime("%Y-%m-%d")
                expected_day1 = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                expected_day2 = (now - datetime.timedelta(days=2)).strftime("%Y-%m-%d")

                completed_dates = get_completed_dates_for_machine(model_name, machine_num)
                if expected_today in completed_dates and expected_day1 in completed_dates and expected_day2 in completed_dates:
                    logger.debug(f"Site 1: 台番号 {machine_num} は本日、1日前、2日前のデータがDBに揃っているためスキップ。")
                    continue

                logger.debug(f"Site 1: [{idx+1}/{len(machine_numbers)}] 台番号 {machine_num} のデータ取得を開始")
                try:
                    num_btn = page.query_selector(f"a.btn-dai:has-text('{machine_num}')")
                    if num_btn:
                        num_btn.click()
                        page.wait_for_load_state("networkidle")
                        human_like_delay(2.0, 3.5)
                        
                        # 割り込み要素（ご存意ダイアログ等）のチェック
                        handle_interstitial(page)

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
                                
                                record_tuple = (
                                    actual_date, model_name, machine_num,
                                    int(str(bonus).replace(',','')) if str(bonus).replace(',','').isdigit() else 0,
                                    int(str(big).replace(',','')) if str(big).replace(',','').isdigit() else 0,
                                    int(str(reg).replace(',','')) if str(reg).replace(',','').isdigit() else 0,
                                    int(str(games).replace(',','')) if str(games).replace(',','').isdigit() else 0,
                                    sasamai if isinstance(sasamai, (int, float)) else 0
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

def main():
    logger.info("=== スロット スクレイピング開始 ===")
    init_db()
    migrate_csv_to_db()
    
    # 処理ループ (エラー時のリトライ付き)
    max_restarts = 20
    for attempt in range(max_restarts):
        try:
            if not ensure_docker_desktop_running():
                logger.error("Docker Desktopが起動できなかったため、処理を中止します。")
                break
            
            if not setup_docker_proxy():
                logger.error("Dockerプロキシのセットアップに失敗しました。再試行します。")
                continue
            
            scrape_site1_scrapling()
            
            # 成功してここまで来たらループを抜ける
            logger.info("全機種のスクレイピングが正常に完了しました。")
            break
            
        except Exception as e:
            logger.error(f"スクレイピング中に致命的なエラーが発生しました (試行 {attempt+1}/{max_restarts}): {e}")
            if attempt < max_restarts - 1:
                logger.info("Docker Desktopとコンテナを再起動してリトライします...")
                subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
                stop_docker_desktop()
                time.sleep(15)
            else:
                logger.error("最大リトライ回数に達したため、処理を終了します。")
    
    # データのエクスポート処理
    progress = load_progress()
    data = progress.get("data", [])
    if data:
        save_data_to_db(data)
        logger.info(f"合計 {len(data)} 件の新規データを DB に保存しました。")
        
        # pickleをクリア
        clear_progress()
        
        # docsディレクトリへのJSON出力とGitHubへの自動アップロード
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
    else:
        logger.warning("取得データがありませんでした。")
    
    logger.info("=== 全処理終了 ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P's Cube Slot Scraper")
    parser.add_argument("--cron", action="store_true", help="Cron mode: Only run between 5:00 and 7:00 AM")
    args = parser.parse_args()

    if args.cron:
        now = datetime.datetime.now()
        if not (5 <= now.hour < 7):
            logger.info(f"Cron mode: 現在の時刻({now.strftime('%H:%M')})は実行時間(5:00-7:00)外のため終了します。")
            exit(0)

    try:
        main()
    finally:
        logger.info("クリーンアップ処理を開始します...")
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
        stop_docker_desktop()
        
        # 定期実行(--cron)の場合は処理終了後にPCをシャットダウンする
        if args.cron:
            logger.info("タスクが完了しました。1分後にPCをシャットダウンします。")
            subprocess.run(["shutdown", "/s", "/t", "60"])
