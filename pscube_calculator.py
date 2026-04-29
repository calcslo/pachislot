import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# 機種ごとのボーダー値
BORDER_DICT = {
    "eF戦姫絶唱シンフォギア4 キャロルver.": 17.8,
    "e ソードアート・オンライン 閃光の軌跡": 16.5,
    "P にゃんこ大戦争 多様性のネコ": 17.5,
    "e Re:ｾﾞﾛ season2 M13": 16.6,
    "P大海物語5": 17.7,
    "P新世ｴｳﾞｧ15未来への咆哮": 17.8,
    "eF.からくりｻｰｶｽ2 R": 18.1,
    "P 魔法少女まどか☆マギカ3": 17.1,
    "eぱちんこ押忍!番長 漢の頂": 17.1,
    "PA大海物語5 ARBC": 18.3,
    "Pｽｰﾊﾟｰ海物語IN沖縄6 LTP": 17.6,
    "e新世紀ｴｳﾞｧ17はじまりR": 16.7,
    "e東京喰種W": 16.7,
    "e魔法少女まどかﾏｷﾞｶ3LPM1": 20.2,
    "eF.ｷﾝ肉ﾏﾝ": 16.6,
    "e北斗の拳11暴凶星SHEF": 16.8,
    "eF.ﾌﾞﾙｰﾛｯｸMZ": 17.4,
    "e甲鉄城のｶﾊﾞﾈﾘ2 GFEA": 17.1,
    "eﾘｺﾘｽ･ﾘｺｲﾙM3": 17.2,
    "e牙狼12 XX-MJ": 17.2,
    "eﾘﾝｸﾞ最恐領域RHA": 17.4,
    "PA海物語極ｼﾞｬﾊﾟﾝHBD": 17.6,
    "PA大海物語5 HLD": 16.8,
}

