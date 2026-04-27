import pickle
import sqlite3
import requests
import re
import time
import random
import subprocess
import logging
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin
from urllib.parse import unquote

# ==========================================
# ログ設定
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# 設定値
# ==========================================
PROXY_SERVER = "http://localhost:8118"
CONTAINER_NAME = "vpngate-proxy"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "slot_data.db")

# みんレポ機種名 → DB登録名のマッピング（みんレポDB登録_オーギヤ半田.py と同期）
MACHINE_NAME_MAP = {
    "スマート沖スロ ニューキングハナハナV": "LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV",
    "スマート沖スロ+ニューキングハナハナV": "LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV",
    "ゴーゴージャグラー３":               "ｺﾞｰｺﾞｰｼﾞｬｸﾞﾗｰ3",
    "ジャグラーガールズSS":               "ｼﾞｬｸﾞﾗｰｶﾞｰﾙｽﾞSS",
    "ウルトラミラクルジャグラー":         "ｳﾙﾄﾗﾐﾗｸﾙｼﾞｬｸﾞﾗｰ",
    "ミスタージャグラー":                 "ﾐｽﾀｰｼﾞｬｸﾞﾗｰ",
}

# BOT検知回避用 User-Agent リスト
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
]

BASE_URL = 'https://min-repo.com/tag/%E3%82%AA%E3%83%BC%E3%82%AE%E3%83%A4%E3%82%BF%E3%82%A6%E3%83%B3%E5%8D%8A%E7%94%B0%E5%BA%97/'

# ==========================================
# Docker / プロキシ 管理
# ==========================================

def ensure_docker_desktop_running() -> bool:
    """Docker Desktopが起動しているか確認し、起動していなければ起動する。"""
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
    import socket
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


# ==========================================
# BOT検知回避 ユーティリティ
# ==========================================

def make_session(use_proxy: bool = True) -> requests.Session:
    """
    ランダムなUser-Agentを持つ新規セッションを生成する。
    プロキシを使用する場合はlocalhost:8118経由にする。
    """
    session = requests.Session()
    ua = random.choice(USER_AGENTS)
    session.headers.update({
        'User-Agent': ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.google.co.jp/',
        'DNT': '1',
    })
    if use_proxy:
        session.proxies = {
            "http": PROXY_SERVER,
            "https": PROXY_SERVER,
        }
    return session


def human_like_delay(min_sec: float = 1.5, max_sec: float = 4.0):
    """ランダム待機（BOT検知回避）"""
    delay = random.uniform(min_sec, max_sec)
    logger.debug(f"待機: {delay:.2f}秒")
    time.sleep(delay)


def fetch_with_retry(session: requests.Session, url: str, timeout: int = 20,
                     max_retries: int = 3) -> requests.Response:
    """
    リクエストを最大 max_retries 回試みる。
    失敗時は例外を再スロー。
    """
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response
        except Exception as e:
            logger.warning(f"リクエスト失敗 ({attempt+1}/{max_retries}) - {url}: {e}")
            if attempt < max_retries - 1:
                human_like_delay(3.0, 7.0)
            else:
                raise


# ==========================================
# データ保存
# ==========================================

def save_to_pickle(data, file_path):
    """データをpickleファイルに保存する"""
    with open(file_path, 'wb') as file:
        pickle.dump(data, file)
    logger.info(f"Data successfully saved to {file_path}")


# ==========================================
# DB 既存データ確認
# ==========================================

def is_data_already_scraped(date_str: str, machine_name: str) -> bool:
    """
    指定された日付と機種のデータが既に slot_data.db に存在するか確認する。
    date_str: YYYY/MM/DD
    machine_name: みんレポ上の機種名
    """
    if not os.path.exists(DB_FILE):
        return False

    # DB登録名に変換（マッピングにある場合）
    db_machine_name = MACHINE_NAME_MAP.get(machine_name, machine_name)
    # 日付フォーマット変換 (YYYY/MM/DD -> YYYY-MM-DD)
    db_date_str = date_str.replace("/", "-")

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 該当の日付・機種のデータが1件でもあれば「取得済み」とみなす
        query = "SELECT COUNT(*) FROM slot_data WHERE 日付 = ? AND 機種名 = ?"
        cursor.execute(query, (db_date_str, db_machine_name))
        count = cursor.fetchone()[0]
        
        conn.close()
        return count > 0
    except Exception as e:
        logger.error(f"DB確認中にエラー: {e}")
        return False


