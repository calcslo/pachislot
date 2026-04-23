import pyautogui
import numpy as np
import pandas as pd
import winsound
from retry import retry
from オーギヤ半田パチンコ出玉履歴から差枚計算 import cal_samai
from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import pickle
from datetime import datetime, timedelta
from DrissionPage.common import Settings
from itertools import chain
@retry(tries=3, delay=2)
def main():
    Settings.set_language('en')
    #リンク先のスクレイピングでは要素がロードされるまで待たせる必要があるかも


    def save_to_pickle(data, file_path):
        """データをpickleファイルに保存する"""
        with open(file_path, 'wb') as file:
            pickle.dump(data, file)
        print(f"Data successfully saved to {file_path}")

    def url_select(dai_num, year, month, day):
        target_url = f'https://ogiya.pt.teramoba2.com/handa/standgraph/?rack_no={dai_num}&dai_hall_id=2648&target_date={year}-{month}-{day}'
        return target_url
    def doui_button():
        try:
            print("「同意する」ボタンの探索開始")
            doui_button = page.ele("@id=submittos")
            print("「同意する」ボタンが見つかりました")
            doui_button.click()
        except Exception as e:
            print(f"「同意する」ボタンのクリックエラー: {e}")
        sleep(10)
        window_width = page.run_js("return window.innerWidth;")
        window_height = page.run_js("return window.innerHeight;")
        page.actions.move_to((window_width - 300, window_height - 53)).click()  # 右下に移動
        # マウスの移動位置に円を描画するJavaScriptを実行
        page.run_js("""
            var x = window.innerWidth - 300;
            var y = window.innerHeight - 53;
            var circle = document.createElement('div');
            circle.style.position = 'absolute';
            circle.style.left = x + 'px';
            circle.style.top = y + 'px';
            circle.style.width = '20px';
            circle.style.height = '20px';
            circle.style.borderRadius = '50%';
            circle.style.backgroundColor = 'red';
            circle.style.zIndex = '999999';  // 最前面に表示
            document.body.appendChild(circle);
        """)
        # 「同意する」ボタンをクリック
        pyautogui.click(x=window_width - 300, y=window_height - 53)
        print("クリックしました")
        sleep(3)

    def flatten_list(nested_list):
        flat_list = []
        for item in nested_list:
            if isinstance(item, list):
                flat_list.extend(flatten_list(item))  # 内側のリストをフラット化
            else:
                flat_list.append(item)
        return flat_list

    try:
        co = ChromiumOptions()
        path = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
        co.set_browser_path(path).save()
        co.set_proxy("http://localhost:8118")
        page = ChromiumPage(addr_or_opts=co)
        page.set.window.max()
        yesterday = datetime.now() - timedelta(days=1)
        all_scraped_data = []  # 全データを保存するリスト
        pickle_file_path = f'ogiyahanda_scraped_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
        page.get("https://www.google.co.jp/")
        page.get(url_select(606, yesterday.year, yesterday.month, yesterday.day))
        sleep(3)
        # 「同意する」ボタンをクリック
        doui_button()
        #674-1386
        ranges = [
            range(674, 267),
            range(277, 297),
            range(449, 525),
            range(558, 576),
            range(586, 636),
        ]
        for i in range(674, 1386):
            page.get(url_select(i, yesterday.year, yesterday.month, yesterday.day))
            sleep(2)
            kaisu = len(page.eles('css:#sel_target_date > option')) - 1
            print(f"台番号{i}")
            for d in range(kaisu):
                try:
                    select_date = page.ele(f'css:#sel_target_date > option:nth-child({d + 1})')
                    if not select_date.states.is_displayed:
                        sleep(1)
                    if select_date and select_date.states.is_displayed:
                        select_date.click()
                    else:
                        print(f"Select date option {d + 1} not displayed.")
                        continue  # 日付が見つからない場合、次のループに進む
                except Exception as e:
                    print(f"Error selecting date: {e}")
                    continue  # 日付選択時にエラーが発生した場合、次のループに進む
                date = select_date.text if select_date else "不明"
                print(f"取得日付:{date}")
                try:
                    kishumei = page.ele('css:div.st01.title.wrap-machine-name > span')
                    kishumei = kishumei.text if kishumei else "不明"
                except Exception as e:
                    print(f"Error getting kishumei: {e}")
                    kishumei = "不明"  # 取得できなかった場合、デフォルトの値
                dai_num = i
                try:
                    ichiran = page.ele(
                        'css:#bonus_history_v2-block > section > div > div.control-button-group > div:nth-child(2) > a',
                        timeout=1)
                    if ichiran.states.is_displayed:
                        ichiran.click()
                except Exception as e:
                    print(f"Error finding or clicking 'ichiran': {e}")
                    continue
                try:
                    tuduki = page.ele('css:#bonus_history_v2-block > section > div > div.graph-container.box > div:nth-child(1) > div > div > div.table-list > div > div > a', timeout=2)
                    if tuduki and tuduki.states.is_displayed:
                        tuduki.click()
                    else:
                        print(f"tuduki is not displayed.")
                except Exception as e:
                    print(f"Error clicking 'tuduki': {e}")
                try:
                    max_mochidama = int(page.ele('css:#contents-container > article > section.box-base.machine-info > div.box-article01 > div.banBox.digitPanel > div:nth-child(5) > div.left.max_mochidama > div > div.daidigit.num.ss.data-max-mochidama').text)
                    path = page.ele('css:#sequence_graph-block > section > div > div.graph-container > div.box > div > svg > g.path-slump > path').attr('d')
                    samai = cal_samai(path, max_mochidama)
                    start_sum = int(page.ele("css:#contents-container > article > section.box-base.machine-info > div.box-article01 > div.banBox.digitPanel > div.tables.doubleBox.topBorder > div.right.soukaiten.start_boxheight_pachi > div > div.daidigit.num.m.green.data-soukaiten").text)
                except Exception as e:
                    print(f"Error extracting win list or dedama: {e}")
                    continue  # 勝ちリストや出玉取得時にエラーが発生した場合、次のループに進む

                try:
                    all_scraped_data.append([date, kishumei, dai_num, samai, start_sum])
                except Exception as e:
                    print(f"Error appending data to all_scraped_data: {e}")
                # ピクルファイルに保存
                try:
                    save_to_pickle(all_scraped_data, pickle_file_path)
                except Exception as e:
                    print(f"Error saving data to pickle: {e}")
        page.close()
        if pickle_file_path:
            # 選択されたファイルを開いて読み込む
            with open(pickle_file_path, 'rb') as f:
                data_list = pickle.load(f)
        data_list = flatten_list(data_list)
        print(data_list)

        chunk_size = 5  # 1行あたりの列数
        num_chunks = (len(data_list) + chunk_size - 1) // chunk_size  # 切り上げ

        # パディングを行ってチャンクのサイズを揃える
        data_list_2d = [data_list[i * chunk_size: (i + 1) * chunk_size] for i in range(num_chunks)]

        # 最後のチャンクが満たない場合、パディング
        if len(data_list_2d[-1]) < chunk_size:
            data_list_2d[-1].extend([None] * (chunk_size - len(data_list_2d[-1])))

        # NumPy 配列に変換する
        data_array = np.array(data_list_2d, dtype=object)

        # Pandas DataFrameに変換してカラム名を設定
        column_names = ["日付", "機種名", "台番号", "差玉", "総回転数"]
        df = pd.DataFrame(data_array, columns=column_names)
        df = df.fillna('')
        store_name = "オーギヤ半田"
        # CSVファイルに書き出し
        df.to_csv(f"samaidata{store_name}.csv", index=False, encoding="utf-8_sig")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        # エラー音を鳴らす
        winsound.Beep(1000, 500)
try:
    main()
except Exception as e:
    print(f"最終的に失敗しました: {e}")