# 機種ごとのST/時短設定 (Min, Med, Max の計算に使用)
# key: machine_name or partial name
# value: { mode: { "big": ST回数, "special": ST回数, "threshold_dedama": 出玉閾値 } }
ST_CONFIG = {
    "シンフォギア4": {
        "med": {"big": 8, "special": 15},
        "min": {"big": 15, "special": 15},
        "max": {"big": 0, "special": 15},
    },
    "ソードアート・オンライン": {
        "med": {"big_low": 35, "big_high":115, "special_low": 50, "special_high": 115, "big_dedama": 500},
        "min": {"big_low": 50, "big_high":115, "special_low": 50, "special_high": 115, "big_dedama": 500},
        "max": {"big_low": 0, "big_high":115, "special_low": 50, "special_high": 115, "big_dedama": 500},
    },
    "にゃんこ大戦争": {
        "all": {"special": 155}
    },
    "e Re:ｾﾞﾛ season2 M13": {
        "all": {"big": 145, "special": 145}
    },
    "P大海物語5": {
        "all": {"big": 100, "special": 100}
    },
    "P新世ｴｳﾞｧ15未来への咆哮": {
        "med": {"big": 135, "special": 163},
        "min": {"big": 163, "special": 163},
        "max": {"big": 100, "special": 163},
    },
    "eF.からくりｻｰｶｽ2 R": {
        "med": {"big": 70, "special": 135},
        "min": {"big": 135, "special": 135},
        "max": {"big": 0, "special": 135},
    },
    "P 魔法少女まどか☆マギカ3": {
        "med": {"big_low": 33, "big_high": 120, "special_low": 60, "special_high": 120, "big_dedama": 1000},
        "min": {"big_low": 60, "big_high": 120, "special_low": 60, "special_high": 120, "big_dedama": 1000},
        "max": {"big_low": 0, "big_high": 120, "special_low": 60, "special_high": 120, "big_dedama": 1000},
    },
    "押忍!番長 漢の頂": {
        "med": {"big": 39, "special": 157},
        "min": {"big": 157, "special": 157},
        "max": {"big": 0, "special": 157},
    },
    "Pｽｰﾊﾟｰ海物語IN沖縄6 LTP": {
        "all": {"big": 100, "special_low": 100, "special_high": 200}
    },
    "e新世紀ｴｳﾞｧ17はじまりR": {
        "med": {"big_low": 129,"big_high":157, "special": 157, "big_dedama": 800},
        "min": {"big_low": 157,"big_high":157, "special": 157, "big_dedama": 800},
        "max": {"big_low": 100,"big_high":157, "special": 157, "big_dedama": 800},
    },
    "e東京喰種W": {
        "med": {"big": 65, "special": 130},
        "min": {"big": 130, "special": 130},
        "max": {"big": 0, "special": 130},
    },
    "e魔法少女まどかﾏｷﾞｶ3LPM1": {
        "med": {"big_low": 70, "big_high": 130, "special": 130, "big_dedama": 600},
        "min": {"big_low": 100, "big_high": 130, "special": 130, "big_dedama": 600},
        "max": {"big_low": 0, "big_high": 130, "special": 130, "big_dedama": 600},
    },
    "eF.ｷﾝ肉ﾏﾝ": {
        "med": {"big": 73, "special": 145},
        "min": {"big": 145, "special": 145},
        "max": {"big": 0, "special": 145},
    },
    "e北斗の拳11暴凶星SHEF": {
        "med": {"big_low": 4,"big_high":10,"special": 10, "big_dedama": 1500},
        "min": {"big_low": 10,"big_high":10, "special": 10, "big_dedama": 1500},
        "max": {"big_low": 0,"big_high":10, "special": 10, "big_dedama": 1500},
    },
    "eF.ﾌﾞﾙｰﾛｯｸMZ": {
        "med": {"big_low":41,"big_high":75, "special": 75, "big_dedama": 1300},
        "min": {"big_low":136,"big_high":248, "special": 248, "big_dedama": 1300},
        "max": {"big_low":6,"big_high":11, "special": 11, "big_dedama": 1300},
    },
    "e甲鉄城のｶﾊﾞﾈﾘ2 GFEA":{
        "med": {"big":67, "special": 134},
        "min": {"big": 134, "special": 134},
        "max": {"big": 0, "special": 134},
    },
    "eﾘｺﾘｽ･ﾘｺｲﾙM3": {
        "med": {"big_low": 66, "big_high":132,"special": 132, "big_dedama": 1300},
        "min": {"big_low": 132, "big_high":132,"special": 132, "big_dedama": 1300},
        "max": {"big_low": 0, "big_high":132, "special": 132, "big_dedama": 1300},
    },
    "e牙狼12 XX-MJ": {
        "all": {"special": 1}
    },
    "eﾘﾝｸﾞ最恐領域RHA": {
        "med": {"big": 43, "special": 75},
        "min": {"big": 75, "special": 75},
        "max": {"big": 0, "special": 75},
    },
    "PA海物語極ｼﾞｬﾊﾟﾝHBD": {
        "med": {"big": 47, "special": 74},
        "min": {"big": 74, "special": 74},
        "max": {"big": 20, "special": 74},
    },
    "PA大海物語5 HLD": {
        "med": {"big": 25, "special_low": 35, "special_high": 110},
        "min": {"big": 35, "special_low": 35, "special_high": 110},
        "max": {"big": 0, "special_low": 35, "special_high": 110},
    },
}

def get_machine_config(machine_name):
    """機種名から設定を取得する"""
    for key, config in ST_CONFIG.items():
        if key == machine_name:
            return config
    return None

