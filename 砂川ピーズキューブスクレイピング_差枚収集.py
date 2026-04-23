import random

import pandas as pd

from 出玉履歴から差枚計算 import cal_samai_from_bonus_history
import psutil
from DrissionPage import ChromiumPage, ChromiumOptions
from DrissionPage.errors import ElementLostError
from time import sleep
from itertools import cycle
import pickle
from datetime import datetime, timedelta
import re  # 曜日を削除するために正規表現を使用
from DrissionPage.common import Settings
import signal
import os

Settings.set_language('en')
#リンク先のスクレイピングでは要素がロードされるまで待たせる必要があるかも
proxy_list = [
    "http://203.99.240.179:80",
    "http://91.193.58.1:80",
    "http://203.99.240.182:80",
    "http://133.18.234.13:80",
]

def set_proxy(proxy):
    co.set_argument(f'{proxy}')
    print(f"Using proxy: {proxy}")

def wait_for_elements(selector, timeout=10):
    for _ in range(timeout):
        elements = page.eles(f'css:{selector}')
        if elements:
            return elements
        sleep(1)
    raise TimeoutError("Elements did not load within the specified timeout.")
def get_all_text(cells):
    all_text = []
    all_text = [cell.text.strip() for cell in cells if cell.text.strip()]
    #print(all_text)
    return all_text

def save_to_pickle(data, file_path):
    """データをpickleファイルに保存する"""
    with open(file_path, 'wb') as file:
        pickle.dump(data, file)
    print(f"Data successfully saved to {file_path}")
def extract_date_without_weekday(text):
    """日付部分のみを抽出してdatetime形式に変換"""
    try:
        # 正規表現で 'YYYY/MM/DD' 部分を抽出
        date_match = re.search(r'\d{4}/\d{2}/\d{2}', text)
        if date_match:
            return datetime.strptime(date_match.group(), '%Y/%m/%d')
        return None
    except ValueError:
        return None

def is_within_date_range(link_text, start_date, end_date):
    """リンクテキストの日付が指定した範囲内にあるかを確認する"""
    link_date = extract_date_without_weekday(link_text)
    if link_date:
        return start_date <= link_date <= end_date
    return False


def cal_samai(max_mochidama, path):
    """
    修正後のY座標に基づいてaとsamaiを計算する関数。

    Args:
        max_mochidama (float): 最大持ち玉の値。
        path (str): SVG pathデータ。

    Returns:
        dict: a, samai, samaiの比率を含む辞書。
    """
    # SVGのpathデータから座標を抽出
    points = re.findall(r"([0-9.]+),([0-9.]+)", path)
    points = [(float(x), float(y)) for x, y in points]

    # 初期基線と反転調整
    baseline_y = points[0][1]
    adjusted_points = [(x, baseline_y - y) for x, y in points]

    min_my = adjusted_points[0][1]
    min_my_index = adjusted_points[0][0]
    max_my = 0
    max_my_index = None
    # 最低差枚数から最大差枚数への差を計算
    for i in range(1, len(adjusted_points)):
        if adjusted_points[i][1] < min_my:
            # 新しい最低差枚数が見つかれば更新
            min_my = adjusted_points[i][1]
            min_my_index = adjusted_points[i][0]
        else:
            # 最低差枚数からの差分を計算
            current_max_my = adjusted_points[i][1] - min_my
            if current_max_my > max_my:
                max_my = current_max_my
                max_my_index = adjusted_points[i][0]

    # 最終差枚数
    final_my = adjusted_points[-1][1]


    # aとsamaiの計算
    samai = (max_mochidama / max_my) * final_my
    return samai

def url_select(dai_num, year, month, day):
    target_url = f'https://ogiya.pt.teramoba2.com/handa/standgraph/?rack_no={dai_num}&dai_hall_id=2292&target_date={year}-{month}-{day}'
    return target_url
def doui_button():
    doui_button = page.ele("@id=submittos")
    if doui_button:
        doui_button.click()