# ==========================================
# メインスクレイピングロジック（1回分）
# ==========================================

def _do_scraping(session: requests.Session, start_date: datetime, end_date: datetime,
                 pickle_file_path: str, td_text_list: list) -> list:
    """
    実際のスクレイピング処理。
    セッション・pickle保存先・途中結果リストを引数に取る。
    例外発生時は呼び出し元でリトライを判断する。
    """
    url = BASE_URL
    response = fetch_with_retry(session, url)
    soup = BeautifulSoup(response.text, 'html.parser')

    today = datetime.today()
    valid_links = []

    for a in soup.find_all('a', href=True):
        text = a.get_text(strip=True)
        link = urljoin(url, a['href'])
        date_candidate = None

        # パターン1: 今年の日付（例: 4/2(水)）
        match1 = re.match(r'^(\d{1,2})/(\d{1,2})\([^)]+\)$', text)
        if match1:
            month = int(match1.group(1))
            day = int(match1.group(2))
            try:
                date_candidate = datetime(today.year, month, day)
            except ValueError:
                continue
            if date_candidate > today:
                date_candidate = datetime(today.year - 1, month, day)

        # パターン2: 年付き日付（例: 2024/9/21(土)）
        match2 = re.match(r'^(\d{4})/(\d{1,2})/(\d{1,2})\([^)]+\)$', text)
        if match2:
            year = int(match2.group(1))
            month = int(match2.group(2))
            day = int(match2.group(3))
            try:
                date_candidate = datetime(year, month, day)
            except ValueError:
                continue

        if date_candidate and end_date >= date_candidate >= start_date:
            valid_links.append((text, link))

    logger.info(f"対象リンク数: {len(valid_links)}")
    for text, link in valid_links:
        logger.info(f"  {text}: {link}")

    kishu_values = [
        #'%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%83%8F%E3%83%8A%E3%83%8F%E3%83%8A%EF%BD%9E%E9%96%83%E5%85%89%EF%BD%9E%E2%80%9030',
        '%E3%82%B8%E3%83%A3%E3%82%B0%E3%83%A9%E3%83%BC%E3%82%AC%E3%83%BC%E3%83%AB%E3%82%BASS',
        "%E3%82%A6%E3%83%AB%E3%83%88%E3%83%A9%E3%83%9F%E3%83%A9%E3%82%AF%E3%83%AB%E3%82%B8%E3%83%A3%E3%82%B0%E3%83%A9%E3%83%BC",
        "%E3%83%9F%E3%82%B9%E3%82%BF%E3%83%BC%E3%82%B8%E3%83%A3%E3%82%B0%E3%83%A9%E3%83%BC",
        "%E3%82%B4%E3%83%BC%E3%82%B4%E3%83%BC%E3%82%B8%E3%83%A3%E3%82%B0%E3%83%A9%E3%83%BC%EF%BC%93",
        "%E3%82%B9%E3%83%9E%E3%83%BC%E3%83%88%E6%B2%96%E3%82%B9%E3%83%AD+%E3%83%8B%E3%83%A5%E3%83%BC%E3%82%AD%E3%83%B3%E3%82%B0%E3%83%8F%E3%83%8A%E3%83%8F%E3%83%8AV"
    ]

    for i in range(len(valid_links)):
        link = valid_links[i][1]
        match = re.search(r'https://min-repo\.com/(\d+)/', link)
        if not match:
            continue
        article_id = match.group(1)

        detail_links = [f'https://min-repo.com/{article_id}/?kishu={kishu}' for kishu in kishu_values]

        for detail_link in detail_links:
            kishu_param = detail_link.split('?kishu=')[-1]
            kishumei = unquote(kishu_param)

            link_text = valid_links[i][0]
            today_loop = datetime.today()
            date_text = re.sub(r'\(\S+\)', '', link_text)
            year_match = re.match(r'^\d{4}/\d{1,2}/\d{1,2}$', date_text)
            try:
                if year_match:
                    parsed_date = datetime.strptime(date_text, "%Y/%m/%d")
                else:
                    parsed_date = datetime.strptime(f"{today_loop.year}/{date_text}", "%Y/%m/%d")
                    if parsed_date > today_loop:
                        parsed_date = datetime(today_loop.year - 1, parsed_date.month, parsed_date.day)
                date_text = parsed_date.strftime("%Y/%m/%d")
                # 何月の何の機種かをログに表示
                logger.info(f"--- 【{parsed_date.month}月】{date_text} {kishumei} スクレイピング中 ---")
            except ValueError:
                logger.warning(f"日付変換エラー: {date_text}")
                continue

            weekday_match = re.search(r'(\(|（)(.)(\)|）)', link_text)
            if not weekday_match:
                continue
            weekday_text = weekday_match.group(2)

            # --- 既存データチェック ---
            if is_data_already_scraped(date_text, kishumei):
                logger.info(f"  [SKIP] 既にデータが存在します: {date_text} {kishumei}")
                continue

            # BOT検知回避: リクエスト間にランダム遅延
            human_like_delay(2.0, 5.0)

            response = fetch_with_retry(session, detail_link)
            soup = BeautifulSoup(response.text, 'html.parser')

            target_divs = soup.find_all('div', class_='tab_content')
            for div in target_divs:
                if div.find_all(class_='slump_list'):
                    logger.debug("slump_listがありました（スキップ）")
                    continue
                if not div.find_all(class_='table_wrap'):
                    logger.debug("table_wrapがありません（スキップ）")
                    continue
                trs = div.find_all('tr')
                trs = [tr for tr in trs if tr.find_all('td')]
                for tr in trs:
                    class_list_tr = tr.get('class', [])
                    if 'avg_row' in class_list_tr:
                        continue
                    td_text_list.append(date_text)
                    td_text_list.append(weekday_text)
                    td_text_list.append(kishumei)
                    tds = tr.find_all('td')
                    for td in tds:
                        text = td.get_text(strip=True)
                        if text:
                            td_text_list.append(text)

            save_to_pickle(td_text_list, pickle_file_path)
            logger.debug(f"中間保存完了: {len(td_text_list)} 件")

    return td_text_list


