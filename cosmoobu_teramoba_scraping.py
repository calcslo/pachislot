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
from datetime import datetime, timedelta
from itertools import chain
from DrissionPage import ChromiumPage, ChromiumOptions
import pyautogui

logger = logging.getLogger(__name__)

PROXY_PORT = 8118
PROXY_SERVER = f"http://localhost:{PROXY_PORT}"
CONTAINER_NAME = "vpngate-proxy-cosmo-obu"
DOCKER_CMD = [
    "docker", "run", "--rm", "--name", CONTAINER_NAME,
    "--cap-add=NET_ADMIN", "--device=/dev/net/tun",
    "--dns=1.1.1.1", "--dns=8.8.8.8", "--dns=9.9.9.9",
    "-p", f"{PROXY_PORT}:8118",
    "tantantanuki/ja-vpngate-proxy"
]

_docker_lifecycle_lock = threading.RLock()


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


def is_docker_engine_ready() -> bool:
    try:
        res = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if res.returncode == 0 and "OSType:" in res.stdout:
            return True
        if res.stderr:
            logger.debug(f"Docker engine not ready: {res.stderr.strip()}")
    except Exception as e:
        logger.debug(f"Docker engine readiness check failed: {e}")
    return False


def is_windows_process_running(process_name: str) -> bool:
    try:
        res = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return process_name.lower() in res.stdout.lower()
    except Exception as e:
        logger.debug(f"Process check failed for {process_name}: {e}")
    return False


