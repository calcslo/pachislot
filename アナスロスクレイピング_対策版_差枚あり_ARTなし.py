import random
from DrissionPage import ChromiumPage, ChromiumOptions
from DrissionPage.errors import ElementLostError
from time import sleep
from itertools import cycle
import pickle
from datetime import datetime
import re  # 曜日を削除するために正規表現を使用
from DrissionPage.common import Settings

Settings.set_language('en')

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

def insert_text_in_list(original_list, text_to_insert, text_to_insert2):
    result = []
    for i in range(0, len(original_list), 9):
        # 10個おきにテキストを挿入
        result.extend(original_list[i:i+9])  # 10個のアイテムを追加
        result.append(text_to_insert)  # テキストを挿入
        result.append(text_to_insert2)
    return result

start_date = datetime.strptime('2024/11/05', '%Y/%m/%d')
end_date = datetime.strptime('2025/02/05', '%Y/%m/%d')
co = ChromiumOptions()
co.set_proxy("http://localhost:8118")
path = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
co.set_browser_path(path).save()
co.no_imgs(True)
co.add_extension(r"D:\ダウンロード\google chrome\AdBlock")
page = ChromiumPage(addr_or_opts=co)
base_url = 'https://ana-slo.com/%E3%83%9B%E3%83%BC%E3%83%AB%E3%83%87%E3%83%BC%E3%82%BF/%E6%84%9B%E7%9F%A5%E7%9C%8C/%E3%82%B3%E3%82%B9%E3%83%A2%E3%82%B8%E3%83%A3%E3%83%91%E3%83%B3%E5%A4%A7%E5%BA%9C%E5%BA%97-%E3%83%87%E3%83%BC%E3%82%BF%E4%B8%80%E8%A6%A7/'
page.get(base_url)
links = []
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
