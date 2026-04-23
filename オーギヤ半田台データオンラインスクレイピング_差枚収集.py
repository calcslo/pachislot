import random
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
import requests
from bs4 import BeautifulSoup
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/537.36",
    "Referer": "https://daidata.goraggio.com/"
}

def get_current_ip(proxy):
    response = requests.get('https://api.ipify.org?format=json', proxies=proxy)
    ip_data = response.json()
    return ip_data['ip']
proxy = {"http": "http://localhost:8118", "https": "http://localhost:8118"}
print(get_current_ip(proxy))
today = datetime.today().strftime("%Y-%m-%d")
url = 'https://daidata.goraggio.com/101297'
api_url = "https://daidata.goraggio.com/api/store/more_list/101297"
session = requests.Session()
response = session.get(url,headers=headers, proxies=proxy)
print("1")
soup = BeautifulSoup(response.text, "html.parser")
agree_button = soup.select_one("#Result-Column > div > nav > ul > li.accept_btn > form > span > button")
if agree_button:
    print("規約ページが表示されました。同意ボタンを押します。")

    # 同意ボタンのフォームを取得
    form = agree_button.find_parent("form")

    if form:
        action_url = form["action"]  # フォームの送信先URL
        payload = {input_tag["name"]: input_tag["value"] for input_tag in
                   form.find_all("input", {"type": "hidden"})}  # 隠し入力値を取得

        # 同意リクエストを送信
        session.post(action_url, data=payload)
        print("規約に同意しました。")

        # 元のページに再アクセス
        response = session.get(url,headers=headers, proxies=proxy)
        soup = BeautifulSoup(response.text, "html.parser")
else:
    print("規約画面が表示されませんでした。")
# スクレイピングしたい要素を取得
params = {
    "targetDate": today,  # 今日の日付
    "ps": "P",
    "page": 1,  # 初回リクエストは1ページ目
    "totaldata": 49,
    "ballPrice": 4.00
}
all_html = ""  # 取得した HTML を格納
prev_html = None  # 前回の HTML を保存
page = 1  # 最初のページ
# ページが変化しなくなるまでリクエストを続ける
while True:
    params["page"] = page
    response = requests.get(api_url, params=params, headers=headers, proxies=proxy)
    print("ボタンを押しました。")
    if response.status_code == 200:
        data = response.json()  # JSONとして取得
        html = data.get("html", "")
        has_next = data.get("hasNext", False)  # 次のページがあるか確認

        print(f"[INFO] ページ {page} のデータ取得成功 ({len(html)} バイト)")

        if not html:
            print(f"[INFO] ページ {page} のHTMLが空のため終了します。")
            break

        all_html += html  # 取得したHTMLを追加

        # `hasNext` が `false` なら終了
        if not has_next:
            print(f"[INFO] hasNext=False のためスクレイピング終了。")
            break

        page += 1  # 次のページへ
    else:
        print(f"[ERROR] ページ {page} でエラー発生: {response.status_code}")
        break
soup = BeautifulSoup(all_html, "html.parser")
href_list = [a["href"] for li in soup.select("li.Pachinko") for a in li.find_all("a", href=True)]
print(href_list)

