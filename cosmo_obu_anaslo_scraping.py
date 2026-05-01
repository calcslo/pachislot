"""
コスモジャパン大府店 アナスロスクレイピングスクリプト
- スクレイピングロジック: アナスロスクレイピング_対策版_差枚あり_ARTなし.py を参考
- Docker/Proxy/DB/エクスポート部分: ogiya_pscube_slot_scraping.py と同じ構造
- データ保存先: slot_data_obu.db (slot_data.dbと同じスキーマ)
- エクスポート先: docs/cosmo_obu/data.json, docs/cosmo_obu/layout.json
"""

import random
import time
import logging
import os
import subprocess
import re
import socket
import requests
import pickle
import datetime
import sqlite3
import argparse
import sys
import threading
from DrissionPage import ChromiumPage, ChromiumOptions
from DrissionPage.errors import ElementLostError
from DrissionPage.common import Settings

Settings.set_language('en')

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
# アナスロ コスモジャパン大府店URL
ANASLO_BASE_URL = 'https://ana-slo.com/%E3%83%9B%E3%83%BC%E3%83%AB%E3%83%87%E3%83%BC%E3%82%BF/%E6%84%9B%E7%9F%A5%E7%9C%8C/%E3%82%B3%E3%82%B9%E3%83%A2%E3%82%B8%E3%83%A3%E3%83%91%E3%83%B3%E5%A4%A7%E5%BA%9C%E5%BA%97-%E3%83%87%E3%83%BC%E3%82%BF%E4%B8%80%E8%A6%A7/'

# プロキシ設定
PROXY_SERVER = "http://localhost:8118"
CONTAINER_NAME = "vpngate-proxy"

# DB・ファイル設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "slot_data_obu.db")
DOCS_DIR = os.path.join(SCRIPT_DIR, "docs", "cosmo_obu")

# Chromeパス
CHROME_PATH = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
ADBLOCK_PATH = r"D:\Download\google chrome\AdBlock"


# ==========================================
# DB管理 (slot_data.dbと同じスキーマ)
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


