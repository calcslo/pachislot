import os
from itertools import chain
import pyautogui
import numpy as np
import pandas as pd
import winsound
from retry import retry
from 大府パチンコ出玉履歴から差枚計算 import cal_samai_from_bonus_history
from 大府パチンコ出玉履歴から差枚計算 import m_cal_samai_from_bonus_history
from 大府パチンコ出玉履歴から差枚計算 import M_cal_samai_from_bonus_history
from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import pickle
from datetime import datetime, timedelta
from DrissionPage.common import Settings
@retry(tries=3, delay=2)
def main():
    Settings.set_language('en')
    flag = False
    #リンク先のスクレイピングでは要素がロードされるまで待たせる必要があるかも
    def remove_outliers(df, column_name):
        Q1 = df[column_name].quantile(0.25)
        Q3 = df[column_name].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return df[(df[column_name] >= lower_bound) & (df[column_name] <= upper_bound)]
    def check_and_write_dates(last_date_text, first_date_text, flag):
        last_date_file =  r"C:\Users\mikih\PycharmProjects\pythonProject\obu_last_date.txt"
        if not flag:
            """
            # last_date.txt の確認と作成
            if not os.path.exists(last_date_file):
                with open(last_date_file, "w") as f:
                    f.write(last_date_text)
                print(f"{last_date_file} を作成しました。")
    
            # first_date.txt の確認と作成
            if not os.path.exists(first_date_file):
                with open(first_date_file, "w") as f:
                    f.write(first_date_text)
                print(f"{first_date_file} を作成しました。")
            """
            # 両方のファイルが存在する場合、日付の比較
            if os.path.exists(last_date_file):

                with open(last_date_file, "r") as f:
                    last_date = datetime.strptime(f.read().strip(), "%Y/%m/%d")
                first_date = datetime.strptime(first_date_text,'%Y/%m/%d')

                if last_date < first_date:
                    flag = True
                    with open(last_date_file, "w") as f:
                        f.write(last_date_text)
                    print("ファイルの内容を更新しました。")

        return flag

    def save_to_pickle(data, file_path):
        """データをpickleファイルに保存する"""
        with open(file_path, 'wb') as file:
            pickle.dump(data, file)
        print(f"Data successfully saved to {file_path}")

    def url_select(dai_num, year, month, day):
        target_url = f'https://cosmojapan.pt.teramoba2.com/obu/standgraph/?rack_no={dai_num}&dai_hall_id=2648&target_date={year}-{month}-{day}'
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
        pickle_file_path = f'scraped_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
        page.get("https://www.google.co.jp/")
        page.get(url_select(606, yesterday.year, yesterday.month, yesterday.day))
        sleep(3)
        # 「同意する」ボタンをクリック
        doui_button()
        #674-1386
        ranges = [
            range(601, 640),
            range(650, 690),
            range(700, 721),
            range(756, 790),
            range(800, 840),
            range(850, 851),
            range(1731, 1740),
            range(1750, 1753),
            range(1886, 1890),
            range(2000, 2021),
            range(2116, 2140),
            range(2150, 2151),
        ]
        break_flag = False
        for i in chain(*ranges):
            page.get(url_select(i, yesterday.year, yesterday.month, yesterday.day))
            sleep(2)
            if not page.eles('css:#sel_target_date > option'):
                page.refresh()
                print("ページをリフレッシュしました。1")
                doui_button()
                continue
            kaisu = len(page.eles('css:#sel_target_date > option')) - 1
            kaisu = 1
            last_date = page.ele(f'css:#sel_target_date > option:nth-child(2)')
            try:
                if last_date:
                    last_date_text = last_date.text
            except:
                pass
            first_date = page.ele(f'css:#sel_target_date > option:nth-child(3)')
            try:
                if first_date:
                    first_date_text = first_date.text
            except:
                pass
            try:
                flag = check_and_write_dates(last_date_text, first_date_text, flag)
                if (last_date_text and first_date_text) and not flag:
                    break_flag = True
                    print("この範囲のデータはすでに取得しています")
                    break
            except:
                continue
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
                    page.refresh()
                    print("ページをリフレッシュしました。2")
                    doui_button()
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
                    start = page.eles('css:tr.winlist td:nth-child(3), tr.winlistcollar td:nth-child(3)', timeout=3).get.texts()
                    dedama = page.eles('css:tr.winlist td:nth-child(4), tr.winlistcollar td:nth-child(4)', timeout=1).get.texts()
                    shubetu = page.eles('css:tr.winlist td:nth-child(5), tr.winlistcollar td:nth-child(5)', timeout=1).get.texts()
                    path = page.ele('css:#sequence_graph-block > section > div > div.graph-container > div.box > div > svg > g.path-slump > path').attr('d')
                    print(path)
                    second_line = int(page.ele('@fill=MediumSpringGreen').child(3).attr('y')) - 0.5
                    second_line_digit = page.ele('@fill=MediumSpringGreen').child(3).text
                    second_line_digit = int(second_line_digit.replace(",", ""))
                    final_start = int(page.ele('css:#contents-container > article > section.box-base.machine-info > div.box-article01 > div.banBox.digitPanel > div.tables.doubleBox.topBorder > div.left.start > div > div.daidigit.num.m.green').text)
                    csfb_list = cal_samai_from_bonus_history(start, dedama, kishumei, final_start, path, shubetu, second_line_digit, second_line)
                    m_csfb_list = m_cal_samai_from_bonus_history(start, dedama, kishumei, final_start, path, shubetu, second_line_digit, second_line)
                    M_csfb_list = M_cal_samai_from_bonus_history(start, dedama, kishumei, final_start, path, shubetu, second_line_digit, second_line)
                    kaitensuu = csfb_list[0]
                    sadama = csfb_list[1]
                    kitaichi = csfb_list[2]
                    m_kaitensuu = m_csfb_list[0]
                    m_kitaichi = m_csfb_list[2]
                    M_kaitensuu = M_csfb_list[0]
                    M_kitaichi = M_csfb_list[2]
                    start_sum = int(page.ele("css:#contents-container > article > section.box-base.machine-info > div.box-article01 > div.banBox.digitPanel > div.tables.doubleBox.topBorder > div.right.soukaiten.start_boxheight_pachi > div > div.daidigit.num.m.green.data-soukaiten").text)
                    print(f"総回転数：{start_sum}")
                except Exception as e:
                    print(f"Error extracting win list or dedama: {e}")
                    continue  # 勝ちリストや出玉取得時にエラーが発生した場合、次のループに進む

                try:
                    all_scraped_data.append([date, kishumei, dai_num, m_kaitensuu, kaitensuu, M_kaitensuu, sadama, m_kitaichi, kitaichi, M_kitaichi, start_sum])
                except Exception as e:
                    print(f"Error appending data to all_scraped_data: {e}")
                # ピクルファイルに保存
                try:
                    save_to_pickle(all_scraped_data, pickle_file_path)
                except Exception as e:
                    print(f"Error saving data to pickle: {e}")
        page.close()
        if break_flag:
            print("この範囲のデータはすでに取得しています")
        if not break_flag:
            if pickle_file_path:
                # 選択されたファイルを開いて読み込む
                with open(pickle_file_path, 'rb') as f:
                    data_list = pickle.load(f)
            data_list = flatten_list(data_list)
            print(data_list)

            chunk_size = 11  # 1行あたりの列数
            num_chunks = (len(data_list) + chunk_size - 1) // chunk_size  # 切り上げ

            # パディングを行ってチャンクのサイズを揃える
            data_list_2d = [data_list[i * chunk_size: (i + 1) * chunk_size] for i in range(num_chunks)]

            # 最後のチャンクが満たない場合、パディング
            if len(data_list_2d[-1]) < chunk_size:
                data_list_2d[-1].extend([None] * (chunk_size - len(data_list_2d[-1])))

            # NumPy 配列に変換する
            data_array = np.array(data_list_2d, dtype=object)

            # Pandas DataFrameに変換してカラム名を設定
            column_names = ["日付", "機種名", "台番号", "最小回転率", "回転率", "最大回転率", "差玉", "最小ボーダー差分", "ボーダー差分", "最大ボーダー差分", "総回転数"]
            df = pd.DataFrame(data_array, columns=column_names)
            df = df.fillna('')
            df = remove_outliers(df, "ボーダー差分")
            store_name = "コスモ大府"
            # CSVファイルに書き出し
            filename = f"P_sadamadata{store_name}.csv"
            if os.path.exists(filename):
                df2 = pd.read_csv(filename)

                # 列名が一致する場合のみ結合
                if df2.columns.tolist() == column_names:
                    df = pd.concat([df2, df], ignore_index=True)
                    print("ファイルが存在し、列名が一致したため結合しました。")
                else:
                    print("ファイルが存在しますが、列名が一致しないためスキップしました。")
            else:
                print("ファイルが存在しないため、新規作成します。")
            df = df.drop_duplicates()
            df.to_csv(filename, index=False, encoding="utf-8_sig")
            print(f"データを {filename} に保存しました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        # エラー音を鳴らす
        winsound.Beep(1000, 500)
try:
    main()
except Exception as e:
    print(f"最終的に失敗しました: {e}")