co = ChromiumOptions()
path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
#co.set_browser_path(path).save()
set_proxy(random.choice(proxy_list))
#co.set_argument('--no-sandbox')  # 无沙盒模式
#co.add_extension(r"C:\Users\mikih\Downloads\AdBlock")
page = ChromiumPage(addr_or_opts=co)
page.get("https://www.google.co.jp/")
page.get("https://www.pscube.jp/dedamajyoho-P-townDMMpachi/c733209/cgi-bin/nc-v03-001.php?cd_ps=2&bai=20")
sleep(3)
previous_height = 0
while True:
    page.scroll.to_bottom()
    sleep(5)
    current_height = page.rect.size
    if current_height == previous_height:
        break
    previous_height = current_height
kishu_links = [ele.link for ele in page.eles('css:ul#ulKI > li > a')]
for link in kishu_links:
    page.get(link)
    sleep(3)
    print("リンク先に飛びました")
    #ここから機種ごとにスクレイピング
    try:
        daiban_links = [ele.link for ele in page.eles('@class=inner nc-text-align-right btn-dai')]
        for link in daiban_links:
            page.get(link)
            sleep(1)
            page.scroll.to_bottom()
            parents = page.eles('css:ul.nc-listview.nc-shadow.nc-mB-1p0.nc-svg-chart')
            points = []
            try:
                while page.ele('@class=nc-relative nc-btn'):
                    page.ele('@class=nc-relative nc-btn').click()
                    sleep(1)
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
            try:
                table_list = page.eles('@style=display: table-row;').get.texts()
                table_list = table_list[::-1]
                table_list = [entry.replace('\t', ',') for entry in table_list]
                split_data = [table_list[i:i + len(table_list) // 4] for i in
                              range(0, len(table_list), len(table_list) // 4)]
                b_his_df = pd.DataFrame(split_data).T
                b_his_df.columns = ['何回目の当たり', '時刻', '当たりG数', '当たり種別']
                #リセ据え判別コード
                #空き時間判別コード
                first_hit_g = int(b_his_df[b_his_df['何回目の当たり'] == 1]['当たりG数'].iloc[0])
                print(first_hit_g)
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
            try:
                for parent in parents:
                    # 子要素 `g.amcharts-graph-line.amcharts-graph-g1` を取得
                    child_groups = parent.eles('css:g.amcharts-graph-line.amcharts-graph-g1')

                    # 各 `g` 要素の子要素の `transform` を取得
                    for group in child_groups:
                        circles = group.eles('circle')  # `circle` 要素を取得
                        for circle in circles:
                            transform = circle.attr('transform')  # `transform` 属性を取得
                            if transform:
                                # 正規表現で座標 (x, y) を抽出
                                match = re.search(r"translate\(([-\d.]+),\s*([-\d.]+)\)", transform)
                                if match:
                                    x, y = map(float, match.groups())
                                    points.append((x, y))  # (-y, x) に変換して格納
                                    if points:
                                        base_y = points[0][1]  # 最初の (x, y) ペアの y 座標
                                        points = [(x, base_y - y) for x, y in points]
                    ele = parent.ele('@text-anchor=end')
                    axis_point = ele.attr('transform')
                    base_y = points[0][1]  # 最初の (x, y) ペアの y 座標
                    axis_y = base_y - axis_point[1]
                    final_y = points[-1][1]
                    match = re.search(r"translate\(-?\d+,\s*(-?\d+)\)", axis_point)
                    if match:
                        y_value = int(match.group(1))
                    axis_int = int(ele.text)
                    samai = axis_int*int(final_y)/int(axis_y)
                    print(samai)


            except Exception as e:
                print(f"An unexpected error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
links = []
yesterday = datetime.now() - timedelta(days=1)
all_scraped_data = []  # 全データを保存するリスト
pickle_file_path = f'scraped_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
#kaisu = int(input("取得する日数を選択してください。（昨日含めて何日分か,最大６）"))
kaisu = 6
#674-1386
for i in range(674, 1386):
    #page.get(url_select(i, yesterday.year, yesterday.month, yesterday.day))
    for d in range(kaisu):
        doui_button()
        select_date = page.ele(f'css:#sel_target_date > option:nth-child({d + 2})')
        select_date.click()
        date = select_date.text
        kishumei = page.ele('css:div.st01.title.wrap-machine-name > span').text
        dai_num = i
        #max_mochidama = int(page.ele('css:div.daidigit.num.ss.data-max-mochidama').text)
        #path = page.ele('css:#sequence_graph-block > section > div > div.graph-container > div.box > div > svg > g.path-slump > path')
        #path_text = path.attr('d')
        ichiran = page.ele('css:#bonus_history_v2-block > section > div > div.control-button-group > div:nth-child(2) > a')
        ichiran.click()
        tuduki = page.ele('css:#bonus_history_v2-block > section > div > div.graph-container.box > div:nth-child(1) > div > div > div.table-list > div > div > a')
        if tuduki:
            tuduki.click()
        start = page.eles('css:tr.winlist td:nth-child(3), tr.winlistcollar td:nth-child(3)')
        dedama = page.eles('css:tr.winlist td:nth-child(4), tr.winlistcollar td:nth-child(4)')
        final_start = page.ele('css:#contents-container > article > section.box-base.machine-info > div.box-article01 > div.banBox.digitPanel > div.tables.doubleBox.topBorder.dailist_boxheight_slot > div.left.start > div > div.daidigit.num.s.green').text
        samai = cal_samai_from_bonus_history(start, dedama, kishumei, final_start)
        date_pulldown = page.ele('css:#sel_target_date')
        date_pulldown.click()



try:
    selector = 'div.table-row > div.table-data-cell > a'  # <div class="table-row"> を基準
    links = wait_for_elements(selector)
    print(f"Total links found: {len(links)}")
    index = 0
    all_scraped_data = []  # 全データを保存するリスト
    pickle_file_path = f'scraped_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
    update_interval = 5  # 更新間隔
    processed_count = 0  # 処理済みリンクのカウント
    for i in range(len(links)):
        # インデックスを指定してクリック（例: 上から3番目のリンク）
        # 上から3番目の要素（0-based index）
        """
        if i > 0 and i % 1 == 0:  # 例: 5リクエストごとにプロキシを変更
            print("Switching proxy...")
            page.close()  # 現在のページを閉じる
            set_proxy(next(proxy_cycle))  # 次のプロキシを設定
            page = ChromiumPage(addr_or_opts=co)  # 新しいページを開始
            sleep(2)
            page.get(base_url)  # 元のページに戻る
            sleep(2)
        """
        if index < len(links):
            link = links[index]
            link_text = link.text.strip()
            date_text = re.sub(r'\(\S+\)', '', link_text)
            weekday_text = re.search(r'(\(|（)(.)(\)|）)', link_text).group(2)
            if not is_within_date_range(link_text, start_date, end_date):
                print(f"Skipping link: {link_text} (not within date range)")
                index = index + 1
                continue
            print(f"Clicking link: {link.text.strip()} -> {link.attr('href')}")
            link.click()  # 要素をクリック
            sleep(2)
            print(f"Page title after click: {page.title}")
            #以下にスクレイピングを記述
            page.ele('#all_data_btn').click()
            selector2 = 'table#all_data_table > tbody > tr > td'
            elements2 = wait_for_elements(selector2)
            scraped_data = get_all_text(elements2)
            scraped_data = insert_text_in_list(scraped_data, date_text, weekday_text)
            print(scraped_data)
            all_scraped_data.append(scraped_data)
            page.get(base_url)
            links = wait_for_elements(selector)
            processed_count += 1
            save_to_pickle(all_scraped_data, pickle_file_path)
        else:
            print(f"Index {index} is out of range. Total links: {len(links)}")
        index = index + 1


except TimeoutError as e:
    print(f"Error: {e}")
except ElementLostError as e:
    print(f"ElementLostError: {e}")
except Exception as e:
  print(f"An unexpected error occurred: {e}")
finally:
    # ページを閉じる
    page.close()