def get_completed_dates_for_machine(model_name: str, machine_num: str) -> list:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    min_date = (datetime.datetime.now() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
    c.execute('SELECT 日付 FROM slot_data WHERE 機種名=? AND 台番号=? AND 日付 >= ?',
              (model_name, machine_num, min_date))
    dates = [row[0] for row in c.fetchall()]
    conn.close()
    return dates


def is_date_complete(date_str: str, expected_count: int = 640) -> bool:
    """指定した日付のデータがDBに全て揃っているか確認する"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM slot_data WHERE 日付 = ?', (date_str,))
        count = c.fetchone()[0]
        conn.close()
        return count >= expected_count
    except Exception as e:
        logger.warning(f"完了チェック中にエラー: {e}")
        return False


def save_data_to_db(data_list):
    if not data_list:
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.executemany('''
        INSERT OR IGNORE INTO slot_data
        (日付, 機種名, 台番号, BONUS, BIG, REG, 累計ゲーム, 最終差枚)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [(d['日付'], d['機種名'], d['台番号'], d['BONUS'], d['BIG'], d['REG'],
           d['累計ゲーム'], d['最終差枚']) for d in data_list])
    conn.commit()
    conn.close()


# ==========================================
# Docker/Proxy管理 (ogiya_pscube_slot_scraping.pyと同じ)
# ==========================================
def ensure_docker_desktop_running():
    logger.info("Docker Desktopの起動状態を確認しています...")
    try:
        res = subprocess.run(["docker", "version"], capture_output=True, text=True)
        if res.returncode == 0:
            logger.info("Docker Desktopは既に起動しています。")
            return True
    except Exception:
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
        logger.info(f"Dockerの起動を待機中... ({(i+1)*5}秒経過)")
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


def is_proxy_working() -> bool:
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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def is_port_owner_docker(port: int) -> bool:
    try:
        res = subprocess.run(
            ["docker", "ps", "--filter", f"publish={port}", "--format", "{{.ID}}"],
            capture_output=True, text=True
        )
        return bool(res.stdout.strip())
    except Exception:
        return False


def kill_process_on_port(port: int):
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True, capture_output=True, text=True
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
    logger.info("=== Docker再起動・プロキシ切替を開始します ===")
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
    stop_docker_desktop()
    time.sleep(15)
    if not ensure_docker_desktop_running():
        logger.error("Docker Desktopを再起動できませんでした。")
        return False
    return setup_docker_proxy(force_restart_docker=True)


def setup_docker_proxy(force_restart_docker: bool = False) -> bool:
    if not force_restart_docker:
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
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
        process = subprocess.Popen(
            ["docker", "run", "--rm", "--name", CONTAINER_NAME,
             "--cap-add=NET_ADMIN", "--device=/dev/net/tun",
             "--dns=1.1.1.1", "--dns=8.8.8.8", "--dns=9.9.9.9",
             "-p", "8118:8118",
             "tantantanuki/ja-vpngate-proxy"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
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


# ==========================================
# アナスロ スクレイピングユーティリティ
# ==========================================
def wait_for_elements(page: ChromiumPage, selector: str, timeout: int = 10):
    for _ in range(timeout):
        elements = page.eles(f'css:{selector}')
        if elements:
            return elements
        time.sleep(1)
    raise TimeoutError(f"Elements did not load within timeout: {selector}")


def get_all_text(cells):
    return [cell.text.strip() for cell in cells if cell.text.strip()]


def extract_date_without_weekday(text: str):
    """日付部分のみを抽出してdatetime形式に変換"""
    try:
        date_match = re.search(r'\d{4}/\d{2}/\d{2}', text)
        if date_match:
            return datetime.datetime.strptime(date_match.group(), '%Y/%m/%d')
        return None
    except ValueError:
        return None


def is_within_date_range(link_text: str, start_date: datetime.datetime, end_date: datetime.datetime) -> bool:
    """リンクテキストの日付が指定した範囲内にあるかを確認する"""
    link_date = extract_date_without_weekday(link_text)
    if link_date:
        return start_date <= link_date <= end_date
    return False


# insert_text_in_list 関数は廃止されました。


def parse_scraped_data(scraped_list: list, date_str: str) -> list:
    """
    アナスロのスクレイピングデータ(6要素/行: 機種名, 台番号, G数, 差枚, BIG, REG)
    をDBレコード用dictに変換する。
    """
    records = []
    chunk_size = 9
    for i in range(0, len(scraped_list), chunk_size):
        chunk = scraped_list[i:i+chunk_size]
        if len(chunk) < chunk_size:
            break
        try:
            # インデックスはアナスロの表レイアウトに準拠
            kishumei = str(chunk[0]).strip()
            dai_num = str(chunk[1]).strip()
            games = int(str(chunk[2]).replace(',', '')) if str(chunk[2]).replace(',', '').isdigit() else 0
            sasamai = int(str(chunk[3]).replace(',', '').replace('+', '')) if re.match(r'^[+-]?\d+$', str(chunk[3]).replace(',', '')) else 0
            big = int(str(chunk[4]).replace(',', '')) if str(chunk[4]).replace(',', '').isdigit() else 0
            reg = int(str(chunk[5]).replace(',', '')) if str(chunk[5]).replace(',', '').isdigit() else 0
            bonus = big + reg

            records.append({
                '日付': date_str,
                '機種名': kishumei,
                '台番号': dai_num,
                'BONUS': bonus,
                'BIG': big,
                'REG': reg,
                '累計ゲーム': games,
                '最終差枚': sasamai,
            })
        except Exception as e:
            logger.warning(f"データ解析エラー (index {i}): {e}")
            continue
    return records



# ==========================================
# スクレイピング本体 (アナスロ方式)
# ==========================================
def scrape_cosmo_obu_anaslo(
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    stop_event: threading.Event = None,
) -> list:
    """
    アナスロからコスモジャパン大府店のデータをスクレイピングして
    DBレコードのリストを返す。
    """
    co = ChromiumOptions()
    co.headless(False)
    co.set_proxy(PROXY_SERVER)
    co.set_browser_path(CHROME_PATH).save()
    co.no_imgs(True)
    try:
        co.add_extension(ADBLOCK_PATH)
    except Exception:
        pass

    page = ChromiumPage(addr_or_opts=co)
    all_records = []

    try:
        page.get(ANASLO_BASE_URL)
        selector = 'div.table-row > div.table-data-cell > a'
        links = wait_for_elements(page, selector)
        logger.info(f"Total links found: {len(links)}")

        index = 0
        while index < len(links):
            if stop_event and stop_event.is_set():
                logger.info("停止信号を検知しました。スクレイピングを中断します。")
                break

            link = links[index]
            link_text = link.text.strip()

            if not is_within_date_range(link_text, start_date, end_date):
                logger.info(f"Skipping link: {link_text} (not within date range)")
                index += 1
                continue

            date_text = re.sub(r'\(\S+\)', '', link_text)
            weekday_match = re.search(r'(\(|（)(.)(\)|）)', link_text)
            weekday_text = weekday_match.group(2) if weekday_match else ''

            # 日付フォーマット変換 (YYYY/MM/DD -> YYYY-MM-DD)
            date_match = re.search(r'(\d{4})/(\d{2})/(\d{2})', date_text)
            if date_match:
                date_db_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                if is_date_complete(date_db_str):
                    logger.info(f"Skipping completed date: {date_db_str}")
                    index += 1
                    continue
            else:
                logger.warning(f"Could not parse date from link: {link_text}")

            success = False
            for retry in range(3):
                try:
                    logger.info(f"Processing link ({retry+1}/3): {link_text} -> {link.attr('href')}")
                    link.click()
                    time.sleep(2)

                    # URLから日付を取得
                    current_url = page.url
                    date_from_url = None
                    url_date_match = re.search(r'(\d{4}-\d{2}-\d{2})', current_url)
                    if url_date_match:
                        date_from_url = url_date_match.group(1)
                    else:
                        # URLに含まれない場合のフォールバック
                        date_from_url = date_db_str
                    
                    logger.info(f"Page Date: {date_from_url}")

                    # 「すべてのデータ」ボタンをクリック
                    page.ele('#all_data_btn').click()
                    selector2 = 'table#all_data_table > tbody > tr > td'
                    elements2 = wait_for_elements(page, selector2)
                    scraped_data = get_all_text(elements2)

                    records = parse_scraped_data(scraped_data, date_from_url)
                    logger.info(f"{date_text}: {len(records)} 件取得")
                    all_records.extend(records)

                    # DBに保存
                    save_data_to_db(records)
                    logger.info(f"{date_text}: DBへ保存完了")
                    
                    success = True
                    break

                except Exception as e:
                    logger.warning(f"ページ処理エラー (試行 {retry+1}/3, {link_text}): {e}")
                    if retry == 0:
                        logger.info("ページをリロードして再試行します...")
                    elif retry == 1:
                        logger.info("プロキシを再起動して再試行します...")
                        restart_proxy()
                    else:
                        logger.error(f"最大リトライ回数に達しました。この台をスキップします: {link_text}")
                        break
                    
                    # リロードして要素を再取得
                    try:
                        page.get(ANASLO_BASE_URL)
                        links = wait_for_elements(page, selector)
                        if index < len(links):
                            link = links[index]
                        else:
                            logger.error("リロード後にリンクが見つかりませんでした。")
                            break
                    except Exception as re_e:
                        logger.error(f"リロード中にエラーが発生しました: {re_e}")
                        break

            # 一覧ページに戻る（既にリトライ処理内で戻っている場合もあるが、確実に）
            if page.url != ANASLO_BASE_URL:
                try:
                    page.get(ANASLO_BASE_URL)
                except Exception:
                    pass
            
            # linksを常に最新の状態に更新し、次の台へ
            try:
                links = wait_for_elements(page, selector)
            except Exception:
                logger.error("ベースURLの要素取得に失敗しました。")
                break
            index += 1


    except TimeoutError as e:
        logger.error(f"タイムアウトエラー: {e}")
    except ElementLostError as e:
        logger.error(f"ElementLostError: {e}")
    except Exception as e:
        logger.error(f"予期せぬエラー: {e}")
    finally:
        try:
            page.close()
        except Exception:
            pass

    logger.info(f"スクレイピング完了: 合計 {len(all_records)} 件")
    return all_records


# ==========================================
# エクスポートとGitHub
# ==========================================
def export_and_upload_to_github():
    logger.info("docsディレクトリへのJSONデータエクスポートを開始します...")
    try:
        subprocess.run([sys.executable, "export_slot_data_obu.py"], check=True)
        logger.info("JSONデータのエクスポートが完了しました。")

        logger.info("GitHub Pagesへのアップロードを開始します...")
        subprocess.run(["git", "add", "docs/"], check=True)

        commit_res = subprocess.run(
            ["git", "commit", "-m",
             f"Auto update cosmo_obu data {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
            capture_output=True, text=True
        )
        if "nothing to commit" in commit_res.stdout or "nothing added to commit" in commit_res.stdout:
            logger.info("変更がないため、コミット・プッシュはスキップします。")
        else:
            subprocess.run(["git", "push"], check=True)
            logger.info("GitHub Pagesへのアップロードが完了しました。")
    except Exception as e:
        logger.error(f"エクスポートまたはGitHubアップロード中にエラー: {e}")


# ==========================================
# メイン処理
# ==========================================
def main(skip_scraping: bool = False):
    logger.info("=== コスモジャパン大府店 スクレイピング開始 ===")
    init_db()

    if not skip_scraping:
        # デフォルト: 直近90日間を収集対象とする
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=90)

        max_restarts = 10
        for attempt in range(max_restarts):
            try:
                force_reset = (attempt > 0)
                if not ensure_docker_desktop_running():
                    logger.error("Docker Desktopが起動できなかったため、処理を中止します。")
                    break

                if not setup_docker_proxy(force_restart_docker=force_reset):
                    logger.error("Dockerプロキシのセットアップに失敗しました。再試行します。")
                    continue

                scrape_cosmo_obu_anaslo(start_date, end_date)
                logger.info("スクレイピングが正常に完了しました。")
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
    parser = argparse.ArgumentParser(description="Cosmo Obu Anaslot Scraper")
    parser.add_argument("--cron", action="store_true", help="Cron mode: Only run between 3:00 and 5:00 AM")
    parser.add_argument("--days", type=int, default=90, help="収集対象日数 (default: 90)")
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

        if args.cron:
            logger.info("タスクが完了しました。1分後にPCをシャットダウンします。")
            subprocess.run(["shutdown", "/s", "/t", "60"])
