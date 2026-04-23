import pandas as pd
from オーギヤ半田パチンコ出玉履歴から差枚計算 import cal_samai


def cal_border(start, dedama, machine_name, final_start, path, shubetu, max_mochidama, sadama, type):
    start = [text.replace("-", "0") for text in start]
    start = [int(text) for text in start if text.isdigit()]  # 数字のみ変
    dedama = [text.replace("-", "0") for text in dedama]
    dedama = [int(text) for text in dedama if text.isdigit()]  # 数字のみ変換
    df = pd.DataFrame({
        "スタート": start,
        "出玉": dedama,
        "種別": shubetu
    })
    dict = {"eF.戦姫絶唱ｼﾝﾌｫｷﾞｱ4 F": 17.8,
            "eｿｰﾄﾞｱｰﾄ･ｵﾝﾗｲﾝ閃光K7": 16.5,
            "e Re:ｾﾞﾛ season2 M13": 16.6,
            "P大海物語5 MTE2": 17.7,
            "P桃剣鬼神ZC": 16.3,
            "P新世ｴｳﾞｧ15未来への咆哮": 17.8,
            "eF.からくりｻｰｶｽ2 R": 18.1,
            "Pまどか☆ﾏｷﾞｶ3 LM3": 17.1,
            "e東京喰種W": 16.7,
            "P海物語極ｼﾞｬﾊﾟﾝHTH": 18.5,
            "P ToLOVEるﾀﾞｰｸﾈｽL0YU1": 17.4,
            "Pうる星やつら2 N2-K": 17.3,
            "P防振りFHZ": 17.7,
            "PAわんわんｾﾚﾌﾞﾚｰｼｮﾝAGBD": 15.3,
            "PA異世界魔王N2-X": 17.2,
            "PF.炎炎ﾉ消防隊YR": 16.9,
            "Pｸｲｰﾝｽﾞﾌﾞﾚｲﾄﾞ4 V1A": 17.4,
            "PﾊﾞﾝﾄﾞﾘL1AU1": 18.3,
            "P少女歌劇ﾚｳﾞｭｰｽﾀｧﾗｲﾄLT1": 17.4,
            "PｿﾞﾝﾋﾞﾗﾝﾄﾞｻｶﾞSCPC": 17.7,
            "PA大海物語5 ARBC": 18.3,
            "PA大海物語5 HLD": 16.8,
            "P中森明菜歌姫伝説愛KD-NS": 16.9,
            "P宇宙戦艦ﾔﾏﾄ2202ｵﾝﾘｰﾜﾝYR": 17.0,
            "e／押忍番長漢の頂／L09": 17.1,
            }
    type_A = {"e Re:ｾﾞﾛ season2 M13"}
    type_B = {"eF.戦姫絶唱ｼﾝﾌｫｷﾞｱ4 F", "P新世ｴｳﾞｧ15未来への咆哮", "P桃剣鬼神ZC", "e／押忍番長漢の頂／L09", "P少女歌劇ﾚｳﾞｭｰｽﾀｧﾗｲﾄLT1", "PﾊﾞﾝﾄﾞﾘL1AU1", "P海物語極ｼﾞｬﾊﾟﾝHTH", "Pｸｲｰﾝｽﾞﾌﾞﾚｲﾄﾞ4 V1A"}
    type_C = {"Pまどか☆ﾏｷﾞｶ3 LM3", "P ToLOVEるﾀﾞｰｸﾈｽL0YU1","eｿｰﾄﾞｱｰﾄ･ｵﾝﾗｲﾝ閃光K7", "PF.炎炎ﾉ消防隊YR", "PｿﾞﾝﾋﾞﾗﾝﾄﾞｻｶﾞSCPC", "Pうる星やつら2 N2-K"}
    type_D = {"P大海物語5 MTE2", "PA異世界魔王N2-X"}
    type_E = {"PA大海物語5 ARBC"}
    type_F = {"P中森明菜歌姫伝説愛KD-NS", "P宇宙戦艦ﾔﾏﾄ2202ｵﾝﾘｰﾜﾝYR"}
    type_G = {"PAわんわんｾﾚﾌﾞﾚｰｼｮﾝAGBD"}
    type_H = {"eF.からくりｻｰｶｽ2 R", "e東京喰種W", "P防振りFHZ"}
    decrease_start = 0

    if machine_name in type_A:
        param_dict = {"e Re:ｾﾞﾛ season2 M13":{"ikichi":1800, "ST":144}}
        ikichi = param_dict[machine_name]["ikichi"]
        ST = param_dict[machine_name]["ST"]
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "出玉"] >= ikichi and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                decrease_start += ST
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                decrease_start += ST
        if final_start < ST and df.loc[len(df) - 1, "出玉"] >= ikichi and df.loc[len(df) - 1, "種別"] == "大当":
            decrease_start += final_start
        if final_start > ST and df.loc[len(df) - 1, "種別"] == "確変":
            decrease_start += ST


    if machine_name in type_B:
        param_dict = {"P新世ｴｳﾞｧ15未来への咆哮": {"ST_A": 135, "ST_B": 163, "jitan":100},
                      "eF.戦姫絶唱ｼﾝﾌｫｷﾞｱ4 F": {"ST_A": 7.5, "ST_B": 15, "jitan":0},
                      "P桃剣鬼神ZC": {"ST_A": 0.62, "ST_B": 1, "jitan":0},
                      "P海物語極ｼﾞｬﾊﾟﾝHTH": {"ST_A": 60, "ST_B": 100, "jitan":20},
                      "P少女歌劇ﾚｳﾞｭｰｽﾀｧﾗｲﾄLT1": {"ST_A": 50, "ST_B": 100, "jitan":0},
                      "Pｸｲｰﾝｽﾞﾌﾞﾚｲﾄﾞ4 V1A": {"ST_A": 30.3, "ST_B": 60, "jitan":0},
                      "PﾊﾞﾝﾄﾞﾘL1AU1": {"ST_A": 100, "ST_B": 100, "jitan":0},
                      "e／押忍番長漢の頂／L09": {"ST_A": 39.25, "ST_B": 157, "jitan":0}}
        param_dict_m = {"P新世ｴｳﾞｧ15未来への咆哮": {"ST_A": 163, "ST_B": 163, "jitan":100},
                        "eF.戦姫絶唱ｼﾝﾌｫｷﾞｱ4 F": {"ST_A": 15, "ST_B": 15, "jitan":0},
                        "P桃剣鬼神ZC": {"ST_A": 1, "ST_B": 1, "jitan":0},
                        "P海物語極ｼﾞｬﾊﾟﾝHTH": {"ST_A": 100, "ST_B": 100, "jitan":20},
                        "Pｸｲｰﾝｽﾞﾌﾞﾚｲﾄﾞ4 V1A": {"ST_A": 60, "ST_B": 60, "jitan":0},
                        "P少女歌劇ﾚｳﾞｭｰｽﾀｧﾗｲﾄLT1": {"ST_A": 100, "ST_B": 100, "jitan":0},
                        "PﾊﾞﾝﾄﾞﾘL1AU1": {"ST_A": 100, "ST_B": 100, "jitan":0},
                        "e／押忍番長漢の頂／L09": {"ST_A": 157, "ST_B": 157, "jitan":0}}
        param_dict_M = {"P新世ｴｳﾞｧ15未来への咆哮": {"ST_A": 100, "ST_B": 163, "jitan":100},
                        "eF.戦姫絶唱ｼﾝﾌｫｷﾞｱ4 F": {"ST_A": 0, "ST_B": 15, "jitan":0},
                        "P桃剣鬼神ZC": {"ST_A": 0, "ST_B": 1, "jitan":0},
                        "P海物語極ｼﾞｬﾊﾟﾝHTH": {"ST_A": 20, "ST_B": 100, "jitan":20},
                        "P少女歌劇ﾚｳﾞｭｰｽﾀｧﾗｲﾄLT1": {"ST_A": 0, "ST_B": 100, "jitan":0},
                        "Pｸｲｰﾝｽﾞﾌﾞﾚｲﾄﾞ4 V1A": {"ST_A": 0, "ST_B": 60, "jitan":0},
                        "PﾊﾞﾝﾄﾞﾘL1AU1": {"ST_A": 100, "ST_B": 100, "jitan":0},
                        "e／押忍番長漢の頂／L09": {"ST_A": 0, "ST_B": 157, "jitan":0}}
        if type == 0:
            ST_A = param_dict[machine_name]["ST_A"]
            ST_B = param_dict[machine_name]["ST_B"]
            jitan = param_dict[machine_name]["jitan"]
        if type == 1:
            ST_A = param_dict_m[machine_name]["ST_A"]
            ST_B = param_dict_m[machine_name]["ST_B"]
            jitan = param_dict_m[machine_name]["jitan"]
        if type == 2:
            ST_A = param_dict_M[machine_name]["ST_A"]
            ST_B = param_dict_M[machine_name]["ST_B"]
            jitan = param_dict_M[machine_name]["jitan"]
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if jitan < df.loc[i + 1, "スタート"] <= ST_B:
                    decrease_start += jitan
                if ST_B < df.loc[i + 1, "スタート"]:
                    decrease_start += ST_A
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= ST_B:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > ST_B:
                    decrease_start += ST_B
        if df.loc[len(df) - 1, "種別"] == "大当":
            if final_start <= ST_A:
                decrease_start += final_start
            if final_start > ST_A:
                decrease_start += ST_A
        if df.loc[len(df) - 1, "種別"] == "確変":
            if final_start <= ST_B:
                decrease_start += final_start
            if final_start > ST_B:
                decrease_start += ST_B

    if machine_name in type_C:
        param_dict = {"eｿｰﾄﾞｱｰﾄ･ｵﾝﾗｲﾝ閃光K7": {"ikichi": 500, "ST_A": 35, "ST_B": 50, "ST_C": 115, "jitan":0},
                      "Pまどか☆ﾏｷﾞｶ3 LM3": {"ikichi": 500, "ST_A": 32.72, "ST_B": 60, "ST_C": 120, "jitan":0},
                      "Pうる星やつら2 N2-K": {"ikichi": 500, "ST_A": 70, "ST_B": 70, "ST_C": 174, "jitan":0},
                      "P ToLOVEるﾀﾞｰｸﾈｽL0YU1": {"ikichi": 500, "ST_A": 40, "ST_B": 40, "ST_C": 100, "jitan":0},
                      "PF.炎炎ﾉ消防隊YR": {"ikichi": 500, "ST_A": 20.64, "ST_B": 31, "ST_C": 100, "jitan":1},
                      "PA大海物語5 HLD": {"ikichi": 500, "ST_A": 24.5, "ST_B": 35, "ST_C": 110, "jitan":0},
                      "PｿﾞﾝﾋﾞﾗﾝﾄﾞｻｶﾞSCPC": {"ikichi": 500, "ST_A": 45, "ST_B": 90, "ST_C": 1, "jitan":0}}
        param_dict_m = {"eｿｰﾄﾞｱｰﾄ･ｵﾝﾗｲﾝ閃光K7": {"ikichi": 500, "ST_A": 50, "ST_B": 50, "ST_C": 115, "jitan":0},
                      "Pまどか☆ﾏｷﾞｶ3 LM3": {"ikichi": 500, "ST_A": 60, "ST_B": 60, "ST_C": 120, "jitan":0},
                        "Pうる星やつら2 N2-K": {"ikichi": 500, "ST_A": 70, "ST_B": 70, "ST_C": 174, "jitan":0},
                        "P ToLOVEるﾀﾞｰｸﾈｽL0YU1": {"ikichi": 500, "ST_A": 40, "ST_B": 40, "ST_C": 100, "jitan":0},
                        "PF.炎炎ﾉ消防隊YR": {"ikichi": 500, "ST_A": 31, "ST_B": 31, "ST_C": 100, "jitan":1},
                        "PA大海物語5 HLD": {"ikichi": 500, "ST_A": 35, "ST_B": 35, "ST_C": 110, "jitan":0},
                        "PｿﾞﾝﾋﾞﾗﾝﾄﾞｻｶﾞSCPC": {"ikichi": 500, "ST_A": 90, "ST_B": 90, "ST_C": 1, "jitan":0}}
        param_dict_M = {"eｿｰﾄﾞｱｰﾄ･ｵﾝﾗｲﾝ閃光K7": {"ikichi": 500, "ST_A": 0, "ST_B": 50, "ST_C": 115, "jitan":0},
                      "Pまどか☆ﾏｷﾞｶ3 LM3": {"ikichi": 500, "ST_A": 0, "ST_B": 60, "ST_C": 120, "jitan":0},
                        "PA大海物語5 HLD": {"ikichi": 500, "ST_A": 0, "ST_B": 35, "ST_C": 110, "jitan":0},
                        "P ToLOVEるﾀﾞｰｸﾈｽL0YU1": {"ikichi": 500, "ST_A": 40, "ST_B": 40, "ST_C": 100, "jitan":0},
                        "PF.炎炎ﾉ消防隊YR": {"ikichi": 500, "ST_A": 1, "ST_B": 31, "ST_C": 100, "jitan":1},
                        "Pうる星やつら2 N2-K": {"ikichi": 500, "ST_A": 70, "ST_B": 70, "ST_C": 174, "jitan":0},
                        "PｿﾞﾝﾋﾞﾗﾝﾄﾞｻｶﾞSCPC": {"ikichi": 500, "ST_A": 0, "ST_B": 90, "ST_C": 1, "jitan":0}}
        if type == 0:
            ikichi = param_dict[machine_name]["ikichi"]
            ST_A = param_dict[machine_name]["ST_A"]
            ST_B = param_dict[machine_name]["ST_B"]
            ST_C = param_dict[machine_name]["ST_C"]
            jitan = param_dict[machine_name]["jitan"]
        if type == 1:
            ikichi = param_dict_m[machine_name]["ikichi"]
            ST_A = param_dict_m[machine_name]["ST_A"]
            ST_B = param_dict_m[machine_name]["ST_B"]
            ST_C = param_dict_m[machine_name]["ST_C"]
            jitan = param_dict_m[machine_name]["jitan"]
        if type == 2:
            ikichi = param_dict_M[machine_name]["ikichi"]
            ST_A = param_dict_M[machine_name]["ST_A"]
            ST_B = param_dict_M[machine_name]["ST_B"]
            ST_C = param_dict_M[machine_name]["ST_C"]
            jitan = param_dict_M[machine_name]["jitan"]
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "出玉"] <= ikichi and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if jitan < df.loc[i + 1, "スタート"] <= ST_B:
                    decrease_start += jitan
                elif ST_B <= df.loc[i + 1, "スタート"]:
                    decrease_start += ST_A
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":  # おかしい
                last_big_win_idx = df.loc[:i, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
                if last_big_win_idx is not None:
                    has_large_start = (df.loc[last_big_win_idx + 1:i, "スタート"] >= ST_B + 1).any()
                    if has_large_start:
                        if df.loc[i + 1, "スタート"] <= ST_C:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > ST_C:
                            decrease_start += ST_C
                    else:
                        if df.loc[i + 1, "スタート"] <= ST_B:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > ST_B:
                            decrease_start += ST_B
        if df.loc[len(df) - 1, "出玉"] <= ikichi and df.loc[len(df) - 1, "種別"] == "大当":
            if jitan < final_start <= ST_B:
                decrease_start += jitan
            elif final_start > ST_B:
                decrease_start += ST_A
        if df.loc[len(df) - 1, "種別"] == "確変":
            last_big_win_idx = df.loc[:len(df) - 1, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
            if last_big_win_idx is not None:
                has_large_start = (df.loc[last_big_win_idx + 1:len(df) - 1, "スタート"] >= ST_B + 1).any()
                if has_large_start:
                    if final_start <= ST_C:
                        decrease_start += final_start
                    if final_start > ST_C:
                        decrease_start += ST_C
                else:
                    if final_start <= ST_B:
                        decrease_start += final_start
                    if final_start > ST_B:
                        decrease_start += ST_B


    if machine_name in type_D:
        param_dict = {"P大海物語5 MTE2": {"ST":100}, "PA異世界魔王N2-X": {"ST":1}}
        ST = param_dict[machine_name]["ST"]
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= ST:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > ST:
                    decrease_start += ST
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= ST:
                    decrease_start += df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > ST:
                    decrease_start += ST
        if final_start < ST:
            decrease_start += final_start
        if final_start > ST:
            decrease_start += ST


    if machine_name in type_E:
        param_dict = {"PA大海物語5 ARBC": {"ikichi_A": 500, "ikichi_B": 700, "ST_A": 25, "ST_B": 50, "ST_C": 120,
                                            "ST_D": 299, "ST_E": 379, "ST_F": 678}}
        ikichi_A = param_dict[machine_name]["ikichi_A"]
        ikichi_B = param_dict[machine_name]["ikichi_B"]
        ST_A = param_dict[machine_name]["ST_A"]
        ST_B = param_dict[machine_name]["ST_B"]
        ST_C = param_dict[machine_name]["ST_C"]
        ST_D = param_dict[machine_name]["ST_D"]
        ST_E = param_dict[machine_name]["ST_E"]
        ST_F = param_dict[machine_name]["ST_F"]
        temp_d_start = 0
        for i in range(len(df) - 1):  # 最後の行は対象外
            if (df.loc[i, "スタート"] - temp_d_start) > ST_D:
                if (df.loc[i, "スタート"] - temp_d_start) <= ST_F:
                    decrease_start += df.loc[i, "スタート"] - temp_d_start - ST_D
                else:
                    decrease_start += ST_E
            temp_d_start = 0
            if df.loc[i, "出玉"] <= ikichi_A and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= ST_A:
                    decrease_start += df.loc[i + 1, "スタート"]
                    temp_d_start = df.loc[i + 1, "スタート"]
                else:
                    decrease_start += ST_A
                    temp_d_start = ST_A
            elif ikichi_A < df.loc[i, "出玉"] <= ikichi_B and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= ST_B:
                    decrease_start += df.loc[i + 1, "スタート"]
                    temp_d_start = df.loc[i + 1, "スタート"]
                else:
                    decrease_start += ST_B
                    temp_d_start = ST_B
            elif ikichi_B < df.loc[i, "出玉"] and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= ST_C:
                    decrease_start += df.loc[i + 1, "スタート"]
                    temp_d_start = df.loc[i + 1, "スタート"]
                else:
                    decrease_start += ST_C
                    temp_d_start = ST_C
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":  # おかしい
                last_big_win_idx = df.loc[:i, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
                if last_big_win_idx is not None:
                    has_large_start = (df.loc[last_big_win_idx + 1:i, "出玉"] >= ikichi_B).any()
                    if has_large_start:
                        if df.loc[i + 1, "スタート"] <= ST_C:
                            decrease_start += df.loc[i + 1, "スタート"]
                            temp_d_start = df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > ST_C:
                            decrease_start += ST_C
                            temp_d_start = ST_C
                    elif df.loc[i, "出玉"] <= ikichi_A:
                        if df.loc[i + 1, "スタート"] <= ST_A:
                            decrease_start += df.loc[i + 1, "スタート"]
                            temp_d_start = df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > ST_A:
                            decrease_start += ST_A
                            temp_d_start = ST_A
                    elif ikichi_A < df.loc[i, "出玉"]:
                        if df.loc[i + 1, "スタート"] <= ST_B:
                            decrease_start += df.loc[i + 1, "スタート"]
                            temp_d_start = df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > ST_B:
                            decrease_start += ST_B
                            temp_d_start = ST_B
        if df.loc[len(df) - 1, "種別"] == "大当":
            if df.loc[len(df) - 1, "出玉"] <= ikichi_A:
                if final_start <= ST_A:
                    decrease_start += final_start
                elif final_start > ST_A:
                    decrease_start += ST_A
            if ikichi_A < df.loc[len(df) - 1, "出玉"] <= ikichi_B:
                if final_start <= ST_B:
                    decrease_start += final_start
                elif final_start > ST_B:
                    decrease_start += ST_B
            if ikichi_B < df.loc[len(df) - 1, "出玉"]:
                if final_start <= ST_C:
                    decrease_start += final_start
                elif final_start > ST_C:
                    decrease_start += ST_C
        if df.loc[len(df) - 1, "種別"] == "確変":
            last_big_win_idx = df.loc[:len(df) - 1, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
            if last_big_win_idx is not None:
                has_large_start = (df.loc[last_big_win_idx + 1:len(df) - 1, "出玉"] >= ikichi_B).any()
                if has_large_start:
                    if final_start <= ST_C:
                        decrease_start += final_start
                    if final_start > ST_C:
                        decrease_start += ST_C
                elif df.loc[len(df) - 1, "出玉"] <= ikichi_A:
                    if final_start <= ST_A:
                        decrease_start += final_start
                    if final_start > ST_A:
                        decrease_start += ST_A
                elif ikichi_A < df.loc[len(df) - 1, "出玉"]:
                    if final_start <= ST_A:
                        decrease_start += final_start
                    if final_start > ST_B:
                        decrease_start += ST_B

    if machine_name in type_G:
        param_dict = {"PAわんわんｾﾚﾌﾞﾚｰｼｮﾝAGBD": {"ikichi": 5000, "ST_A": 50, "ST_B": 50, "ST_C": 117, "ST_D": 250, "ST_E": 379, "ST_F": 629},
                      }
        param_dict_m = {"PAわんわんｾﾚﾌﾞﾚｰｼｮﾝAGBD": {"ikichi": 5000, "ST_A": 50, "ST_B": 50, "ST_C": 117, "ST_D": 250, "ST_E": 379, "ST_F": 629},
                        }
        param_dict_M = {"PAわんわんｾﾚﾌﾞﾚｰｼｮﾝAGBD": {"ikichi": 5000, "ST_A": 50, "ST_B": 50, "ST_C": 117, "ST_D": 250, "ST_E": 379, "ST_F": 629},
                        }
        if type == 0:
            ikichi = param_dict[machine_name]["ikichi"]
            ST_A = param_dict[machine_name]["ST_A"]
            ST_B = param_dict[machine_name]["ST_B"]
            ST_C = param_dict[machine_name]["ST_C"]
            ST_D = param_dict[machine_name]["ST_D"]
            ST_E = param_dict[machine_name]["ST_E"]
            ST_F = param_dict[machine_name]["ST_F"]
        if type == 1:
            ikichi = param_dict_m[machine_name]["ikichi"]
            ST_A = param_dict_m[machine_name]["ST_A"]
            ST_B = param_dict_m[machine_name]["ST_B"]
            ST_C = param_dict_m[machine_name]["ST_C"]
            ST_D = param_dict_m[machine_name]["ST_D"]
            ST_E = param_dict_m[machine_name]["ST_E"]
            ST_F = param_dict_m[machine_name]["ST_F"]
        if type == 2:
            ikichi = param_dict_M[machine_name]["ikichi"]
            ST_A = param_dict_M[machine_name]["ST_A"]
            ST_B = param_dict_M[machine_name]["ST_B"]
            ST_C = param_dict_M[machine_name]["ST_C"]
            ST_D = param_dict_M[machine_name]["ST_D"]
            ST_E = param_dict_M[machine_name]["ST_E"]
            ST_F = param_dict_M[machine_name]["ST_F"]
        temp_d_start = 0
        for i in range(len(df) - 1):  # 最後の行は対象外
            if (df.loc[i, "スタート"] - temp_d_start) > ST_D:
                if (df.loc[i, "スタート"] - temp_d_start) <= ST_F:
                    decrease_start += df.loc[i, "スタート"] - temp_d_start - ST_D
                else:
                    decrease_start += ST_E
            temp_d_start = 0

            if df.loc[i, "出玉"] <= ikichi and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= ST_A:
                    decrease_start += df.loc[i + 1, "スタート"]
                    temp_d_start = df.loc[i + 1, "スタート"]
                else:
                    decrease_start += ST_A
                    temp_d_start = ST_A
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":  # おかしい
                last_big_win_idx = df.loc[:i, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
                if last_big_win_idx is not None:
                    has_large_start = (df.loc[last_big_win_idx + 1:i, "スタート"] >= ST_B + 1).any()
                    if has_large_start:
                        if df.loc[i + 1, "スタート"] <= ST_C:
                            decrease_start += df.loc[i + 1, "スタート"]
                            temp_d_start = df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > ST_C:
                            decrease_start += ST_C
                            temp_d_start = ST_C
                    else:
                        if df.loc[i + 1, "スタート"] <= ST_B:
                            decrease_start += df.loc[i + 1, "スタート"]
                            temp_d_start = df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > ST_B:
                            decrease_start += ST_B
                            temp_d_start = ST_B
        if df.loc[len(df) - 1, "出玉"] <= ikichi and df.loc[len(df) - 1, "種別"] == "大当":
            if final_start <= ST_A:
                decrease_start += final_start
            elif final_start > ST_A:
                decrease_start += ST_A
        if df.loc[len(df) - 1, "種別"] == "確変":
            last_big_win_idx = df.loc[:len(df) - 1, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
            if last_big_win_idx is not None:
                has_large_start = (df.loc[last_big_win_idx + 1:len(df) - 1, "スタート"] >= ST_B + 1).any()
                if has_large_start:
                    if final_start <= ST_C:
                        decrease_start += final_start
                    if final_start > ST_C:
                        decrease_start += ST_C
                else:
                    if final_start <= ST_B:
                        decrease_start += final_start
                    if final_start > ST_B:
                        decrease_start += ST_B

    if machine_name in type_F:
        param_dict = {"P中森明菜歌姫伝説愛KD-NS": {"ST":80, "ST_A":150, "ST_B":50000, "ST_C":50150},
                      "P宇宙戦艦ﾔﾏﾄ2202ｵﾝﾘｰﾜﾝYR": {"ST":1, "ST_A":255, "ST_B":50000, "ST_C":50255}}
        ST = param_dict[machine_name]["ST"]
        ST_A = param_dict[machine_name]["ST_A"]
        ST_B = param_dict[machine_name]["ST_B"]
        ST_C = param_dict[machine_name]["ST_B"]
        temp_d_start = 0
        for i in range(len(df) - 1):  # 最後の行は対象外
            if (df.loc[i, "スタート"] - temp_d_start) > ST_A:
                if (df.loc[i, "スタート"] - temp_d_start) <= ST_C:
                    decrease_start += df.loc[i, "スタート"] - temp_d_start - ST_A
                else:
                    decrease_start += ST_B
            temp_d_start = 0
            if df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= ST:
                    decrease_start += df.loc[i + 1, "スタート"]
                    temp_d_start = df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > ST:
                    decrease_start += ST
                    temp_d_start = ST
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= ST:
                    decrease_start += df.loc[i + 1, "スタート"]
                    temp_d_start = df.loc[i + 1, "スタート"]
                if df.loc[i + 1, "スタート"] > ST:
                    decrease_start += ST
                    temp_d_start = ST
        if final_start < ST:
            decrease_start += final_start
        if final_start > ST:
            decrease_start += ST

    if machine_name in type_H:
        param_dict = {"P防振りFHZ": {"ikichi": 350, "ST_A": 100, "ST_B": 100, "ST_C": 157},
                      "e東京喰種W": {"ikichi": 350,"ST_A": 66.3, "ST_B": 130, "ST_C": 130},
                      "eF.からくりｻｰｶｽ2 R": {"ikichi": 350, "ST_A": 70.2, "ST_B": 135, "ST_C": 135},
                      }
        param_dict_m = {"P防振りFHZ": {"ikichi": 350, "ST_A": 100, "ST_B": 100, "ST_C": 157},
                        "e東京喰種W": {"ikichi": 350,"ST_A": 130, "ST_B": 130, "ST_C": 130},
                        "eF.からくりｻｰｶｽ2 R": {"ikichi": 350,"ST_A": 135, "ST_B": 135, "ST_C": 135}}
        param_dict_M = {"P防振りFHZ": {"ikichi": 350, "ST_A": 100, "ST_B": 100, "ST_C": 157},
                        "e東京喰種W": {"ikichi": 350,"ST_A": 0, "ST_B": 130, "ST_C": 130},
                        "eF.からくりｻｰｶｽ2 R": {"ikichi": 350,"ST_A": 0, "ST_B": 135, "ST_C": 135}}
        if type == 0:
            ikichi = param_dict[machine_name]["ikichi"]
            ST_A = param_dict[machine_name]["ST_A"]
            ST_B = param_dict[machine_name]["ST_B"]
            ST_C = param_dict[machine_name]["ST_C"]
        if type == 1:
            ikichi = param_dict_m[machine_name]["ikichi"]
            ST_A = param_dict_m[machine_name]["ST_A"]
            ST_B = param_dict_m[machine_name]["ST_B"]
            ST_C = param_dict_m[machine_name]["ST_C"]
        if type == 2:
            ikichi = param_dict_M[machine_name]["ikichi"]
            ST_A = param_dict_M[machine_name]["ST_A"]
            ST_B = param_dict_M[machine_name]["ST_B"]
            ST_C = param_dict_M[machine_name]["ST_C"]
        for i in range(len(df) - 1):  # 最後の行は対象外
            if df.loc[i, "出玉"] >= ikichi and df.loc[i, "種別"] == "大当" and df.loc[i + 1, "種別"] == "大当":
                if df.loc[i + 1, "スタート"] <= ST_A:
                    decrease_start += df.loc[i + 1, "スタート"]
                else:
                    decrease_start += ST_A
            elif df.loc[i, "種別"] == "確変" and df.loc[i + 1, "種別"] == "大当":  # おかしい
                last_big_win_idx = df.loc[:i, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
                if last_big_win_idx is not None:
                    has_large_start = (df.loc[last_big_win_idx + 1:i, "スタート"] >= ST_B + 1).any()
                    if has_large_start:
                        if df.loc[i + 1, "スタート"] <= ST_C:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > ST_C:
                            decrease_start += ST_C
                    else:
                        if df.loc[i + 1, "スタート"] <= ST_B:
                            decrease_start += df.loc[i + 1, "スタート"]
                        if df.loc[i + 1, "スタート"] > ST_B:
                            decrease_start += ST_B
        if df.loc[len(df) - 1, "出玉"] <= ikichi and df.loc[len(df) - 1, "種別"] == "大当":
            if final_start <= ST_A:
                decrease_start += final_start
            elif final_start > ST_A:
                decrease_start += ST_A
        if df.loc[len(df) - 1, "種別"] == "確変":
            last_big_win_idx = df.loc[:len(df) - 1, "種別"].eq("大当").replace(False, pd.NA).last_valid_index()
            if last_big_win_idx is not None:
                has_large_start = (df.loc[last_big_win_idx + 1:len(df) - 1, "スタート"] >= ST_B + 1).any()
                if has_large_start:
                    if final_start <= ST_C:
                        decrease_start += final_start
                    if final_start > ST_C:
                        decrease_start += ST_C
                else:
                    if final_start <= ST_B:
                        decrease_start += final_start
                    if final_start > ST_B:
                        decrease_start += ST_B



    nomal_start = df[df["種別"] == "大当"]["スタート"].sum() - decrease_start + final_start
    print(nomal_start)
    special_start = df[df["種別"] == "確変"]["スタート"].sum() + decrease_start
    dedama_sum = df["出玉"].sum()
    if not sadama:
        saishusadama = cal_samai(path, max_mochidama)[0]
    else:
        saishusadama = sadama
    print(f"最終差玉:{saishusadama}")
    kaitensuu = nomal_start * 250 / (dedama_sum - saishusadama - special_start * 0.1)
    print(f"回転数:{kaitensuu}")
    if machine_name in dict:
        kitaichi = kaitensuu - dict[machine_name] if kaitensuu is not None else None
    else:
        kaitensuu = None
        kitaichi = None

    print(f"{type}ボーダー差分:{kitaichi}")
    return kaitensuu, saishusadama, kitaichi, nomal_start
"""
start = ['32', '1', '10', '479', '3', '38', '5', '146', '87', '1', '101', '1', '8', '85', '99', '32', '2', '10', '22', '15', '2', '158', '1', '6', '141', '1', '4', '3', '73', '40', '18', '68', '3', '25', '181', '10', '229', '5', '5', '1', '10', '3', '122', '53', '81', '6', '56', '9', '5', '135', '2', '120', '6', '4', '173', '7', '5', '163', '2', '153', '4', '18', '3', '6', '10', '3']
dedama = ['550', '370', '580', '590', '540', '370', '550', '580', '380', '560', '590', '600', '570', '600', '380', '560', '390', '360', '390', '580', '360', '390', '600', '610', '610', '590', '610', '370', '370', '610', '410', '370', '590', '580', '590', '370', '590', '400', '580', '610', '580', '400', '580', '590', '580', '580', '580', '570', '640', '570', '420', '360', '590', '380', '980', '590', '600', '590', '590', '560', '420', '590', '380', '380', '610', '590']
machine_name = 'PA大海物語5 ARBC'
final_start = 96
path = 'M0.50,200.50 L0.50,200.50 L13.50,200.50 L36.50,185.50 L59.50,222.50 L82.50,258.50 L105.50,244.50 L129.50,223.50 L152.50,203.50 L175.50,179.50 L198.50,186.50 L221.50,173.50 L244.50,146.50 L267.50,130.50 L290.50,140.50 L313.50,138.50 L336.50,189.50 L359.50,126.50 L382.50,131.50 L405.50,141.50 L428.50,137.50 L451.50,83.50 L474.50,78.50 L497.50,78.50 L520.50,75.50 L543.50,103.50 L566.50,81.50 L589.50,89.50 L612.50,22.50 L635.50,27.50 L682.50,27.50 L682.50,27.50 96'
max_mochidama = 10820
shubetu = ['大当', '確変', '確変', '大当', '確変', '確変', '確変', '大当', '大当', '確変', '大当', '確変', '確変', '大当', '大当', '大当', '確変', '確変', '確変', '確変', '確変', '大当', '確変', '確変', '大当', '確変', '確変', '確変', '大当', '大当', '確変', '大当', '確変', '確変', '大当', '確変', '大当', '確変', '確変', '確変', '確変', '確変', '大当', '大当', '大当', '確変', '大当', '確変', '確変', '大当', '確変', '大当', '確変', '確変', '大当', '確変', '確変', '大当', '確変', '大当', '確変', '確変', '確変', '確変', '確変', '確変']
x = cal_border(start, dedama , machine_name, final_start, path, shubetu, max_mochidama, None, 1)
print(x[0],x[1],x[2])
"""