def calculate_decrease_start_core(df, final_start, machine_name, mode):
    """ST/時短回数の合計（減算対象）を計算する"""
    config = get_machine_config(machine_name)
    if not config:
        return 0

    # モードに応じた設定を取得
    m_config = config.get(mode) or config.get("all")
    if not m_config:
        return 0

    decrease_start = 0
    has_large_start = False # SAOやまでか3用

    # 履歴行のループ
    for i in range(len(df)):
        # 次のスタートがどれだけSTだったかを判定する
        # i行目の大当たりの後のスタート（i+1行目のスタート、または最後の次はfinal_start）
        current_start = df.loc[i + 1, "スタート"] if i + 1 < len(df) else final_start
        current_shubetu = df.loc[i, "種別"]
        current_dedama = df.loc[i, "出玉"]

        st_val = 0
        if current_shubetu == "大当":
            # 大当たりの場合
            if "big_dedama" in m_config:
                if "big_high" in m_config: # まどか3等
                    st_val = m_config["big_high"] if current_dedama >= m_config["big_dedama"] else m_config["big_low"]
                else: # シンフォギア等
                    st_val = m_config["big"] if current_dedama >= m_config["big_dedama"] else 0
            else:
                st_val = m_config.get("big", 0)
                
            if machine_name == "Pｽｰﾊﾟｰ海物語IN沖縄6 LTP" and current_dedama <= 100:
                has_large_start = True
                st_val = 200
            elif machine_name == "e Re:ｾﾞﾛ season2 M13":
                next_shubetu = df.loc[i+1, "種別"] if i+1 < len(df) else "大当"
                if next_shubetu != "確変":
                    st_val = 0
            elif machine_name in ["e東京喰種W", "e北斗の拳11暴凶星SHEF"] and current_dedama <= 300:
                next_shubetu = df.loc[i+1, "種別"] if i+1 < len(df) else "大当"
                if next_shubetu != "確変":
                    st_val = 0
        elif current_shubetu == "確変":
            # 確変の場合
            if "special_high" in m_config:
                # 汎用的な上位ST突入判定:
                # インターバルのスタートが special_low を超えていて、かつその当たりが「確変」であれば
                # 既に上位ST (special_high) に滞在していると判定できる。
                next_shubetu = df.loc[i+1, "種別"] if i+1 < len(df) else "大当"
                
                if machine_name == "Pｽｰﾊﾟｰ海物語IN沖縄6 LTP":
                    if current_dedama <= 100:
                        has_large_start = True
                else:
                    if m_config["special_low"] < current_start <= m_config["special_high"] and next_shubetu == "確変":
                        has_large_start = True
                
                st_val = m_config["special_high"] if has_large_start else m_config["special_low"]
            else:
                st_val = m_config.get("special", 0)
        
        # スタート回数を超えて引くことはできない
        decrease_start += min(current_start, st_val)
        
        # 確変が途切れたらフラグをリセット（簡易的な実装）
        if i + 1 < len(df) and df.loc[i+1, "種別"] == "大当":
            has_large_start = False

    return decrease_start

def calculate_decrease_start_agnes(df, final_start, mode):
    """PA大海物語5 アグネス専用の減算計算"""
    is_happiness = False
    decrease_start = 0
    for i in range(len(df)):
        current_dedama = df.loc[i, "出玉"]
        next_start = df.loc[i + 1, "スタート"] if i + 1 < len(df) else final_start
        
        # 1. 電サポ回数の判定
        st_val = 0
        if is_happiness:
            st_val = 120
        else:
            if current_dedama >= 900: # 10R想定
                is_happiness = True
                st_val = 120
            elif current_dedama >= 500: # 6R想定
                st_val = 50
            else: # 4R想定
                if mode == "med":
                    st_val = 29
                elif mode == "min":
                    st_val = 50
                else: # max
                    st_val = 25
        
        # 2. 電サポ分を減算
        decrease_start += min(next_start, st_val)
        
        # 3. 遊タイム判定 (通常299回転で発動)
        normal_rot = next_start - st_val
        if normal_rot > 299:
            yu_time = min(normal_rot - 299, 379) # 最大379回
            decrease_start += yu_time
            
    return decrease_start

