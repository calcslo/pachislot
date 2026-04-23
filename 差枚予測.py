def cal_setting_short(b_count, r_count, total_game, machine_type):
    settings_probs = {
        "マイジャグラーV":{}
        "ハナハナホウオウ〜天翔〜-30"
        "ハナハナホウオウ～天翔～-30"
        "ハナハナホウオウ?天翔?-30"
        "ゴーゴージャグラー3"
        "アイムジャグラーEX-TP"
        "アイムジャグラーEX"
        "キングハナハナ-30"
        "ドラゴンハナハナ～閃光～‐30"
        "ドラゴンハナハナ〜閃光〜‐30"
        "ドラゴンハナハナ?閃光?‐30"
        "ジャグラーガールズ"
        "ウルトラミラクルジャグラー"
        "ミスタージャグラー"
        "ハッピージャグラーVIII"
        "ファンキージャグラー2"
    }
    hokuto_settings = {
            1: {"初当たり": 1 / 383.4},
            2: {"初当たり": 1 / 370.5},
            4: {"初当たり": 1 / 297.8},
            5: {"初当たり": 1 / 258.7},
            6: {"初当たり": 1 / 235.1}
    }
    r_prob = r_count / total_game
    b_prob = b_count / total_game
    if total_game < 4000:
        return 0
    elif machine_type in settings_probs:
        closest_setting = min(settings_probs[machine_type],
                              key=lambda x: abs(settings_probs[machine_type][x]["REG"] - r_prob))
        return closest_setting
    elif machine_type == "スマスロ北斗の拳":
        n_total_game = total_game - ((b_count - r_count) * 10)
        at_prob = r_count / n_total_game
        closest_setting = min(key=lambda x: abs(hokuto_settings[x]["初当たり"] - at_prob))
        return closest_setting
    else:
        return 0