def ensure_docker_desktop_running() -> bool:
    logger.info("Docker Desktopの起動状態を確認しています...")
    if is_docker_engine_ready():
        logger.info("Docker Desktopは既に起動しています。")
        return True

    if is_windows_process_running("Docker Desktop.exe"):
        logger.info("Docker Desktopのプロセスは起動中です。エンジンの準備を待機します...")
    else:
        docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if not os.path.exists(docker_path):
            logger.error(f"Docker Desktopが見つかりません: {docker_path}")
            return False

        logger.info("Docker Desktopを起動します...")
        subprocess.Popen([docker_path], shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    # 起動を待機 (最大30秒)
    for i in range(6):
        time.sleep(5)
        logger.info(f"Dockerの起動を待機中... ({(i + 1) * 5}秒経過)")
        if is_docker_engine_ready():
            time.sleep(5)
            logger.info("Docker Desktopが正常に起動しました。")
            return True

    logger.error("Docker Desktopの起動タイムアウトです。")
    return False


def stop_docker_desktop():
    logger.info("Docker Desktopを終了しています...")
    for proc in ["Docker Desktop.exe", "com.docker.backend.exe", "com.docker.proxy.exe"]:
        subprocess.run(f'taskkill /F /IM "{proc}" /T', shell=True, capture_output=True)


def kill_process_on_port(port: int):
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True,
            capture_output=True,
            text=True
        )
        if not result.stdout:
            return

        pids = set()
        for line in result.stdout.strip().splitlines():
            if "LISTENING" in line and f":{port}" in line:
                parts = line.split()
                if parts:
                    pids.add(parts[-1])

        for pid in pids:
            logger.info(f"ポート {port} を使用中のプロセス (PID: {pid}) を終了します...")
            subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
            time.sleep(1)
    except Exception as e:
        logger.error(f"ポート {port} の解放中にエラー: {e}")


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def get_docker_containers_publishing_port(port: int) -> list[tuple[str, str]]:
    try:
        res = subprocess.run(
            ["docker", "ps", "--filter", f"publish={port}", "--format", "{{.ID}}\t{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=15
        )
        containers = []
        for line in res.stdout.strip().splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                containers.append((parts[0], parts[1]))
        return containers
    except Exception as e:
        logger.debug(f"Failed to inspect Docker port owner: {e}")
    return []


def is_port_owner_docker(port: int) -> bool:
    return bool(get_docker_containers_publishing_port(port))


def remove_docker_container(identifier: str):
    try:
        subprocess.run(["docker", "rm", "-f", identifier], capture_output=True, timeout=30)
    except Exception as e:
        logger.debug(f"Failed to remove Docker container {identifier}: {e}")


def remove_docker_containers(containers: list[tuple[str, str]]):
    for container_id, name in containers:
        logger.info(f"Dockerコンテナを停止します: {name} ({container_id})")
        remove_docker_container(container_id)


def remove_cosmo_proxy_container():
    remove_docker_container(CONTAINER_NAME)


def remove_containers_publishing_proxy_port():
    containers = get_docker_containers_publishing_port(PROXY_PORT)
    if containers:
        remove_docker_containers(containers)


def is_proxy_working() -> bool:
    try:
        resp = requests.get(
            "http://httpbin.org/ip",
            proxies={"http": PROXY_SERVER, "https": PROXY_SERVER},
            timeout=10
        )
        if resp.status_code == 200:
            logger.info(f"プロキシ接続成功: {resp.json().get('origin')}")
            return True
    except Exception as e:
        logger.debug(f"Proxy check failed: {e}")
    return False


def handle_docker_error():
    with _docker_lifecycle_lock:
        logger.info("エラー発生。DockerDesktopと関連プロセスをすべて終了し、10秒待機します...")
        stop_docker_desktop()
        time.sleep(10)
        logger.info("DockerDesktopを再起動します...")
        ensure_docker_desktop_running()

def start_container_until_ip_changes():
    with _docker_lifecycle_lock:
        while True:
            remove_cosmo_proxy_container()
            time.sleep(2)
            
            logger.info("コンテナを起動します...")
            process = subprocess.Popen(
                DOCKER_CMD,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            output_queue = queue.Queue()
            def read_docker_output():
                try:
                    for line in iter(process.stdout.readline, ""):
                        output_queue.put(line)
                finally:
                    try: process.stdout.close()
                    except: pass
            
            threading.Thread(target=read_docker_output, daemon=True).start()
            
            success = False
            start_time = time.time()
            error_occurred = False
            
            # IPが変わるまで10秒待つ
            while time.time() - start_time < 10:
                try:
                    line = output_queue.get(timeout=1)
                    line = line.strip()
                    if line:
                        logger.debug(f"Docker: {line}")
                        if "unknown server OS" in line or "error during connect" in line or "no matching manifest" in line:
                            error_occurred = True
                            break
                            
                        match = re.search(r"before=([\d\.]+) after=([\d\.]+)", line)
                        if match:
                            before_ip = match.group(1)
                            after_ip = match.group(2)
                            if before_ip != after_ip:
                                logger.info(f"IPが変更されました: {before_ip} -> {after_ip}")
                                success = True
                                break
                except queue.Empty:
                    if process.poll() is not None:
                        if process.returncode != 0:
                            error_occurred = True
                        break
            
            if error_occurred:
                process.terminate()
                raise Exception("コンテナ実行中にDockerエラーが発生しました。")
                
            if success:
                time.sleep(3)
                if is_proxy_working():
                    logger.info("プロキシの稼働を確認しました。")
                    return
                else:
                    logger.warning("プロキシが機能していません。コンテナを再起動します。")
            else:
                logger.warning("10秒以内にIPが変更されなかったため、コンテナを再起動します。")
                
            process.terminate()

def setup_docker_proxy(force_restart_docker: bool = False) -> bool:
    with _docker_lifecycle_lock:
        try:
            ensure_docker_desktop_running()
            start_container_until_ip_changes()
            return True
        except Exception as e:
            logger.error(f"セットアップ中にエラー: {e}")
            try:
                handle_docker_error()
                start_container_until_ip_changes()
                return True
            except Exception as e2:
                logger.error(f"再試行後もエラー: {e2}")
                return False

def restart_docker_proxy(restart_desktop: bool = False) -> bool:
    with _docker_lifecycle_lock:
        logger.info("Dockerプロキシを再起動します...")
        if restart_desktop:
            handle_docker_error()
            try:
                start_container_until_ip_changes()
                return True
            except Exception:
                return False
        else:
            try:
                start_container_until_ip_changes()
                return True
            except Exception:
                return False

def cleanup_docker_proxy(stop_desktop: bool = False):
    with _docker_lifecycle_lock:
        logger.info("Cosmo Obu Dockerプロキシをクリーンアップします...")
        remove_cosmo_proxy_container()
        if stop_desktop:
            stop_docker_desktop()

TARGET_MODELS = list(calc.COSMO_BORDER_DICT.keys())

def get_url(dai_num, year, month, day):
    return f'https://cosmojapan.pt.teramoba2.com/obu/standgraph/?rack_no={dai_num}&dai_hall_id=2648&target_date={year}-{month}-{day}'

import pyautogui

def click_doui_button(page: ChromiumPage):
    try:
        logger.debug("「同意する」ボタンの探索開始")
        doui_button = page.ele("@id=submittos", timeout=2)
        if doui_button:
            logger.info("「同意する」ボタンが見つかりました")
            try:
                doui_button.click()
            except Exception as e:
                logger.warning(f"「同意する」ボタンのクリックエラー: {e}")
        
        # 認証ボタン処理までの待機
        time.sleep(10)
        
        window_width = page.run_js("return window.innerWidth;")
        window_height = page.run_js("return window.innerHeight;")
        
        target_x = window_width - 300
        target_y = window_height - 53
        
        # 座標の可視化 (デバッグ用円描画)
        page.run_js(f"""
            var x = {target_x};
            var y = {target_y};
            var circle = document.createElement('div');
            circle.style.position = 'absolute';
            circle.style.left = x + 'px';
            circle.style.top = y + 'px';
            circle.style.width = '20px';
            circle.style.height = '20px';
            circle.style.borderRadius = '50%';
            circle.style.backgroundColor = 'red';
            circle.style.zIndex = '999999';
            document.body.appendChild(circle);
        """)
        
        logger.info(f"右下の認証ボタンをpyautoguiでクリックします。座標: ({target_x}, {target_y})")
        # まずページアクションで移動を試みる
        page.actions.move_to((target_x, target_y)).click()
        # pyautoguiで確実にクリック
        pyautogui.click(x=target_x, y=target_y)
        
        time.sleep(3)
    except Exception as e:
        logger.warning(f"「同意する」ボタンの処理でエラー: {e}")

def cal_samai_from_svg(path, second_line_digit, second_line_point):
    try:
        points = re.findall(r"([0-9.]+),([0-9.]+)", path)
        points = [(float(x), float(y)) for x, y in points]
        if not points:
            return 0
        baseline_y = points[0][1]
        adjusted_points = [(x, baseline_y - y) for x, y in points]
        final_my = adjusted_points[-1][1]
        samai = (second_line_digit / second_line_point) * final_my
        return round(samai)
    except Exception as e:
        logger.error(f"SVG差枚計算エラー: {e}")
        return 0

def scrape_cosmo_obu_drissionpage(target_models: list = None, specific_machines: list = None, result_queue: queue.Queue = None, stop_event: threading.Event = None) -> Dict[str, dict]:
    logger.info("Cosmo Obu: DrissionPage を使用して実行します")
    data = {}
    if target_models is None:
        target_models = TARGET_MODELS
        
    try:
        co = ChromiumOptions()
        path = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
        co.set_browser_path(path).save()
        co.set_proxy(PROXY_SERVER)
        page = ChromiumPage(addr_or_opts=co)
        page.set.window.max()
        
        yesterday = datetime.now() - timedelta(days=1)
        
        # 最初のアクセスで同意を処理
        page.get("https://www.google.co.jp/")
        page.get(get_url(606, yesterday.year, yesterday.month, yesterday.day))
        time.sleep(3)
        click_doui_button(page)
        
        all_machines = []
        for model in target_models:
            norm_model = calc.normalize_machine_name(model)
            found_ranges = None
            if hasattr(calc, 'COSMO_MACHINE_MAP'):
                for k, v in calc.COSMO_MACHINE_MAP.items():
                    if calc.normalize_machine_name(k) == norm_model:
                        found_ranges = v
                        break
            
            if found_ranges:
                for r in found_ranges:
                    all_machines.extend(list(r))
            else:
                logger.warning(f"機種 '{model}' の台番号範囲マップが定義されていないためスキップします。")
                
        # 重複排除とソート
        all_machines = sorted(list(set(all_machines)))
        
        if specific_machines:
            all_machines = [m for m in all_machines if str(m) in specific_machines]
            
        for dai_num in all_machines:
            if stop_event and stop_event.is_set():
                logger.info("停止信号を検知しました。スクレイピングを中断します。")
                break
            if '4' in str(dai_num) or '9' in str(dai_num):
                continue
            logger.debug(f"台番号 {dai_num} にアクセス中...")
            success = False
            for retry_count in range(3):
                try:
                    page.get(get_url(dai_num, yesterday.year, yesterday.month, yesterday.day))
                    time.sleep(2)
                    
                    if not page.eles('css:#sel_target_date > option'):
                        logger.debug(f"台番号 {dai_num}: 日付要素未検出のため同意画面を確認します。")
                        doui_button = page.ele("@id=submittos", timeout=1)
                        if doui_button:
                            logger.info(f"台番号 {dai_num}: 同意画面を検知。同意ボタン処理を実行します。")
                            click_doui_button(page)
                            page.refresh()
                            time.sleep(2)
                    
                    if not page.eles('css:#sel_target_date > option'):
                        raise Exception("要素が見つかりません。")
                    
                    # 機種名の取得
                    try:
                        kishumei_el = page.ele('css:div.st01.title.wrap-machine-name > span', timeout=2)
                        kishumei = kishumei_el.text.strip() if kishumei_el else "不明"
                    except Exception as e:
                        logger.warning(f"機種名取得エラー: {e}")
                        kishumei = "不明"
                    
                    # 対象機種チェック
                    norm_kishumei = calc.normalize_machine_name(kishumei)
                    if not any(calc.normalize_machine_name(m) == norm_kishumei for m in target_models):
                        success = True # スキップ対象として「処理成功（次へ）」
                        break
                        
                    # 総回転数（累計スタート）の取得と0ならスキップ
                    try:
                        total_start_el = page.ele("css:#contents-container > article > section.box-base.machine-info > div.box-article01 > div.banBox.digitPanel > div.tables.doubleBox.topBorder > div.right.soukaiten.start_boxheight_pachi > div > div.daidigit.num.m.green.data-soukaiten", timeout=1)
                        total_start_val = int(total_start_el.text.replace(',', '')) if total_start_el else 0
                        if total_start_val == 0:
                            logger.info(f"台番号 {dai_num}: 累計スタートが0のためスキップします。")
                            success = True
                            break
                    except Exception as e:
                        total_start_val = 0
                        
                    # 大当たり一覧ボタンのクリック
                    try:
                        ichiran = page.ele('css:#bonus_history_v2-block > section > div > div.control-button-group > div:nth-child(2) > a', timeout=1)
                        if ichiran and ichiran.states.is_displayed:
                            ichiran.click()
                            time.sleep(1)
                    except Exception as e:
                        logger.warning(f"一覧ボタンクリックエラー: {e}")
                        
                    # 続きを見るボタン
                    try:
                        tuduki = page.ele('css:#bonus_history_v2-block > section > div > div.graph-container.box > div:nth-child(1) > div > div > div.table-list > div > div > a', timeout=2)
                        if tuduki and tuduki.states.is_displayed:
                            tuduki.click()
                            time.sleep(1)
                    except Exception as e:
                        pass
                        
                    # 履歴の取得
                    try:
                        start_els = page.eles('css:tr.winlist td:nth-child(3), tr.winlistcollar td:nth-child(3)', timeout=3)
                        dedama_els = page.eles('css:tr.winlist td:nth-child(4), tr.winlistcollar td:nth-child(4)', timeout=1)
                        shubetu_els = page.eles('css:tr.winlist td:nth-child(5), tr.winlistcollar td:nth-child(5)', timeout=1)
                        
                        starts = [el.text for el in start_els]
                        dedamas = [el.text for el in dedama_els]
                        shubetus = [el.text for el in shubetu_els]
                    except Exception as e:
                        logger.warning(f"履歴取得エラー: {e}")
                        starts, dedamas, shubetus = [], [], []
                    
                    # SVGの解析
                    try:
                        path = page.ele('css:#sequence_graph-block > section > div > div.graph-container > div.box > div > svg > g.path-slump > path').attr('d')
                        second_line_el = page.ele('@fill=MediumSpringGreen').child(3)
                        second_line_point = float(second_line_el.attr('y')) - 0.5
                        second_line_digit = int(second_line_el.text.replace(",", ""))
                    except Exception as e:
                        logger.warning(f"台番号 {dai_num}: グラフデータが見つかりません。エラー: {e}")
                        success = True
                        break
                    
                    # 最終差玉
                    final_diff_ball = cal_samai_from_svg(path, second_line_digit, second_line_point)
                    
                    # 最終スタート
                    try:
                        final_start_el = page.ele('css:#contents-container > article > section.box-base.machine-info > div.box-article01 > div.banBox.digitPanel > div.tables.doubleBox.topBorder > div.left.start > div > div.daidigit.num.m.green')
                        final_start = int(final_start_el.text.replace(',', '')) if final_start_el else 0
                    except:
                        final_start = 0
                    
                    # ユーザー指摘により、リストの反転処理を削除（元のデータ順を維持）
                    # starts.reverse()
                    # shubetus.reverse()
                    # dedamas.reverse()
                    
                    # 期待値計算
                    calc_results = calc.calculate_expected_value(
                        starts, dedamas, shubetus, final_start, kishumei, final_diff_ball
                    )
                    
                    med_res = calc_results.get("med", (0, 0, 0))
                    kaitensuu, saishusadama, kitaichi = med_res
                    
                    machine_num = str(dai_num)
                    data[machine_num] = {
                        "機種名": kishumei,
                        "累計スタート": total_start_val,
                        "最終スタート": final_start,
                        "最終差玉": final_diff_ball,
                        "回転率(med)": kaitensuu,
                        "ボーダー差(med)": kitaichi,
                        "回転率(min)": calc_results["min"][0] if "min" in calc_results else 0,
                        "ボーダー差(min)": calc_results["min"][2] if "min" in calc_results else 0,
                        "回転率(max)": calc_results["max"][0] if "max" in calc_results else 0,
                        "ボーダー差(max)": calc_results["max"][2] if "max" in calc_results else 0,
                        "履歴_スタート": starts,
                        "履歴_種別": shubetus,
                        "履歴_出玉": dedamas
                    }
                    
                    min_res = calc_results.get("min", (0, 0, 0))
                    max_res = calc_results.get("max", (0, 0, 0))
                    print(f"日付:{yesterday.strftime('%m/%d')} 機種名:{kishumei} 台番号:{machine_num} 最小回転率:{min_res[0]:.2f} 回転率:{kaitensuu:.2f} 最大回転率:{max_res[0]:.2f} 差玉:{final_diff_ball} 最小ボーダー差分:{min_res[2]:.2f} ボーダー差分:{kitaichi:.2f} 最大ボーダー差分:{max_res[2]:.2f} 総回転数:{total_start_val}")
                    logger.info(f"CosmoObu: 台番号 {machine_num} ({kishumei}) 取得完了")
                    
                    try:
                        with open("scraping_data_cosmo_obu.pkl", "wb") as f:
                            pickle.dump(data, f)
                    except Exception as e:
                        logger.error(f"pickle保存エラー: {e}")
                        
                    if result_queue:
                        result_queue.put({"type": "progress", "data": data.copy()})
                        
                    success = True
                    break # 成功したのでリトライループを抜ける

                except Exception as e:
                    logger.warning(f"台番号 {dai_num} 試行 {retry_count + 1} でエラーが発生しました: {e}")
                    
                    try:
                        doui_button = page.ele("@id=submittos", timeout=1)
                        if doui_button:
                            click_doui_button(page)
                    except:
                        pass
                    
                    if retry_count == 0:
                        logger.info("エラー発生。IPが変わるまでコンテナを再起動します。")
                        start_container_until_ip_changes()
                    elif retry_count == 1:
                        logger.info("再試行失敗。Docker Desktopを終了し、10秒待機後再起動します。")
                        handle_docker_error()
                        start_container_until_ip_changes()
                    else:
                        logger.error(f"台番号 {dai_num}: 全試行失敗。スキップします。")
                        break
            
            if not success:
                continue
                
    except Exception as e:
        logger.error(f"全体処理でエラーが発生しました: {e}")
    finally:
        try:
            page.quit()
        except:
            pass
        
    logger.info("Cosmo Obu: 処理終了")
    return data


def run_cosmo_obu_scraping(
    target_models: list = None,
    specific_machines: list = None,
    result_queue: queue.Queue = None,
    stop_desktop_when_done: bool = False,
    stop_event: threading.Event = None,
) -> Dict[str, dict]:
    """Cosmo Obu用のDocker準備、スクレイピング、後片付けを一括で行う。"""
    with _docker_lifecycle_lock:
        try:
            logger.info("Cosmo Obu: Dockerとプロキシを準備します")
            if not setup_docker_proxy():
                logger.warning("初回のDockerプロキシ準備に失敗しました。Docker Desktopを再起動して再試行します。")
                if not restart_docker_proxy(restart_desktop=True):
                    raise RuntimeError("Dockerプロキシの準備に失敗しました。")

            logger.info("スクレイピングを開始します...")
            results = scrape_cosmo_obu_drissionpage(
                target_models=target_models,
                specific_machines=specific_machines,
                result_queue=result_queue,
                stop_event=stop_event,
            )
            logger.info("スクレイピングが完了しました。")
            return results
        finally:
            cleanup_docker_proxy(stop_desktop=stop_desktop_when_done)
if __name__ == "__main__":
    scrape_cosmo_obu_drissionpage()