# ==========================================
# メインエントリ（Docker再起動リトライ付き）
# ==========================================

def scraping_from_minrepo(start_date: str, end_date: str):
    start_dt = datetime.strptime(start_date, '%Y/%m/%d')
    end_dt = datetime.strptime(end_date, '%Y/%m/%d')

    pickle_file_path = os.path.join(
        SCRIPT_DIR,
        f'scraped_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
    )
    td_text_list = []

    max_restarts = 10
    for attempt in range(max_restarts):
        logger.info(f"=== スクレイピング開始 (試行 {attempt+1}/{max_restarts}) ===")

        # Docker Desktop & プロキシ起動
        # 初回以外は強制的にDocker Desktop再起動から試みる（ループ回避）
        force_reset = (attempt > 0)
        if not ensure_docker_desktop_running():
            logger.error("Docker Desktopが起動できませんでした。15秒後に再試行します。")
            time.sleep(15)
            continue

        if not setup_docker_proxy(force_restart_docker=force_reset):
            logger.error("Dockerプロキシのセットアップに失敗しました。再試行します。")
            continue

        # 新しいセッション（新プロキシIP + ランダムUA）でリクエスト
        session = make_session(use_proxy=True)

        try:
            td_text_list = _do_scraping(session, start_dt, end_dt, pickle_file_path, td_text_list)
            logger.info("=== スクレイピング正常完了 ===")
            break

        except Exception as e:
            logger.error(f"スクレイピング中にエラーが発生しました: {e}")
            logger.info("中間データを保存します...")
            save_to_pickle(td_text_list, pickle_file_path)

            if attempt < max_restarts - 1:
                logger.info("Docker再起動・プロキシ切替後にリトライします...")
                if not restart_proxy():
                    logger.warning("プロキシ再起動に失敗。15秒後に再試行します。")
                    time.sleep(15)
            else:
                logger.error("最大リトライ回数に達しました。処理を終了します。")

    logger.info(f"取得済みデータ件数: {len(td_text_list)}")
    logger.info(f"pickleファイル: {pickle_file_path}")
    return pickle_file_path


if __name__ == "__main__":
    scraping_from_minrepo("2026/01/07", "2026/04/21")