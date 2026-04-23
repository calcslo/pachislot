import re
import pandas as pd



def cal_samai_from_bonus_history(start, dedama, machine_name, final_start, path, shubetu, max_mochidama):
    start = [text.replace("-", "0") for text in start]
    start = [int(text) for text in start if text.isdigit()]  # 数字のみ変
    dedama = [text.replace("-", "0") for text in dedama]
    dedama = [int(text) for text in dedama if text.isdigit()]  # 数字のみ変換
    df = pd.DataFrame({
        "スタート": start,
        "出玉": dedama,
        "種別": shubetu
    })
    dict = {"eF.戦姫絶唱ｼﾝﾌｫｷﾞｱ4 F":17.8,
            "eｿｰﾄﾞｱｰﾄ･ｵﾝﾗｲﾝ閃光K7": 16.5,
            "Pにゃんこ大戦争M4": 17.5,
            "e Re:ｾﾞﾛ season2 M13": 16.6,
            "P大海物語5 MTE2": 17.7,
            "P新世ｴｳﾞｧ15未来への咆哮": 17.8,
            "eF.からくりｻｰｶｽ2 R": 18.1,
            "Pまどか☆ﾏｷﾞｶ3 LM3": 17.1,
            "e／押忍番長漢の頂／L09": 17.1,
            }
    decrease_start = 0
    if machine_name == "eF.戦姫絶唱ｼﾝﾌｫｷﾞｱ4 F":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "出玉"] >= 1000 and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                decrease_start += 8
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                decrease_start += 15
        if final_start < 8 and df.loc[len(df) - 1, "出玉"] >= 1000 and df.loc[len(df) - 1, "種別"] == "大当":
            decrease_start += final_start           # 何もしない
        if final_start >= 8 and df.loc[len(df) - 1, "出玉"] >= 1000 and df.loc[len(df) - 1, "種別"] == "大当":
            decrease_start += 8            # 何もしない
        if final_start < 15 and df.loc[len(df) - 1, "種別"] == "確変":
            decrease_start += final_start
        if final_start >= 15 and df.loc[len(df) - 1, "種別"] == "確変":
            decrease_start += 15
    if machine_name == "eｿｰﾄﾞｱｰﾄ･ｵﾝﾗｲﾝ閃光K7":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "出玉"] <= 500 and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 35:
                    decrease_start += df.loc[i + 1, "スタート"]
                else:
                    decrease_start += 35
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":#おかしい
                last_big_win_idx = df.loc[:i, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
                if last_big_win_idx is not None:
                    has_large_start = (df.loc[last_big_win_idx:i, "スタート"] >= 51).any()
                    if has_large_start:
                        if df.loc[i + 1, "スタート"] <= 115:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > 115:
                            decrease_start += 115
                    else:
                        if df.loc[i + 1, "スタート"] <= 50:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > 50:
                            decrease_start += 50
        if df.loc[len(df) - 1, "出玉"] <= 500 and df.loc[len(df) - 1, "種別"] == "大当":
            if final_start <= 35:
                decrease_start += final_start
            elif final_start > 35:
                decrease_start += 35
        if df.loc[len(df) - 1, "種別"] == "確変":
            last_big_win_idx = df.loc[:len(df) - 1, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
            if last_big_win_idx is not None:
                has_large_start = (df.loc[last_big_win_idx:len(df) - 1, "スタート"] >= 51).any()
                if has_large_start:
                    if final_start <= 115:
                        decrease_start += final_start
                    if final_start > 115:
                        decrease_start += 115
                else:
                    if final_start <= 50:
                        decrease_start += final_start
                    if final_start > 50:
                        decrease_start += 50
    if machine_name == "Pにゃんこ大戦争M4":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] >= 155:
                    decrease_start += 155
                if df.loc[i + 1, "スタート"] < 155:
                    decrease_start += df.loc[i + 1, "スタート"]
        if final_start < 155 and df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 155:
                decrease_start += final_start
            elif final_start > 155:
                decrease_start += 155
    if machine_name == "e Re:ｾﾞﾛ season2 M13":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "出玉"] >= 1800 and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                decrease_start += 145
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                decrease_start += 145
        if final_start < 145 and df.loc[len(df) - 1, "出玉"] >= 1800 and df.loc[len(df) - 1, "種別"] == "大当":
            decrease_start += final_start
        if final_start > 145 and df.loc[len(df) - 1, "種別"] == "確変":
            decrease_start += 145
    if machine_name == "P大海物語5 MTE2":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 100:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 100:
                    decrease_start += 100
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 100:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 100:
                    decrease_start += 100
        if final_start < 100:
            decrease_start += final_start
        if final_start > 100:
            decrease_start += 100
    if machine_name == "P新世ｴｳﾞｧ15未来への咆哮":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 135:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 135:
                    decrease_start += 135
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 163:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 163:
                    decrease_start += 163
        if df.loc[len(df) - 1, "種別"] == "大当":
            if final_start <= 135:
                decrease_start += final_start
            if final_start > 135:
                decrease_start += 135
        if df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 163:
                decrease_start += final_start
            if final_start > 163:
                decrease_start += 163
    if machine_name == "eF.からくりｻｰｶｽ2 R":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当" and df.loc[i, "出玉"] >= 1000:#駆け抜け
                if df.loc[i + 1, "スタート"] <= 70:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 70:
                    decrease_start += 70
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 135:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 135:
                    decrease_start += 135
        if df.loc[len(df) - 1, "種別"] == "大当"and df.loc[len(df) - 1, "出玉"] >= 1000:
            if final_start <= 70:
                decrease_start += final_start
            if final_start > 70:
                decrease_start += 70
        if df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 135:
                decrease_start += final_start
            if final_start > 135:
                decrease_start += 135
    if machine_name == "Pまどか☆ﾏｷﾞｶ3 LM3":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当" and df.loc[i, "出玉"] <= 1000:#駆け抜け
                if df.loc[i + 1, "スタート"] <= 33:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 33:
                    decrease_start += 33
            elif df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当" and df.loc[i, "出玉"] >= 1000:#駆け抜け
                if df.loc[i + 1, "スタート"] <= 120:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 120:
                    decrease_start += 120
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                last_big_win_idx = df.loc[:i, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
                if last_big_win_idx is not None:
                    has_large_start = (df.loc[last_big_win_idx:i, "スタート"] >= 61).any()
                    if has_large_start:
                        if df.loc[i + 1, "スタート"] <= 120:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > 120:
                            decrease_start += 120
                    else:
                        if df.loc[i + 1, "スタート"] <= 60:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > 60:
                            decrease_start += 60
        if df.loc[len(df) - 1, "種別"] == "大当" and df.loc[len(df) - 1, "出玉"] <= 1000:
            if final_start <= 33:
                decrease_start += final_start
            if final_start > 33:
                decrease_start += 33
        if df.loc[len(df) - 1, "種別"] == "大当" and df.loc[len(df) - 1, "出玉"] >= 1000:
            if final_start <= 120:
                decrease_start += final_start
            if final_start > 120:
                decrease_start += 120
        if df.loc[len(df) - 1, "種別"] == "確変":
            last_big_win_idx = df.loc[:len(df) - 1, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
            if last_big_win_idx is not None:
                has_large_start = (df.loc[last_big_win_idx:len(df) - 1, "スタート"] >= 61).any()
                if has_large_start:
                    if final_start <= 120:
                        decrease_start += final_start
                    if final_start > 120:
                        decrease_start += 120
                else:
                    if final_start <= 60:
                        decrease_start += final_start
                    if final_start > 60:
                        decrease_start += 60
    if machine_name == "e／押忍番長漢の頂／L09":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":#駆け抜け
                if df.loc[i + 1, "スタート"] <= 39:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 39:
                    decrease_start += 39
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 157:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 157:
                    decrease_start += 157
        if df.loc[len(df) - 1, "種別"] == "大当":
            if final_start <= 39:
                decrease_start += final_start
            if final_start > 39:
                decrease_start += 39
        if df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 157:
                decrease_start += final_start
            if final_start > 157:
                decrease_start += 157
    """
    if machine_name == "PA大海物語5 ARBC":#一回でも10Rとってたら時短120、648個で50回、432個で30:6で25回、50回　未完
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 135:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 135:
                    decrease_start += 135
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 163:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 163:
                    decrease_start += 163
        if df.loc[len(df) - 1, "種別"] == "大当":
            if final_start <= 135:
                decrease_start += final_start
            if final_start > 135:
                decrease_start += 135
        if df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 163:
                decrease_start += final_start
            if final_start > 163:
                decrease_start += 163
    """
    nomal_start = df[df["種別"] == "大当"]["スタート"].sum() - decrease_start + final_start
    print(nomal_start)
    special_start = df[df["種別"] == "確変"]["スタート"].sum() + decrease_start
    dedama_sum = df["出玉"].sum()
    saishusadama = cal_samai(path, max_mochidama)[0]
    print(f"最終差玉:{saishusadama}")
    kaitensuu = nomal_start*250/(dedama_sum - saishusadama - special_start*0.1)
    print(f"回転数:{kaitensuu}")
    if machine_name in dict:
        kitaichi = kaitensuu - dict[machine_name] if kaitensuu is not None else None
    else:
        kaitensuu = None
        kitaichi = None
    print(f"ボーダー差分:{kitaichi}")
    return kaitensuu, saishusadama, kitaichi, nomal_start

def m_cal_samai_from_bonus_history(start, dedama, machine_name, final_start, path, shubetu, max_mochidama):#　通常回転数を引けるだけ引く
    start = [text.replace("-", "0") for text in start]
    start = [int(text) for text in start if text.isdigit()]  # 数字のみ変
    dedama = [text.replace("-", "0") for text in dedama]
    dedama = [int(text) for text in dedama if text.isdigit()]  # 数字のみ変換
    df = pd.DataFrame({
        "スタート": start,
        "出玉": dedama,
        "種別": shubetu
    })
    dict = {"eF.戦姫絶唱ｼﾝﾌｫｷﾞｱ4 F":17.8,
            "eｿｰﾄﾞｱｰﾄ･ｵﾝﾗｲﾝ閃光K7": 16.5,
            "Pにゃんこ大戦争M4": 17.5,
            "e Re:ｾﾞﾛ season2 M13": 16.6,
            "P大海物語5 MTE2": 17.7,
            "P新世ｴｳﾞｧ15未来への咆哮": 17.8,
            "eF.からくりｻｰｶｽ2 R": 18.1,
            "Pまどか☆ﾏｷﾞｶ3 LM3": 17.1,
            "e／押忍番長漢の頂／L09": 17.1,
            }
    decrease_start = 0
    if machine_name == "eF.戦姫絶唱ｼﾝﾌｫｷﾞｱ4 F":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "出玉"] >= 1000 and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] < 15:
                    decrease_start += final_start
                else:
                    decrease_start += 15
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                decrease_start += 15
        if final_start < 15 and df.loc[len(df) - 1, "出玉"] >= 1000 and df.loc[len(df) - 1, "種別"] == "大当":
            decrease_start += final_start
        if final_start >= 15 and df.loc[len(df) - 1, "出玉"] >= 1000 and df.loc[len(df) - 1, "種別"] == "大当":
            decrease_start += 15
        if final_start < 15 and df.loc[len(df) - 1, "種別"] == "確変":
            decrease_start += final_start
        if final_start >= 15 and df.loc[len(df) - 1, "種別"] == "確変":
            decrease_start += 15
    if machine_name == "eｿｰﾄﾞｱｰﾄ･ｵﾝﾗｲﾝ閃光K7":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "出玉"] <= 500 and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 50:
                    decrease_start += df.loc[i + 1, "スタート"]
                else:
                    decrease_start += 50
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":  # おかしい
                last_big_win_idx = df.loc[:i, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
                if last_big_win_idx is not None:
                    has_large_start = (df.loc[last_big_win_idx:i, "スタート"] >= 51).any()
                    if has_large_start:
                        if df.loc[i + 1, "スタート"] <= 115:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > 115:
                            decrease_start += 115
                    else:
                        if df.loc[i + 1, "スタート"] <= 50:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > 50:
                            decrease_start += 50
        if df.loc[len(df) - 1, "出玉"] <= 500 and df.loc[len(df) - 1, "種別"] == "大当":
            if final_start <= 50:
                decrease_start += final_start
            elif final_start > 50:
                decrease_start += 50
        if df.loc[len(df) - 1, "種別"] == "確変":
            last_big_win_idx = df.loc[:len(df) - 1, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
            if last_big_win_idx is not None:
                has_large_start = (df.loc[last_big_win_idx:len(df) - 1, "スタート"] >= 51).any()
                if has_large_start:
                    if final_start <= 115:
                        decrease_start += final_start
                    if final_start > 115:
                        decrease_start += 115
                else:
                    if final_start <= 50:
                        decrease_start += final_start
                    if final_start > 50:
                        decrease_start += 50
    if machine_name == "Pにゃんこ大戦争M4":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] >= 155:
                    decrease_start += 155
                if df.loc[i + 1, "スタート"] < 155:
                    decrease_start += df.loc[i + 1, "スタート"]
        if final_start < 155 and df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 155:
                decrease_start += final_start
            elif final_start > 155:
                decrease_start += 155
    if machine_name == "e Re:ｾﾞﾛ season2 M13":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "出玉"] >= 1800 and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                decrease_start += 145
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                decrease_start += 145
        if final_start < 145 and df.loc[len(df) - 1, "出玉"] >= 1800 and df.loc[len(df) - 1, "種別"] == "大当":
            decrease_start += final_start
        if final_start > 145 and df.loc[len(df) - 1, "種別"] == "確変":
            decrease_start += 145
    if machine_name == "P大海物語5 MTE2":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 100:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 100:
                    decrease_start += 100
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 100:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 100:
                    decrease_start += 100
        if final_start < 100:
            decrease_start += final_start
        if final_start > 100:
            decrease_start += 100
    if machine_name == "P新世ｴｳﾞｧ15未来への咆哮":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 163:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 163:
                    decrease_start += 163
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 163:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 163:
                    decrease_start += 163
        if df.loc[len(df) - 1, "種別"] == "大当":
            if final_start <= 163:
                decrease_start += final_start
            if final_start > 163:
                decrease_start += 163
        if df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 163:
                decrease_start += final_start
            if final_start > 163:
                decrease_start += 163
    if machine_name == "eF.からくりｻｰｶｽ2 R":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当" and df.loc[i, "出玉"] >= 1000:#駆け抜け
                if df.loc[i + 1, "スタート"] <= 135:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 135:
                    decrease_start += 135
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 135:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 135:
                    decrease_start += 135
        if df.loc[len(df) - 1, "種別"] == "大当"and df.loc[len(df) - 1, "出玉"] >= 1000:
            if final_start <= 135:
                decrease_start += final_start
            if final_start > 135:
                decrease_start += 135
        if df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 135:
                decrease_start += final_start
            if final_start > 135:
                decrease_start += 135
    if machine_name == "Pまどか☆ﾏｷﾞｶ3 LM3":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当" and df.loc[i, "出玉"] <= 1000:#駆け抜け
                if df.loc[i + 1, "スタート"] <= 60:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 60:
                    decrease_start += 60
            elif df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当" and df.loc[i, "出玉"] >= 1000:#駆け抜け
                if df.loc[i + 1, "スタート"] <= 120:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 120:
                    decrease_start += 120
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                last_big_win_idx = df.loc[:i, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
                if last_big_win_idx is not None:
                    has_large_start = (df.loc[last_big_win_idx:i, "スタート"] >= 61).any()
                    if has_large_start:
                        if df.loc[i + 1, "スタート"] <= 120:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > 120:
                            decrease_start += 120
                    else:
                        if df.loc[i + 1, "スタート"] <= 60:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > 60:
                            decrease_start += 60
        if df.loc[len(df) - 1, "種別"] == "大当" and df.loc[len(df) - 1, "出玉"] <= 1000:
            if final_start <= 60:
                decrease_start += final_start
            if final_start > 60:
                decrease_start += 60
        if df.loc[len(df) - 1, "種別"] == "大当" and df.loc[len(df) - 1, "出玉"] >= 1000:
            if final_start <= 120:
                decrease_start += final_start
            if final_start > 120:
                decrease_start += 120
        if df.loc[len(df) - 1, "種別"] == "確変":
            last_big_win_idx = df.loc[:len(df) - 1, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
            if last_big_win_idx is not None:
                has_large_start = (df.loc[last_big_win_idx:len(df) - 1, "スタート"] >= 61).any()
                if has_large_start:
                    if final_start <= 120:
                        decrease_start += final_start
                    if final_start > 120:
                        decrease_start += 120
                else:
                    if final_start <= 60:
                        decrease_start += final_start
                    if final_start > 60:
                        decrease_start += 60
    if machine_name == "e／押忍番長漢の頂／L09":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":#駆け抜け
                if df.loc[i + 1, "スタート"] <= 157:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 157:
                    decrease_start += 157
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 157:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 157:
                    decrease_start += 157
        if df.loc[len(df) - 1, "種別"] == "大当":
            if final_start <= 157:
                decrease_start += final_start
            if final_start > 157:
                decrease_start += 157
        if df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 157:
                decrease_start += final_start
            if final_start > 157:
                decrease_start += 157
    """
    if machine_name == "PA大海物語5 ARBC":#一回でも10Rとってたら時短120、648個で50回、432個で30:6で25回、50回　未完
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 135:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 135:
                    decrease_start += 135
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 163:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 163:
                    decrease_start += 163
        if df.loc[len(df) - 1, "種別"] == "大当":
            if final_start <= 135:
                decrease_start += final_start
            if final_start > 135:
                decrease_start += 135
        if df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 163:
                decrease_start += final_start
            if final_start > 163:
                decrease_start += 163
    """
    nomal_start = df[df["種別"] == "大当"]["スタート"].sum() - decrease_start + final_start
    special_start = df[df["種別"] == "確変"]["スタート"].sum() + decrease_start
    dedama_sum = df["出玉"].sum()
    saishusadama = cal_samai(path, max_mochidama)[0]
    kaitensuu = nomal_start*250/(dedama_sum - saishusadama - special_start*0.1)
    print(f"最小回転数:{kaitensuu}")
    if machine_name in dict:
        kitaichi = kaitensuu - dict[machine_name] if kaitensuu is not None else None
    else:
        kaitensuu = None
        kitaichi = None
    print(f"最小ボーダー差分:{kitaichi}")
    return kaitensuu, saishusadama, kitaichi

def M_cal_samai_from_bonus_history(start, dedama, machine_name, final_start, path, shubetu, max_mochidama):
    start = [text.replace("-", "0") for text in start]
    start = [int(text) for text in start if text.isdigit()]  # 数字のみ変
    dedama = [text.replace("-", "0") for text in dedama]
    dedama = [int(text) for text in dedama if text.isdigit()]  # 数字のみ変換
    df = pd.DataFrame({
        "スタート": start,
        "出玉": dedama,
        "種別": shubetu
    })
    dict = {"eF.戦姫絶唱ｼﾝﾌｫｷﾞｱ4 F":17.8,
            "eｿｰﾄﾞｱｰﾄ･ｵﾝﾗｲﾝ閃光K7": 16.5,
            "Pにゃんこ大戦争M4": 17.5,
            "e Re:ｾﾞﾛ season2 M13": 16.6,
            "P大海物語5 MTE2": 17.7,
            "P新世ｴｳﾞｧ15未来への咆哮": 17.8,
            "eF.からくりｻｰｶｽ2 R": 18.1,
            "Pまどか☆ﾏｷﾞｶ3 LM3": 17.1,
            "e／押忍番長漢の頂／L09": 17.1,
            }
    decrease_start = 0
    if machine_name == "eF.戦姫絶唱ｼﾝﾌｫｷﾞｱ4 F":#できるだけ通常回転数を引かない
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] < 15:
                    decrease_start += df.loc[i + 1, "スタート"]
                else:
                    decrease_start += 15
        if final_start < 15 and df.loc[len(df) - 1, "種別"] == "確変":
            decrease_start += final_start
        if final_start >= 15 and df.loc[len(df) - 1, "種別"] == "確変":
            decrease_start += 15
    if machine_name == "eｿｰﾄﾞｱｰﾄ･ｵﾝﾗｲﾝ閃光K7":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                last_big_win_idx = df.loc[:i, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
                if last_big_win_idx is not None:
                    has_large_start = (df.loc[last_big_win_idx:i, "スタート"] >= 51).any()
                    if has_large_start:
                        if df.loc[i + 1, "スタート"] <= 115:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > 115:
                            decrease_start += 115
                    else:
                        if df.loc[i + 1, "スタート"] <= 50:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > 50:
                            decrease_start += 50
        if df.loc[len(df) - 1, "種別"] == "確変":
            last_big_win_idx = df.loc[:len(df) - 1, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
            if last_big_win_idx is not None:
                has_large_start = (df.loc[last_big_win_idx:len(df) - 1, "スタート"] >= 51).any()
                if has_large_start:
                    if final_start <= 115:
                        decrease_start += final_start
                    if final_start > 115:
                        decrease_start += 115
                else:
                    if final_start <= 50:
                        decrease_start += final_start
                    if final_start > 50:
                        decrease_start += 50
    if machine_name == "Pにゃんこ大戦争M4":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] >= 155:
                    decrease_start += 155
                if df.loc[i + 1, "スタート"] < 155:
                    decrease_start += df.loc[i + 1, "スタート"]
        if final_start < 155 and df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 155:
                decrease_start += final_start
            elif final_start > 155:
                decrease_start += 155
    if machine_name == "e Re:ｾﾞﾛ season2 M13":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "出玉"] >= 1800 and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                decrease_start += 145
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                decrease_start += 145
        if final_start < 145 and df.loc[len(df) - 1, "出玉"] >= 1800 and df.loc[len(df) - 1, "種別"] == "大当":
            decrease_start += final_start
        if final_start > 145 and df.loc[len(df) - 1, "種別"] == "確変":
            decrease_start += 145
    if machine_name == "P大海物語5 MTE2":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 100:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 100:
                    decrease_start += 100
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 100:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 100:
                    decrease_start += 100
        if final_start < 100:
            decrease_start += final_start
        if final_start > 100:
            decrease_start += 100
    if machine_name == "P新世ｴｳﾞｧ15未来への咆哮":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 100:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 100:
                    decrease_start += 100
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 163:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 163:
                    decrease_start += 163
        if df.loc[len(df) - 1, "種別"] == "大当":
            if final_start <= 100:
                decrease_start += final_start
            if final_start > 100:
                decrease_start += 100
        if df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 163:
                decrease_start += final_start
            if final_start > 163:
                decrease_start += 163
    if machine_name == "eF.からくりｻｰｶｽ2 R":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 135:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 135:
                    decrease_start += 135
        if df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 135:
                decrease_start += final_start
            if final_start > 135:
                decrease_start += 135
    if machine_name == "Pまどか☆ﾏｷﾞｶ3 LM3":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当" and df.loc[i, "出玉"] >= 1000:#駆け抜け
                if df.loc[i + 1, "スタート"] <= 120:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 120:
                    decrease_start += 120
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                last_big_win_idx = df.loc[:i, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
                if last_big_win_idx is not None:
                    has_large_start = (df.loc[last_big_win_idx:i, "スタート"] >= 61).any()
                    if has_large_start:
                        if df.loc[i + 1, "スタート"] <= 120:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > 120:
                            decrease_start += 120
                    else:
                        if df.loc[i + 1, "スタート"] <= 60:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > 60:
                            decrease_start += 60
        if df.loc[len(df) - 1, "種別"] == "大当" and df.loc[len(df) - 1, "出玉"] >= 1000:
            if final_start <= 120:
                decrease_start += final_start
            if final_start > 120:
                decrease_start += 120
        if df.loc[len(df) - 1, "種別"] == "確変":
            last_big_win_idx = df.loc[:len(df) - 1, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
            if last_big_win_idx is not None:
                has_large_start = (df.loc[last_big_win_idx:len(df) - 1, "スタート"] >= 61).any()
                if has_large_start:
                    if final_start <= 120:
                        decrease_start += final_start
                    if final_start > 120:
                        decrease_start += 120
                else:
                    if final_start <= 60:
                        decrease_start += final_start
                    if final_start > 60:
                        decrease_start += 60
    if machine_name == "e／押忍番長漢の頂／L09":
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 157:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 157:
                    decrease_start += 157
        if df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 157:
                decrease_start += final_start
            if final_start > 157:
                decrease_start += 157
    """
    if machine_name == "PA大海物語5 ARBC":#一回でも10Rとってたら時短120、648個で50回、432個で30:6で25回、50回　未完
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 135:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 135:
                    decrease_start += 135
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= 163:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > 163:
                    decrease_start += 163
        if df.loc[len(df) - 1, "種別"] == "大当":
            if final_start <= 135:
                decrease_start += final_start
            if final_start > 135:
                decrease_start += 135
        if df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= 163:
                decrease_start += final_start
            if final_start > 163:
                decrease_start += 163
    if machine_name == "PAわんわんパラダイスCELEBRATION":
        for i in range(len(df) - 1):
    
    """
    nomal_start = df[df["種別"] == "大当"]["スタート"].sum() - decrease_start + final_start
    special_start = df[df["種別"] == "確変"]["スタート"].sum() + decrease_start
    dedama_sum = df["出玉"].sum()
    saishusadama = cal_samai(path, max_mochidama)[0]
    kaitensuu = nomal_start*250/(dedama_sum - saishusadama - special_start*0.1)
    print(f"最大回転数:{kaitensuu}")
    if machine_name in dict:
        kitaichi = kaitensuu - dict[machine_name] if kaitensuu is not None else None
    else:
        kaitensuu = None
        kitaichi = None
    print(f"最大ボーダー差分:{kitaichi}")
    return kaitensuu, saishusadama, kitaichi

def cal_samai(path, max_mochidama):
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
    if final_my > 0:
        win_flag = True
    else:
        win_flag = False


    # aとsamaiの計算
    #max_my = 0のときの対処が必要
    if max_my == 0:
        samai = None
    else:
        samai = (max_mochidama / max_my) * final_my

    return samai, win_flag
"""
start = ['44', '1', '135', '1', '2', '0', '77', '88', '1', '97', '118', '11', '507', '0', '0', '0', '0', '0', '25', '16', '0', '0', '6', '113']
dedama = ['1560', '1270', '1600', '1270', '1580', '1270', '1430', '1440', '1390', '300', '1410', '290', '1580', '1400', '1340', '1490', '1400', '1300', '1410', '1550', '1430', '1270', '1400', '1410']
machine_name = 'e Re:ｾﾞﾛ season2 M13'
final_start = 144
"""
path = 'M0.50,200.50 L0.50,200.50 L13.50,200.50 L36.50,202.50 L59.50,211.50 L82.50,216.50 L105.50,227.50 L129.50,223.50 L152.50,223.50 L175.50,231.50 L198.50,239.50 L221.50,242.50 L244.50,250.50 L267.50,252.50 L290.50,262.50 L313.50,268.50 L336.50,275.50 L359.50,280.50 L382.50,288.50 L405.50,293.50 L428.50,296.50 L451.50,296.50 L474.50,300.50 L497.50,266.50 L520.50,257.50 L543.50,258.50 L566.50,262.50 L682.50,262.50 L682.50,262.50'
max_mochidama = 11040
print(cal_samai(path, max_mochidama))
"""
second_line = 119.5
second_line_digit = 5000
shubetu = ['大当', '確変', '確変', '確変', '確変', '確変', '確変', '確変', '確変', '確変','確変', '確変', '大当', '確変', '確変', '確変', '確変', '確変', '確変', '確変', '確変', '確変','確変', '確変']
x = cal_samai_from_bonus_history(start, dedama , machine_name, final_start, path, shubetu, max_mochidama)
print(x[0],x[1],x[2])

#STタイプは確変終了後の次のあたりから、ST回数を引く、ボーダー±5から逸脱するものは排除
#にゃんこ確変、大当をそのままOK
#SAO初当たり7割ST50回、3割単発の区別、下位50回、LT115回→一回でも50回を超えたら、次は115回マイナス
#28:30で単発確率の方が高いつまり、24.13回引けばよい（朝1は除く）また、全部単発タイプと全部駆け抜けタイプの合わせて3タイプを作る。
#ガンダムUC50％でST、転落確率100分の1のため、駆け抜けだとしたら100回を引く。つまり次のあたりが100回以降の場合、平均50回を引けばよい。
#シンフォギア初当たり50％でST15回、電サポ中ST10000の振り分けがあるがほぼ継続するので無視。つまり、単発なら、8回、連チャン後なら15回引けばよい
#リゼロ2初当たり3000ならST145回、ST終了時も145回
#eゴジエヴァきついし釘なさそうなのでパス
#大海5二回目以降は次の当たりから100回引く
"""