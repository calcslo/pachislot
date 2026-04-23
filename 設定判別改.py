from scipy import stats
import math
import re

def cal_setting(b_count, r_count, total_game, machine_type, setting_ratio):
    if total_game == 0:
        return 0, None, 0, [0, 0, 0, 0, 0, 0]
    # 各機種の設定確率を定義
    settings_probs = {
        "マイジャグラーV": {
                1: {"BIG": 1 / 273.1, "REG": 1 / 409.6, "Total": 1 / 163.8, "機械割": 0.97},
                2: {"BIG": 1 / 270.8, "REG": 1 / 385.5, "Total": 1 / 159.1, "機械割": 0.98},
                3: {"BIG": 1 / 266.4, "REG": 1 / 336.1, "Total": 1 / 148.6, "機械割": 0.999},
                4: {"BIG": 1 / 254.0, "REG": 1 / 290.0, "Total": 1 / 135.4, "機械割": 1.028},
                5: {"BIG": 1 / 240.1, "REG": 1 / 268.6, "Total": 1 / 126.8, "機械割": 1.053},
                6: {"BIG": 1 / 229.1, "REG": 1 / 229.1, "Total": 1 / 114.6, "機械割": 1.094}
        },
        "ハナハナホウオウ〜天翔〜-30": {
                1: {"BIG": 1 / 297, "REG": 1 / 496, "Total": 1 / 186, "機械割": 0.97},
                2: {"BIG": 1 / 284, "REG": 1 / 458, "Total": 1 / 175, "機械割": 0.99},
                3: {"BIG": 1 / 273, "REG": 1 / 425, "Total": 1 / 166, "機械割": 1.01},
                4: {"BIG": 1 / 262, "REG": 1 / 397, "Total": 1 / 157, "機械割": 1.03},
                5: {"BIG": 1 / 249, "REG": 1 / 366, "Total": 1 / 148, "機械割": 1.06},
                6: {"BIG": 1 / 236, "REG": 1 / 337, "Total": 1 / 139, "機械割": 1.09}
        },
        "ハナハナホウオウ～天翔～-30": {
            1: {"BIG": 1 / 297, "REG": 1 / 496, "Total": 1 / 186, "機械割": 0.97},
            2: {"BIG": 1 / 284, "REG": 1 / 458, "Total": 1 / 175, "機械割": 0.99},
            3: {"BIG": 1 / 273, "REG": 1 / 425, "Total": 1 / 166, "機械割": 1.01},
            4: {"BIG": 1 / 262, "REG": 1 / 397, "Total": 1 / 157, "機械割": 1.03},
            5: {"BIG": 1 / 249, "REG": 1 / 366, "Total": 1 / 148, "機械割": 1.06},
            6: {"BIG": 1 / 236, "REG": 1 / 337, "Total": 1 / 139, "機械割": 1.09}
        },
        "ハナハナホウオウ?天翔?-30": {
            1: {"BIG": 1 / 297, "REG": 1 / 496, "Total": 1 / 186, "機械割": 0.97},
            2: {"BIG": 1 / 284, "REG": 1 / 458, "Total": 1 / 175, "機械割": 0.99},
            3: {"BIG": 1 / 273, "REG": 1 / 425, "Total": 1 / 166, "機械割": 1.01},
            4: {"BIG": 1 / 262, "REG": 1 / 397, "Total": 1 / 157, "機械割": 1.03},
            5: {"BIG": 1 / 249, "REG": 1 / 366, "Total": 1 / 148, "機械割": 1.06},
            6: {"BIG": 1 / 236, "REG": 1 / 337, "Total": 1 / 139, "機械割": 1.09}
        },
        "ゴーゴージャグラー3": {
            1: {"BIG": 1 / 259, "REG": 1 / 354.2, "Total": 1 / 149.6, "機械割": 0.972},
            2: {"BIG": 1 / 258, "REG": 1 / 332.7, "Total": 1 / 145.3, "機械割": 0.982},
            3: {"BIG": 1 / 257, "REG": 1 / 306.2, "Total": 1 / 139.7, "機械割": 0.994},
            4: {"BIG": 1 / 254, "REG": 1 / 268.6, "Total": 1 / 130.5, "機械割": 1.016},
            5: {"BIG": 1 / 247.3, "REG": 1 / 247.3, "Total": 1 / 123.7, "機械割": 1.038},
            6: {"BIG": 1 / 234.9, "REG": 1 / 234.9, "Total": 1 / 117.4, "機械割": 1.065}
        },
        "アイムジャグラーEX-TP": {
            1: {"BIG": 1 / 273.1, "REG": 1 / 496, "Total": 1 / 186, "機械割": 0.97},
            2: {"BIG": 1 / 269.7, "REG": 1 / 399.6, "Total": 1 / 175, "機械割": 0.98},
            3: {"BIG": 1 / 269.7, "REG": 1 / 331.0, "Total": 1 / 166, "機械割": 0.995},
            4: {"BIG": 1 / 259.0, "REG": 1 / 315.1, "Total": 1 / 157, "機械割": 1.011},
            5: {"BIG": 1 / 259.0, "REG": 1 / 255.0, "Total": 1 / 148, "機械割": 1.033},
            6: {"BIG": 1 / 255.0, "REG": 1 / 255.0, "Total": 1 / 139, "機械割": 1.055}
        },
        "アイムジャグラーEX": {
            1: {"BIG": 1 / 287.43, "REG": 1 / 455.11, "Total": 1 / 176.17, "機械割": 0.97},
            2: {"BIG": 1 / 282.48, "REG": 1 / 442.81, "Total": 1 / 172.46, "機械割": 0.98},
            3: {"BIG": 1 / 282.48, "REG": 1 / 348.59, "Total": 1 / 156.03, "機械割": 0.995},
            4: {"BIG": 1 / 273.06, "REG": 1 / 321.25, "Total": 1 / 147.60, "機械割": 1.011},
            5: {"BIG": 1 / 273.06, "REG": 1 / 268.59, "Total": 1 / 135.40, "機械割": 1.033},
            6: {"BIG": 1 / 268.59, "REG": 1 / 268.59, "Total": 1 / 134.29, "機械割": 1.055}
        },
        "キングハナハナ-30": {
            1: {"BIG": 1 / 292, "REG": 1 / 489, "Total": 1 / 183, "機械割": 0.97},
            2: {"BIG": 1 / 280, "REG": 1 / 452, "Total": 1 / 172, "機械割": 0.99},
            3: {"BIG": 1 / 268, "REG": 1 / 420, "Total": 1 / 163, "機械割": 1.01},
            4: {"BIG": 1 / 257, "REG": 1 / 390, "Total": 1 / 154, "機械割": 1.04},
            5: {"BIG": 1 / 244, "REG": 1 / 360, "Total": 1 / 145, "機械割": 1.07},
            6: {"BIG": 1 / 232, "REG": 1 / 332, "Total": 1 / 136, "機械割": 1.10}
        },
        "ドラゴンハナハナ～閃光～‐30": {
            1: {"BIG": 1 / 256, "REG": 1 / 642, "Total": 1 / 183, "機械割": 0.97},
            2: {"BIG": 1 / 246, "REG": 1 / 585, "Total": 1 / 173, "機械割": 0.99},
            3: {"BIG": 1 / 235, "REG": 1 / 537, "Total": 1 / 163, "機械割": 1.01},
            4: {"BIG": 1 / 224, "REG": 1 / 489, "Total": 1 / 153, "機械割": 1.04},
            5: {"BIG": 1 / 212, "REG": 1 / 442, "Total": 1 / 143, "機械割": 1.07},
            6: {"BIG": 1 / 199, "REG": 1 / 399, "Total": 1 / 133, "機械割": 1.10}
        },
        "ドラゴンハナハナ〜閃光〜‐30": {
            1: {"BIG": 1 / 256, "REG": 1 / 642, "Total": 1 / 183, "機械割": 0.97},
            2: {"BIG": 1 / 246, "REG": 1 / 585, "Total": 1 / 173, "機械割": 0.99},
            3: {"BIG": 1 / 235, "REG": 1 / 537, "Total": 1 / 163, "機械割": 1.01},
            4: {"BIG": 1 / 224, "REG": 1 / 489, "Total": 1 / 153, "機械割": 1.04},
            5: {"BIG": 1 / 212, "REG": 1 / 442, "Total": 1 / 143, "機械割": 1.07},
            6: {"BIG": 1 / 199, "REG": 1 / 399, "Total": 1 / 133, "機械割": 1.10}
        },
        "ドラゴンハナハナ?閃光?‐30": {
            1: {"BIG": 1 / 256, "REG": 1 / 642, "Total": 1 / 183, "機械割": 0.97},
            2: {"BIG": 1 / 246, "REG": 1 / 585, "Total": 1 / 173, "機械割": 0.99},
            3: {"BIG": 1 / 235, "REG": 1 / 537, "Total": 1 / 163, "機械割": 1.01},
            4: {"BIG": 1 / 224, "REG": 1 / 489, "Total": 1 / 153, "機械割": 1.04},
            5: {"BIG": 1 / 212, "REG": 1 / 442, "Total": 1 / 143, "機械割": 1.07},
            6: {"BIG": 1 / 199, "REG": 1 / 399, "Total": 1 / 133, "機械割": 1.10}
        },
        "ジャグラーガールズ": {
            1: {"BIG": 1 / 273.1, "REG": 1 / 381.0, "Total": 1 / 159.1, "機械割": 0.97},
            2: {"BIG": 1 / 270.8, "REG": 1 / 350.5, "Total": 1 / 152.8, "機械割": 0.979},
            3: {"BIG": 1 / 260.1, "REG": 1 / 316.6, "Total": 1 / 142.8, "機械割": 0.999},
            4: {"BIG": 1 / 250.1, "REG": 1 / 281.3, "Total": 1 / 132.4, "機械割": 1.021},
            5: {"BIG": 1 / 243.6, "REG": 1 / 270.8, "Total": 1 / 128.3, "機械割": 1.04},
            6: {"BIG": 1 / 226.0, "REG": 1 / 252.1, "Total": 1 / 119.2, "機械割": 1.075}
        },
        "ハッピージャグラーVIII": {
            1: {"BIG": 1 / 273.1, "REG": 1 / 397.2, "Total": 1 / 161.8, "機械割": 0.97},
            2: {"BIG": 1 / 270.8, "REG": 1 / 362.1, "Total": 1 / 154.9, "機械割": 0.981},
            3: {"BIG": 1 / 263.2, "REG": 1 / 332.7, "Total": 1 / 146.9, "機械割": 0.999},
            4: {"BIG": 1 / 254.0, "REG": 1 / 300.6, "Total": 1 / 137.7, "機械割": 1.029},
            5: {"BIG": 1 / 239.2, "REG": 1 / 273.1, "Total": 1 / 127.5, "機械割": 1.058},
            6: {"BIG": 1 / 226.0, "REG": 1 / 256.0, "Total": 1 / 120.0, "機械割": 1.084}
        },
        "ファンキージャグラー2": {
                1: {"BIG": 1 / 266.4, "REG": 1 / 439.8, "Total": 1 / 165.9, "機械割": 0.97},
                2: {"BIG": 1 / 259.0, "REG": 1 / 407.1, "Total": 1 / 158.3, "機械割": 0.985},
                3: {"BIG": 1 / 256.0, "REG": 1 / 366.1, "Total": 1 / 150.7, "機械割": 0.998},
                4: {"BIG": 1 / 249.2, "REG": 1 / 322.8, "Total": 1 / 140.6, "機械割": 1.02},
                5: {"BIG": 1 / 240.1, "REG": 1 / 299.3, "Total": 1 / 133.2, "機械割": 1.043},
                6: {"BIG": 1 / 219.9, "REG": 1 / 262.1, "Total": 1 / 119.6, "機械割": 1.09}
        }
    }

    big_p = []
    reg_p = []
    total_p = []
    for i in range(1, 7):
        big_p.append(stats.binom.pmf(b_count, total_game, settings_probs[machine_type][i]["BIG"]))
        reg_p.append(stats.binom.pmf(r_count, total_game, settings_probs[machine_type][i]["REG"]))
        total_p.append(stats.binom.pmf(b_count + r_count, total_game, settings_probs[machine_type][i]["Total"]))



    setting_prob_list_b = [
        setting_ratio[5] * big_p[5] / sum(setting_ratio[j] * big_p[j] for j in range(6)),
        setting_ratio[4] * big_p[4] / sum(setting_ratio[j] * big_p[j] for j in range(6)),
        setting_ratio[3] * big_p[3] / sum(setting_ratio[j] * big_p[j] for j in range(6)),
        setting_ratio[2] * big_p[2] / sum(setting_ratio[j] * big_p[j] for j in range(6)),
        setting_ratio[1] * big_p[1] / sum(setting_ratio[j] * big_p[j] for j in range(6)),
        setting_ratio[0] * big_p[0] / sum(setting_ratio[j] * big_p[j] for j in range(6))
    ]

    setting_prob_list_r = [
        setting_ratio[5] * reg_p[5] / sum(setting_ratio[j] * reg_p[j] for j in range(6)),
        setting_ratio[4] * reg_p[4] / sum(setting_ratio[j] * reg_p[j] for j in range(6)),
        setting_ratio[3] * reg_p[3] / sum(setting_ratio[j] * reg_p[j] for j in range(6)),
        setting_ratio[2] * reg_p[2] / sum(setting_ratio[j] * reg_p[j] for j in range(6)),
        setting_ratio[1] * reg_p[1] / sum(setting_ratio[j] * reg_p[j] for j in range(6)),
        setting_ratio[0] * reg_p[0] / sum(setting_ratio[j] * reg_p[j] for j in range(6))
    ]

    setting_prob_list_t = [
        setting_ratio[5] * total_p[5] / sum(setting_ratio[j] * total_p[j] for j in range(6)),
        setting_ratio[4] * total_p[4] / sum(setting_ratio[j] * total_p[j] for j in range(6)),
        setting_ratio[3] * total_p[3] / sum(setting_ratio[j] * total_p[j] for j in range(6)),
        setting_ratio[2] * total_p[2] / sum(setting_ratio[j] * total_p[j] for j in range(6)),
        setting_ratio[1] * total_p[1] / sum(setting_ratio[j] * total_p[j] for j in range(6)),
        setting_ratio[0] * total_p[0] / sum(setting_ratio[j] * total_p[j] for j in range(6))
    ]

    r_bi_list_b = []
    r_bi_list_r = []
    r_bi_list_t = []
    settingi_prob_rev_list_b = []
    settingi_prob_rev_list_r = []
    settingi_prob_rev_list_t = []

    # r_bi の計算と settingi_prob_rev の計算
    for i in range(1, 7):
        r_bi_b = math.sqrt(1.96 ** 2 * (1 / settings_probs[machine_type][i]["BIG"] - 1) / total_game)
        r_bi_list_b.append(r_bi_b)
    #print(r_bi_list_b)

    for i in range(1, 7):
        r_bi_r = math.sqrt(1.96 ** 2 * (1 / settings_probs[machine_type][i]["REG"] - 1) / total_game)
        r_bi_list_r.append(r_bi_r)
    #print(r_bi_list_r)

    for i in range(1, 7):
        r_bi_t = math.sqrt(1.96 ** 2 * (1 / settings_probs[machine_type][i]["Total"] - 1) / total_game)
        r_bi_list_t.append(r_bi_t)

    for i in range(1, 7):
        settingi_prob_rev_b = setting_prob_list_b[i-1] / (r_bi_list_b[i-1] ** 2)
        settingi_prob_rev_list_b.append(settingi_prob_rev_b)
    #print(settingi_prob_rev_list_b)

    for i in range(1, 7):
        settingi_prob_rev_r = setting_prob_list_r[i-1] / (r_bi_list_r[i-1] ** 2)
        settingi_prob_rev_list_r.append(settingi_prob_rev_r)
    #print(settingi_prob_rev_list_r)

    for i in range(1, 7):
        settingi_prob_rev_t = setting_prob_list_t[i-1] / (r_bi_list_t[i-1] ** 2)
        settingi_prob_rev_list_t.append(settingi_prob_rev_t)

    # settingi_prob_rev2 の計算
    total_setting_prob_rev_sum_b = sum(settingi_prob_rev_list_b)
    settingi_prob_rev2_list_b = [settingi_prob_rev_b / total_setting_prob_rev_sum_b for settingi_prob_rev_b in settingi_prob_rev_list_b]
    settingi_prob_rev2_list_b.reverse()
    #print(settingi_prob_rev2_list_b)

    total_setting_prob_rev_sum_r = sum(settingi_prob_rev_list_r)
    settingi_prob_rev2_list_r = [settingi_prob_rev_r / total_setting_prob_rev_sum_r for settingi_prob_rev_r in settingi_prob_rev_list_r]
    settingi_prob_rev2_list_r.reverse()
    #print(settingi_prob_rev2_list_r)

    total_setting_prob_rev_sum_t = sum(settingi_prob_rev_list_t)
    settingi_prob_rev2_list_t = [settingi_prob_rev_t / total_setting_prob_rev_sum_t for settingi_prob_rev_t in
                                 settingi_prob_rev_list_t]
    settingi_prob_rev2_list_t.reverse()


    # 設定ごとの事後確率(BIGとREGを組み合わせた結果)
    #print("設定ごとの事後確率(BIGとREGを組み合わせた結果):")
    prob_list = []
    combine_list = []
    for i in range(6):
        combined_prob = (settingi_prob_rev2_list_b[i] * settingi_prob_rev2_list_r[i])
        combine_list.append(combined_prob)
        #combined_prob = (settingi_prob_rev2_list_b[i] + settingi_prob_rev2_list_r[i]) / 2  # BIGとREGの信頼度を単純に平均する
        #print(f"設定 {i+1}: {combined_prob:.6f}")
        #prob_list.append(combined_prob)
    for i in range (6):
        combined_prob2 = combine_list[i] / sum(combine_list)
        prob_list.append(combined_prob2)
    #print(prob_list)
    win_rate = sum(settings_probs[machine_type][i]["機械割"] * prob_list[i-1] for i in range(1,7))
    ave_setting = sum(i * prob_list[i-1] for i in range(1,7))
    #print(win_rate)
    #print(ave_setting)
    prob_setting = prob_list.index(max(prob_list)) + 1
    prob_setting = settingi_prob_rev2_list_r.index(max(settingi_prob_rev2_list_r)) + 1
    return win_rate, prob_setting, ave_setting, settingi_prob_rev2_list_r, settingi_prob_rev2_list_t, prob_list


list = [0.3, 0.2, 0.1, 0.08, 0.06, 0.04]
list2 = [0.1, 0.17, 0.225, 0.232, 0.174, 0.085]
print(cal_setting(49, 26, 9437, "ドラゴンハナハナ～閃光～‐30", list2))
