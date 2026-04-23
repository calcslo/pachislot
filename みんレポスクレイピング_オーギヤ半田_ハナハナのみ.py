import pickle
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin
from urllib.parse import unquote


def save_to_pickle(data, file_path):
    """データをpickleファイルに保存する"""
    with open(file_path, 'wb') as file:
        pickle.dump(data, file)
    print(f"Data successfully saved to {file_path}")
def scraping_from_minrepo(start_date, end_date):
    start_date = datetime.strptime(start_date, '%Y/%m/%d')
    end_date = datetime.strptime(end_date, '%Y/%m/%d')
    url = 'https://min-repo.com/tag/%E3%82%AA%E3%83%BC%E3%82%AE%E3%83%A4%E3%82%BF%E3%82%A6%E3%83%B3%E5%8D%8A%E7%94%B0%E5%BA%97/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    proxies = {
        "http": "http://localhost:8118",
        "https": "http://localhost:8118",
    }
    pickle_file_path = f'scraped_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
    try:
        response = requests.get(url, proxies=proxies, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, 'html.parser')

        today = datetime.today()
        three_months_ago = today - timedelta(days=90)
        #three_months_ago = datetime.strptime(input("YYYY/MM/DDで開始日付を入力："), '%Y/%m/%d')
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
                # 今日より未来なら去年にする
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

        print(f"直近3か月以内のリンク数: {len(valid_links)}")
        for text, link in valid_links:
            print(f"{text}: {link}")
        td_text_list = []
        for i in range(len(valid_links)):
            link = valid_links[i][1]
            match = re.search(r'https://min-repo\.com/(\d+)/', link)
            article_id = match.group(1)
            if match:
                kishu_values = [
                    '%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%83%8F%E3%83%8A%E3%83%8F%E3%83%8A%EF%BD%9E%E9%96%83%E5%85%89%EF%BD%9E%E2%80%9030',
                    '%E3%82%B8%E3%83%A3%E3%82%B0%E3%83%A9%E3%83%BC%E3%82%AC%E3%83%BC%E3%83%AB%E3%82%BASS',
                    "%E3%82%A6%E3%83%AB%E3%83%88%E3%83%A9%E3%83%9F%E3%83%A9%E3%82%AF%E3%83%AB%E3%82%B8%E3%83%A3%E3%82%B0%E3%83%A9%E3%83%BC",
                    "%E3%83%9F%E3%82%B9%E3%82%BF%E3%83%BC%E3%82%B8%E3%83%A3%E3%82%B0%E3%83%A9%E3%83%BC",
                    "%E3%82%B4%E3%83%BC%E3%82%B4%E3%83%BC%E3%82%B8%E3%83%A3%E3%82%B0%E3%83%A9%E3%83%BC%EF%BC%93"
                ]
                links = [f'https://min-repo.com/{article_id}/?kishu={kishu}' for kishu in kishu_values]
            else:
                continue
            for link in links:
                kishu_param = link.split('?kishu=')[-1]  # kishuの部分だけ取り出す
                kishumei = unquote(kishu_param)  # URLデコードしてkishumeiに代入
                print(kishumei)

                link_text = valid_links[i][0]
                today = datetime.today()
                parsed_date = None
                date_text = re.sub(r'\(\S+\)', '', link_text)
                year_match = re.match(r'^\d{4}/\d{1,2}/\d{1,2}$', date_text)
                try:
                    if year_match:
                        parsed_date = datetime.strptime(date_text, "%Y/%m/%d")
                    else:
                        # 年がない → 今年を付けて補完
                        parsed_date = datetime.strptime(f"{today.year}/{date_text}", "%Y/%m/%d")
                        # 今日より未来なら前年とみなす
                        if parsed_date > today:
                            parsed_date = datetime(today.year - 1, parsed_date.month, parsed_date.day)

                    date_text = parsed_date.strftime("%Y/%m/%d")
                except ValueError:
                    print(f"日付変換エラー: {date_text}")
                    date_text = None
                    continue
                weekday_text = re.search(r'(\(|（)(.)(\)|）)', link_text).group(2)
                try:
                    response = requests.get(link, proxies=proxies, headers=headers, timeout=10)
                    soup = BeautifulSoup(response.text, 'html.parser')


                    # tab_content クラスで style="block" のdivを全て取得
                    target_divs = soup.find_all('div', class_='tab_content')
                    for div in target_divs:
                        if div.find_all(class_='slump_list'):
                            print(f"slump_listがありました{div.find_all('slump_list')}")
                            continue
                        if not div.find_all(class_='table_wrap'):
                            print(f"table_wrapがありません{div.find_all('table_wrap')}")
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
                                if text:  # 空テキストは除外したい場合
                                    td_text_list.append(text)
                    save_to_pickle(td_text_list, pickle_file_path)
                    print(td_text_list)

                except Exception as e:
                    print(e)
                    continue


    except requests.exceptions.RequestException as e:
        print(f"リクエストエラーが発生しました: {e}")
    return pickle_file_path

scraping_from_minrepo("2025/07/13", "2025/10/13")