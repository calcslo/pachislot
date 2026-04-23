import pandas as pd
def find_nearest_setting(big_prob, reg_prob, total_prob, machine_type):
    if big_prob == 0 or reg_prob == 0 or total_prob == 0:
        return None
    # 各機種の設定確率を定義
    settings_probs = {
        "マイジャグラーV": {
            1: {"BIG": 1/273.1, "REG": 1/409.6, "Total": 1/163.8},
            2: {"BIG": 1/270.8, "REG": 1/385.5, "Total": 1/159.1},
            3: {"BIG": 1/266.4, "REG": 1/336.1, "Total": 1/148.6},
            4: {"BIG": 1/254.0, "REG": 1/290.0, "Total": 1/135.4},
            5: {"BIG": 1/240.1, "REG": 1/268.6, "Total": 1/126.8},
            6: {"BIG": 1/229.1, "REG": 1/229.1, "Total": 1/114.6}
        },
        "ハナハナホウオウ〜天翔〜-30": {
            1: {"BIG": 1/297, "REG": 1/496, "Total": 1/186},  # 仮の値
            2: {"BIG": 1/284, "REG": 1/458, "Total": 1/175},  # 仮の値
            3: {"BIG": 1/273, "REG": 1/425, "Total": 1/166},  # 仮の値
            4: {"BIG": 1/262, "REG": 1/397, "Total": 1/157},  # 仮の値
            5: {"BIG": 1/249, "REG": 1/366, "Total": 1/148},  # 仮の値
            6: {"BIG": 1/236, "REG": 1/337, "Total": 1/139}   # 仮の値
        },
        "ファンキージャグラー2": {
            1: {"BIG": 1/266.4, "REG": 1/439.8, "Total": 1/165.9},  # 仮の値
            2: {"BIG": 1/259.0, "REG": 1/407.1, "Total": 1/158.3},  # 仮の値
            3: {"BIG": 1/256.0, "REG": 1/366.1, "Total": 1/150.7},  # 仮の値
            4: {"BIG": 1/249.2, "REG": 1/322.8, "Total": 1/140.6},  # 仮の値
            5: {"BIG": 1/240.1, "REG": 1/299.3, "Total": 1/133.2},  # 仮の値
            6: {"BIG": 1/219.9, "REG": 1/262.1, "Total": 1/119.6}   # 仮の値
        }
    }

    # 指定された機種の設定確率を取得
    machine_probs = settings_probs.get(machine_type, {})

    if not machine_probs:
        return None

    try:
        # 与えられた確率を数値に変換して逆数にする
        big_prob = 1 / float(big_prob)
        reg_prob = 1 / float(reg_prob)
        total_prob = 1 / float(total_prob)
    except ValueError:
        return None

    # 各設定と与えられた確率との差を計算
    diffs = {}
    for setting, probs in machine_probs.items():
        diff = abs(probs["BIG"] - big_prob) + abs(probs["REG"] - reg_prob) + abs(probs["Total"] - total_prob)
        diffs[setting] = diff

    # 差が最小の設定を返す
    nearest_setting = min(diffs, key=diffs.get)
    return nearest_setting

train = pd.read_csv("train.csv", encoding="shift-jis")
train["合成確率分母"] = train["合成確率"].str.split('/').str[1].astype(float)
train["RB確率分母"] = train["RB確率"].str.split('/').str[1].astype(float)
train["BB確率分母"] = train["BB確率"].str.split('/').str[1].astype(float)
def calculate_predicted_setting(row):
    big_prob = row['BB確率分母']  # BIG確率列の名前に応じて変更
    reg_prob = row['RB確率分母']  # REG確率列の名前に応じて変更
    total_prob = row['合成確率分母']  # TOTAL確率列の名前に応じて変更
    machine_type = row["機種名"]
    return find_nearest_setting(big_prob, reg_prob, total_prob, machine_type)

# "予測設定" 列を追加
train['設定'] = train.apply(calculate_predicted_setting, axis=1)
train.to_csv("train_test.csv", encoding="utf-8_sig")