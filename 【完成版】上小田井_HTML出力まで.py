#やりたいことCSVの入力だけで何かしらの分かりやすいシートで出力する。（直近3カ月）
#集計
#縦割り日付、曜日、xのつく日かつ〇曜日なら？、〇のつく日、ハナハナ平均差枚、平均G数、平均機械割（推定5以上の台番号）、その日までの月間差枚・累計月間差枚、色分けMAP（差枚 ～-1001、-1000～-1、1～1000、1001～2000、2001～,直近3回イベ日で推定6以上の数値（全ての数値が6以上かつ5000回転）は縁取り、イベ日ごと・全体集計）
#台番号末尾（イベ日、全体集計）、島番号ごとの集計（島番号を入れた島図を同時に添付）、角3まで、週番号ごと、その日までの月間差枚、据え置きするかどうか（2連設定6以上率）、ローテーションか（前回のイベ日・同種イベ日に高設定だったものの設定率）、隣が高設定だった場合（同島番号かつ前後の番号）
#前回イベ日（同種・別種）に設定入った箇所の両隣、前日ワースト凹み・ベスト台（10台）、ボーナス回数　→全て差枚の違いで見るそのあと機械学習に入れてもよいかも
#推測情報
#前日までの情報　前日Ｇ数、平均Ｇ数（3か月、1か月、1週間）、高設定か否か（閾値を上げ下げしながら検証、合算、ＲＥＧだけにした場合など）、差枚（連続凹み）、平均差枚（3か月、1か月、1週間）、その日までの月間差枚
#目的変数：差枚、設定6以上の数値になったか
#上小田井メモ
#イベント日と通常日、イベント日の種類ごと、機種ごと、島図全イベント日集計、凹み上げ系（イベント日とイベント日の前日、イベント日と前回イベント日、イベント日と前回同種イベント日）、前回のイベント日で高設定（高差枚）だったかどうか、できるだけ機種ごとに出す
#前回のイベント日で出てた島と今回のイベント日の相関、スライド、並び
import numpy as np
import pandas as pd
from モジュールまとめ_オーギヤ半田_ハナハナ import MyClass
mod = MyClass()
def html_output():
    df = pd.read_csv("3monthsrowdata上小田井.csv", encoding="utf-8")
    df = df[df['機種名'].str.contains("ジャグラー|ハナハナ|北斗")]
    df['日付'] = pd.to_datetime(df['日付'], errors='coerce')

    df0 = df[df["イベント日"] == 1]
    df1 = df[df["イベント日1"] == 1]
    df2 = df[df["イベント日7"] == 1]
    df3 = df[df["イベント日17"] == 1]
    df7 = df[df["イベント日22"] == 1]
    df8 = df[df["イベント日27"] == 1]


    sp = "上小田井島図.xlsx"
    op = r"E:\PycharmProjects\pythonProject\images_k\上小田井島図全体集計.png"
    op0 = r"E:\PycharmProjects\pythonProject\images_k\上小田井島図全イベント日集計.png"
    op1 = r"E:\PycharmProjects\pythonProject\images_k\上小田井島図1日集計.png"
    op2 = r"E:\PycharmProjects\pythonProject\images_k\上小田井島図7日集計.png"
    op3 = r"E:\PycharmProjects\pythonProject\images_k\上小田井島図17日集計.png"
    op4 = r"E:\PycharmProjects\pythonProject\images_k\上小田井島図前回1日高設定箇所.png"
    op5 = r"E:\PycharmProjects\pythonProject\images_k\上小田井島図前回7日高設定箇所.png"
    op6 = r"E:\PycharmProjects\pythonProject\images_k\上小田井島図前回17日高設定箇所.png"
    op7 = r"E:\PycharmProjects\pythonProject\images_k\上小田井島図22日集計.png"
    op8 = r"E:\PycharmProjects\pythonProject\images_k\上小田井島図27日集計.png"
    op9 = r"E:\PycharmProjects\pythonProject\images_k\上小田井島図前回22日高設定箇所.png"
    op10 = r"E:\PycharmProjects\pythonProject\images_k\上小田井島図前回27日高設定箇所.png"

    mod.shimazu(df, sp, op)
    print("島図全体画像を出力しました。")
    mod.shimazu(df0, sp, op0)
    print("島図0画像を出力しました。")
    mod.shimazu(df1, sp, op1)
    print("島図1画像を出力しました。")
    mod.shimazu(df2, sp, op2)
    print("島図2画像を出力しました。")
    mod.shimazu(df3, sp, op3)
    print("島図3画像を出力しました。")
    mod.shimazu(df7, sp, op7)
    print("島図7画像を出力しました。")
    mod.shimazu(df8, sp, op8)
    print("島図8画像を出力しました。")
    #前回のイベント日の高設定箇所縁取り画像
    latest_date = df1["日付"].max()
    df4 = df1[df1["日付"] == latest_date]
    df4 = df4[df4["G数"] >= 5000]
    df4 = df4[df4["推定高設定"] == 1]
    latest_date = df2["日付"].max()
    df5 = df2[df2["日付"] == latest_date]
    df5 = df5[df5["G数"] >= 5000]
    df5 = df5[df5["推定高設定"] == 1]
    latest_date = df3["日付"].max()
    df6 = df3[df3["日付"] == latest_date]
    df6 = df6[df6["G数"] >= 5000]
    df6 = df6[df6["推定高設定"] == 1]
    latest_date = df7["日付"].max()
    df9 = df7[df7["日付"] == latest_date]
    df9 = df9[df9["G数"] >= 5000]
    df9 = df9[df9["推定高設定"] == 1]
    latest_date = df8["日付"].max()
    df10 = df8[df8["日付"] == latest_date]
    df10 = df10[df10["G数"] >= 5000]
    df10 = df10[df10["推定高設定"] == 1]
    mod.grid_setting6(df4, sp, op4)
    print("島図4画像を出力しました。")
    mod.grid_setting6(df5, sp, op5)
    print("島図5画像を出力しました。")
    mod.grid_setting6(df6, sp, op6)
    print("島図6画像を出力しました。")
    mod.grid_setting6(df9, sp, op9)
    print("島図9画像を出力しました。")
    mod.grid_setting6(df10, sp, op10)
    print("島図10画像を出力しました。")

    #日付ごとデータ、ワードに表添付する。全部機種ごと+全体で出す。ワード：月間差枚、曜日ごと差枚、xのつく日差枚、表column=日付、総差枚、平均差枚、出率、平均G数、その日までの月間累計差枚、
    daily_stats = df.groupby(df["日付"])["予測差枚"].agg(["sum", "mean"]).reset_index()
    daily_g_sum = df.groupby("日付")["G数"].sum().reset_index(name="総G数")
    daily_g_mean = df.groupby("日付")["G数"].mean().reset_index(name="平均G数")
    matubi_df = mod.matubi_kentei(df)
    hanahana = df[df["機種名"] == "キングハナハナ-30"].groupby("日付")["予測差枚"].mean().reset_index(name="ハナハナ")
    j_girls = df[df["機種名"] == "ジャグラーガールズSS"].groupby("日付")["予測差枚"].mean().reset_index(name="ガールズ")
    j_gogo = df[df["機種名"] == "ゴーゴージャグラー３"].groupby("日付")["予測差枚"].mean().reset_index(name="ゴーゴー")
    j_miracle = df[df["機種名"] == "ウルトラミラクルジャグラー"].groupby("日付")["予測差枚"].mean().reset_index(name="ミラクル")
    j_mr = df[df["機種名"] == "ミスタージャグラー"].groupby("日付")["予測差枚"].mean().reset_index(name="ミスター")
    j_my = df[df["機種名"] == "マイジャグラーV"].groupby("日付")["予測差枚"].mean().reset_index(name="マイ")
    j_fa = df[df["機種名"] == "ファンキージャグラー２ＫＴ"].groupby("日付")["予測差枚"].mean().reset_index(name="ファンキー")
    j_im = df[df["機種名"] == "SアイムジャグラーＥＸ"].groupby("日付")["予測差枚"].mean().reset_index(name="アイム")
    hokuto = df[df["機種名"] == "Lスマスロ北斗の拳"].groupby("日付")["予測差枚"].mean().reset_index(name="北斗")

    daily_df = daily_stats.rename(columns={"sum": "日別差枚合計", "mean": "日別差枚平均"})
    daily_df = daily_df.iloc[::-1].reset_index(drop=True)
    daily_df["当月累計差枚"] = (daily_df.sort_values("日付")
                                .groupby(daily_df["日付"].dt.to_period("M").astype(str))["日別差枚合計"]
                                .cumsum())

    # 元の順番に戻す
    daily_df = daily_df.sort_values("日付", ascending=False)
    daily_df["前日当月累計差枚"] = (daily_df.groupby(daily_df["日付"].dt.to_period("M"))["当月累計差枚"].shift(-1).fillna(0).astype(int))

    daily_df = daily_df.merge(daily_g_sum, on="日付", how="left")
    daily_df = daily_df.merge(daily_g_mean, on="日付", how="left")
    daily_df = daily_df.merge(matubi_df, on="日付", how="left")
    daily_df = daily_df.merge(hanahana, on="日付", how="left")
    daily_df = daily_df.merge(j_girls, on="日付", how="left")
    daily_df = daily_df.merge(j_gogo, on="日付", how="left")
    daily_df = daily_df.merge(j_miracle, on="日付", how="left")
    daily_df = daily_df.merge(j_mr, on="日付", how="left")
    daily_df = daily_df.merge(j_my, on="日付", how="left")
    daily_df = daily_df.merge(j_fa, on="日付", how="left")
    daily_df = daily_df.merge(j_im, on="日付", how="left")
    daily_df = daily_df.merge(hokuto, on="日付", how="left")
    daily_df["出率"] = daily_df.apply(lambda row: mod.out_ratio(row["総G数"], row["日別差枚合計"]), axis=1)

    daily_df[daily_df.columns.drop(["日付", "出率", "末尾寄せ"])] = daily_df[daily_df.columns.drop(["日付", "出率", "末尾寄せ"])].fillna(0).astype(int)
    daily_df.to_csv("上小田井日別差枚.csv", index=False)
    monthly_stats = (daily_df.groupby(daily_df["日付"].dt.to_period("M"))["日別差枚合計"].sum()).reset_index()
    def color_cells(val):
        if val > 0:
            return 'color: blue'  # 正の値は青
        elif val < 0:
            return 'color: red'  # 負の値は赤
        else:
            return ''  # 0の場合は色なし

    monthly_stats["日付"] = monthly_stats["日付"].dt.strftime('%Y-%m')
    monthly_stats.rename(columns={
        "日付": "月",
        "日別差枚合計": "月別差枚合計"
    }, inplace=True)
    styled_monthly_stats = monthly_stats.style.map(color_cells, subset=["月別差枚合計"])
    monthly_table = styled_monthly_stats.hide().to_html(index=False, escape=False)

    daily_df["日付"] = pd.to_datetime(daily_df["日付"]).dt.strftime('%Y-%m-%d')
    daily_df_no_column = daily_df.drop('前日当月累計差枚', axis=1)

    def style_daily_table(df):
        # スタイル関数の定義
        def highlight_rows(row):
            return ['background-color: #f2f2f2' if i % 2 == 0 else '' for i in range(len(row))]

        # スタイルを適用
        return df.style.apply(highlight_rows, axis=0)

    # daily_tableに交互の灰色背景を追加
    daily_df_no_column = style_daily_table(daily_df_no_column)
    daily_df_no_column = (daily_df_no_column.format({"出率": "{:.3f}"}))
    styled_daily_stats = daily_df_no_column.map(color_cells, subset=["日別差枚合計", "日別差枚平均", "当月累計差枚", "ハナハナ", "ガールズ", "ゴーゴー", "ミラクル", "ミスター", "マイ", "ファンキー", "アイム", '北斗'])
    daily_table = styled_daily_stats.hide().to_html(index=False, escape=False)
    graph_path = r"E:\PycharmProjects\pythonProject\images_k\日別差枚平均.png"
    mod.plot_daily_samai(daily_df, graph_path)


    graph_path_x = r"E:\PycharmProjects\pythonProject\images_k\xのつく日_平均予測差枚.png"
    graph_path_w = r"E:\PycharmProjects\pythonProject\images_k\曜日_平均予測差枚.png"
    mod.x_day(df, graph_path_x)#xのつく日
    mod.weekday(df[df["イベント日"] == 0], graph_path_w)#イベント日をのぞく曜日別
    graph_path_kado = r"E:\PycharmProjects\pythonProject\images_k\角_平均予測差枚.png"
    graph_path_kado_h = r"E:\PycharmProjects\pythonProject\images_kh\角_平均予測差枚.png"
    graph_path_shima = r"E:\PycharmProjects\pythonProject\images_k\島別_平均予測差枚.png"
    graph_path_matubi = r"E:\PycharmProjects\pythonProject\images_k\台番号末尾別_平均予測差枚.png"
    graph_path_matubi_h = r"E:\PycharmProjects\pythonProject\images_kh\台番号末尾別_平均予測差枚.png"
    graph_path_event = r"E:\PycharmProjects\pythonProject\images_k\イベント日通常日別_平均予測差枚.png"
    graph_path_kishumei = r"E:\PycharmProjects\pythonProject\images_k\機種別_平均予測差枚.png"
    graph_path_eventshubetu = r"E:\PycharmProjects\pythonProject\images_k\イベント日種別_平均予測差枚.png"
    graph_path_shimasoukan = r"E:\PycharmProjects\pythonProject\images_kh\島ごと相関係数.png"
    graph_path_hekomi_h = r"E:\PycharmProjects\pythonProject\images_kh\連続凹み日数.png"
    graph_path_hekomi = r"E:\PycharmProjects\pythonProject\images_k\連続凹み日数.png"
    graph_path_rindai_h = r"E:\PycharmProjects\pythonProject\images_kh\隣台推定高設定数.png"
    graph_path_rindai_k = r"E:\PycharmProjects\pythonProject\images_k\隣台推定高設定数.png"
    shima_num_path = r"E:\PycharmProjects\pythonProject\images_k\島番号.png"
    mod.hanyo_shukei(df, "角からの位置", graph_path_kado)
    mod.hanyo_shukei(df[df["機種名"] == "キングハナハナ-30"], "角からの位置", graph_path_kado_h)
    mod.hanyo_shukei(df, "島番号", graph_path_shima)
    mod.hanyo_shukei(df, "台番号末尾", graph_path_matubi)
    mod.hanyo_shukei(df[df["機種名"] == "キングハナハナ-30"], "台番号末尾", graph_path_matubi_h)
    mod.hanyo_shukei(df[df["機種名"] == "キングハナハナ-30"], "連続凹み日数", graph_path_hekomi_h)
    mod.hanyo_shukei(df[df["機種名"] == "キングハナハナ-30"], "隣台推定高設定数", graph_path_rindai_h)
    mod.hanyo_shukei(df, "隣台推定高設定数", graph_path_rindai_k)
    mod.hanyo_shukei(df, "連続凹み日数", graph_path_hekomi)
    mod.hanyo_shukei(df, "イベント日", graph_path_event)
    df['イベント日種別'] = 0
    for day in [1, 7, 17, 22, 27]:
        df.loc[df[f'イベント日{day}'] == 1, 'イベント日種別'] = day
    mod.hanyo_shukei(df, "イベント日種別", graph_path_eventshubetu)
    df = df.drop(["イベント日種別"], axis=1)
    mod.hanyo_shukei(df, "機種名", graph_path_kishumei)
    mod.yuui_kentei(df.loc[(df["イベント日"] == 1) & (df["機種名"] == "キングハナハナ-30")], "前回イベント日島平均差枚", "当日島平均差枚", graph_path_shimasoukan)
    def set_narabi_osc(df):
        cond1 = df['隣台推定高設定数'] >= 1
        cond2 = df['推定高設定'] == 1
        cond3 = df['推定高設定'] == 0
        df['並びorオセロ'] = np.where(cond1 & cond2, 1, np.where(cond1 & cond3, 0, np.nan))
        return df
    ratio = set_narabi_osc(df[df["機種名"] == "キングハナハナ-30"])['並びorオセロ'].value_counts(normalize=True, dropna=True).sort_index()
    ratio_percent = (ratio * 100).round(2).astype(str) + '%'
    narabi_or_osero = ratio_percent.to_frame(name='割合').to_html()


    html_output = f'''
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0"> <!-- スマホ対応 -->
        <title>上小田井差枚データ</title>
        <style>
            .url_selector {{
                margin-bottom: 20px;  /* 画像とテーブルの間にスペースを追加 */
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                border: 1px solid black;
                padding: 8px;
                text-align: center;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            td {{
                background-color: white;
            }}
            td:first-child, th:first-child {{
                background-color: #f2f2f2;
            }}
    
            .table-container {{
                display: flex;  /* 変更点: 横並びを解除して縦並びに変更 */
                flex-wrap: wrap; /* スマホ対応で折り返す */
                justify-content: space-around;  /* 横並びの中で要素を分ける */
                gap: 20px;
                margin-bottom: 40px;  /* テーブルと島図の間にスペースを追加 */
            }}
            .table-wrapper {{
                width: 100%;  /* 横並びで要素の幅を調整 */
                margin-bottom: 20px;  /* 画像とテーブルの間にスペースを追加 */
            }}
            @media (min-width: 768px) {{
                .table-wrapper {{
                    flex: 1 1 48%; /* タブレット以上では横並び */
                }}
            }}
            .image-wrapper img {{
                max-width: 100%;
                height: auto;
                display: block;
    
        </style>
    </head>
    <body>
        <h1>マルハン上小田井 差枚データ</h1>
        <div class="url_selector">
            <a href="kensho_k.html">検証データまとめ</a>
            <a href="hanahana_k.html">ハナハナまとめ</a>
        </div>
        <h2>各月の差枚合計</h2>
        {monthly_table}
        <div class="table-container">
            <div class="table-wrapper">
                <h2>日別差枚データ</h2>
                {daily_table}
            </div>
            <div class="table-wrapper">
                <h2>日別平均差枚の横棒グラフ</h2>
                <img src="./images_k/日別差枚平均.png" alt="日別平均差枚の横棒グラフ" style="max-width: 100%; height: auto;">
            </div>
        </div>
    
        <div class="image-wrapper">
            <h1>島図</h1>
            <h3>全体集計</h3>
            <img src="./images_k/上小田井島図全体集計.png" alt="島図">
            <h3>全イベント日集計</h3>
            <img src="./images_k/上小田井島図全イベント日集計.png" alt="島図">
            <h3>1日集計</h3>
            <img src="./images_k/上小田井島図1日集計.png" alt="島図">
            <h3>7日集計</h3>
            <img src="./images_k/上小田井島図7日集計.png" alt="島図">
            <h3>17日集計</h3>
            <img src="./images_k/上小田井島図17日集計.png" alt="島図">
            <h3>22日集計</h3>
            <img src="./images_k/上小田井島図22日集計.png" alt="島図">
            <h3>27日集計</h3>
            <img src="./images_k/上小田井島図27日集計.png" alt="島図">
            <h3>前回の1日で高設定投入箇所</h3>
            <img src="./images_k/上小田井島図前回1日高設定箇所.png" alt="島図">
            <h3>前回の7日で高設定投入箇所</h3>
            <img src="./images_k/上小田井島図前回7日高設定箇所.png" alt="島図">
            <h3>前回の17日で高設定投入箇所</h3>
            <img src="./images_k/上小田井島図前回17日高設定箇所.png" alt="島図">
            <h3>前回の22日で高設定投入箇所</h3>
            <img src="./images_k/上小田井島図前回22日高設定箇所.png" alt="島図">
            <h3>前回の27日で高設定投入箇所</h3>
            <img src="./images_k/上小田井島図前回27日高設定箇所.png" alt="島図">
        </div>
    </body>
    </html>
    '''
    html_output1 = f'''
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0"> <!-- スマホ対応 -->
        <title>マルハン上小田井　差枚データ</title>
        <style>
            .url_selector {{
                margin-bottom: 20px;  /* 画像とテーブルの間にスペースを追加 */
            }}   
            .image-wrapper img {{
                max-width: 100%;
                display: flex;
                flex-wrap: wrap;
                justify-content: space-around;
                height: auto;
            }}
        </style>
    </head>
    <body>
        <h1>マルハン上小田井 差枚データ</h1>
        <h2>各種集計</h2>
        <div class="url_selector">
            <a href="index_k.html">TOPページへ戻る</a>
        </div>
        <div class="image-wrapper">
            <h3>xのつく日別平均差枚</h3>
            <img src="./images_k/xのつく日_平均予測差枚.png" alt="差枚データ">
            <h3>曜日別平均差枚（特日の影響を考慮し、通常営業日のみの集計）</h3>
            <img src="./images_k/曜日_平均予測差枚.png" alt="差枚データ">
            <h3>角からの位置別平均差枚（0：島中　1：角台　2、3：角2・3）</h3>
            <img src="./images_k/角_平均予測差枚.png" alt="差枚データ">
            <h3>島別平均差枚（対応番号は下記添付）</h3>
            <img src="./images_k/島別_平均予測差枚.png" alt="差枚データ">
            <h3>島番号</h3>
            <img src="./images_k/島番号.png" alt="差枚データ">
            <h3>イベント日通常日別</h3>
            <img src="./images_k/イベント日通常日別_平均予測差枚.png" alt="差枚データ">
            <h3>機種別</h3>
            <img src="./images_k/機種別_平均予測差枚.png" alt="差枚データ">
            <h3>イベント日種別</h3>
            <img src="./images_k/イベント日種別_平均予測差枚.png" alt="差枚データ">
            <h3>台番号末尾別平均差枚</h3>
            <img src="./images_k/台番号末尾別_平均予測差枚.png" alt="差枚データ">
            <h3>連続凹み日数別平均差枚</h3>
            <img src="./images_k/連続凹み日数.png" alt="差枚データ">
            <h3>隣台推定高設定数</h3>
            <img src="./images_k/隣台推定高設定数.png" alt="差枚データ">
        </div>
    </body>
    </html>
    '''
    html_output2 = f'''
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0"> <!-- スマホ対応 -->
            <title>マルハン上小田井　差枚データ</title>
            <style>
                .url_selector {{
                    margin-bottom: 20px;  /* 画像とテーブルの間にスペースを追加 */
                }}   
                .image-wrapper img {{
                    max-width: 100%;
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-around;
                    height: auto;
                }}
            </style>
        </head>
        <body>
            <h1>マルハン上小田井 差枚データ</h1>
            <h2>ハナハナのみ集計</h2>
            <div class="url_selector">
                <a href="index_k.html">TOPページへ戻る</a>
            </div>
            <div class="image-wrapper">
                <h3>角からの位置別平均差枚（0：島中　1：角台　2、3：角2・3）</h3>
                <img src="./images_kh/角_平均予測差枚.png" alt="差枚データ">
                <h3>台番号末尾別平均差枚</h3>
                <img src="./images_kh/台番号末尾別_平均予測差枚.png" alt="差枚データ">
                <h3>あるイベント日とその前回のイベント日の相関係数</h3>
                <img src="./images_kh/島ごと相関係数.png" alt="差枚データ">
                <h3>連続凹み日数別平均差枚</h3>
                <img src="./images_kh/連続凹み日数.png" alt="差枚データ">
                <h3>隣台推定高設定数</h3>
                <img src="./images_kh/隣台推定高設定数.png" alt="差枚データ">
                <h3>並びとオセロの比率（1：並び、0：オセロ）</h3>
                {narabi_or_osero}
            </div>
        </body>
        </html>
        '''
    # HTMLファイルとして保存
    output_path = "index_k.html"
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html_output)
    output_path1 = "kensho_k.html"
    with open(output_path1, "w", encoding="utf-8") as file:
        file.write(html_output1)
    output_path2 = "hanahana_k.html"
    with open(output_path2, "w", encoding="utf-8") as file:
        file.write(html_output2)
    print(f"HTMLファイルとして保存しました: {output_path}")
html_output()