def calculate_expected_value(start, dedama, shubetu, final_start, machine_name, final_diff_ball):
    """
    大当たり履歴と最終差玉から期待値等を計算する (Min, Med, Maxの3パターン)
    """
    try:
        # 1. 「最終スタート」マーカー以降（本日分）のみを抽出
        # リストは oldest-first (古い順) で渡される
        
        # 最後の要素がマーカーであり、かつそのスタート数が本日の最終スタートと一致する場合、
        # それは「今日の最終状態」を示すマーカーなので除外する
        if len(shubetu) > 0 and ("最終スタート" in str(shubetu[-1]) or "累計" in str(shubetu[-1])):
            last_start_str = str(start[-1]).replace("-", "0").replace(",", "")
            last_start_val = int(last_start_str) if last_start_str.isdigit() else 0
            if last_start_val == final_start:
                start = start[:-1]
                shubetu = shubetu[:-1]
                dedama = dedama[:-1]
                
        # 残りのリストから、最後のマーカーを探す（それが昨日の最終状態を示すマーカーになる）
        marker_idx = -1
        for i, t in enumerate(shubetu):
            if "最終スタート" in str(t) or "累計" in str(t):
                marker_idx = i
        
        if marker_idx != -1:
            start = start[marker_idx+1:]
            shubetu = shubetu[marker_idx+1:]
            dedama = dedama[marker_idx+1:]

        # 2. リストのクリーニング (数値変換と長さの整合性確保)
        cleaned_start = []
        cleaned_dedama = []
        cleaned_shubetu = []
        for i in range(len(start)):
            s = str(start[i]).replace("-", "0").replace(",", "").strip()
            d = str(dedama[i]).replace("-", "0").replace(",", "").strip()
            t = str(shubetu[i]).replace(" ", "").replace("　", "").strip()
            
            cleaned_start.append(int(s) if s.isdigit() else 0)
            cleaned_dedama.append(int(d) if d.isdigit() else 0)
            cleaned_shubetu.append(t)
        
        df = pd.DataFrame({
            "スタート": cleaned_start,
            "出玉": cleaned_dedama,
            "種別": cleaned_shubetu
        })
        print(f"cleaned:{df}")
        
        results = {}
        border = BORDER_DICT.get(machine_name, 18.0)

        for mode in ["min", "med", "max"]:
            if df.empty:
                nomal_start = final_start
                special_start = 0
                dedama_sum = 0
            else:
                if machine_name == "PA大海物語5 ARBC":
                    decrease_start = calculate_decrease_start_agnes(df, final_start, mode)
                else:
                    decrease_start = calculate_decrease_start_core(df, final_start, machine_name, mode)
                
                nomal_start = df["スタート"].sum() + final_start - decrease_start
                special_start = decrease_start
                dedama_sum = df["出玉"].sum()
                print(final_start,nomal_start,special_start,dedama_sum,decrease_start)

            # 回転率の計算
            denominator = dedama_sum - final_diff_ball - (special_start * 0.1)
            
            if denominator <= 0:
                kaitensuu = 0
            else:
                kaitensuu = nomal_start * 250 / denominator
            
            kitaichi = kaitensuu - border
            results[mode] = (round(kaitensuu, 2), round(final_diff_ball, 0), round(kitaichi, 2))
            
        return results

    except Exception as e:
        logger.error(f"計算エラー: {e}")
        # エラー時は0埋めで3モード分返す
        err_res = (0.0, float(final_diff_ball), 0.0)
        return {"min": err_res, "med": err_res, "max": err_res}
        """
start = ['255', '14', '441', '92', '2', '221', '6', '11', '176', '18', '63', '6', '41', '1', '33', '888', '70', '8', '19', '16', '156', '8', '56', '18', '16', '27', '13', '283']
dedama = ['1400', '1410', '', '1400', '1340', '1420', '1370', '1450', '1430', '1390', '1400', '1380', '1400', '20', '1380', '1430', '60', '1340', '1370', '1380', '1400', '1420', '1400', '50', '1450', '1400', '1390', '']
shubetu = ['大当', '確変', '最終スタート', '大当', '確変', '大当', '確変', '確変', '大当', '確変', '確変', '確変', '確変', '確変', '確 変', '大当', '確変', '確変', '確変', '確変', '確変', '確変', '確変', '確変', '確変', '確変', '確変', '最終スタート']
final_start = 283
final_diff_ball = 10855
machine_name = "Pｽｰﾊﾟｰ海物語IN沖縄6 LTP"
print(calculate_expected_value(start, dedama, shubetu, final_start, machine_name, final_diff_ball))
"""