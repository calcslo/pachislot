def cal_samai_from_bonus_history(start, dedama, machine_name, final_start):
    koinmochi_dict = {"ﾄﾞﾗｺﾞﾝﾊﾅﾊﾅ閃光-30":39.9,
                      "沖ﾄﾞｷ!BLACK":32,
                      "Lｽﾏｽﾛ北斗":34.7,
                      "ｼﾞｬｸﾞﾗｰｶﾞｰﾙｽﾞSS": 42,
                      "LﾓﾝｷｰﾀｰﾝV": 32,
                      "L革命機ｳﾞｧﾙｳﾞﾚｲｳﾞ": 32.3,
                      "ｺﾞｰｺﾞｰｼﾞｬｸﾞﾗｰ3": 40,
                      "Lかぐや様は告らせたい": 31,
                      "Lからくりｻｰｶｽ": 32.9,
                      "Lｺﾞｯﾄﾞｲｰﾀｰ ﾘｻﾞﾚｸｼｮﾝ": 31,
                      "L Re：ｾﾞﾛ season2": 33,
                      "Lﾀﾞﾝﾍﾞﾙ何ｷﾛ持てる?": 32.5,
                      "L戦国乙女4": 31.8,
                      "L To LOVEるﾀﾞｰｸﾈｽ": 30,
                      "Lｱﾘﾌﾚﾀ職業ﾃﾞ世界最強": 33.3,
                      "Lﾊﾞﾝﾄﾞﾘ!": 32.7,
                      "Lﾓﾝｽﾀｰﾊﾝﾀｰﾗｲｽﾞ": 32.7,
                      "Lﾁﾊﾞﾘﾖ2": 28,
                      "L防振り": 33,
                      "ｳﾙﾄﾗﾐﾗｸﾙｼﾞｬｸﾞﾗｰ": 42,
                      "甲鉄城のｶﾊﾞﾈﾘ": 33,
                      "Lｺﾞｼﾞﾗ対ｴｳﾞｧﾝｹﾞﾘｵﾝ": 33,
                      "ﾐｽﾀｰｼﾞｬｸﾞﾗｰ": 41,
                      "ﾆｭｰﾊﾟﾙｻｰSP4 太鼓の達人": 38,
                      "Lｼﾝ･ｴｳﾞｧﾝｹﾞﾘｵﾝ": 33.1,
                      "Lｽｰﾊﾟｰﾋﾞﾝｺﾞﾈｵ": 32.5,
                      "Lにゃんこ大戦争 超神速": 32.5,
                      "Lﾊﾞｼﾞﾘｽｸ絆2天膳BLACK": 31.7,
                      "L一方通行ﾄｱﾙ魔術禁書目録": 30.7,
                      "L犬夜叉2": 33.3,
                      "L聖戦士ﾀﾞﾝﾊﾞｲﾝ": 31.5,
                      "L聖闘士星矢 海皇覚醒": 31.4,
                      "L東京喰種": 31,
                      "L頭文字D 2nd": 31,
                      "ﾊｲﾊﾟｰﾗｯｼｭ": 34,
                      "Lﾙﾊﾟﾝ三世 大航海者の秘宝": 31.1,
                      "L炎炎ﾉ消防隊": 33.8,
                      "L真･一騎当千": 31,
                      "L閃乱ｶｸﾞﾗ2 ｼﾉﾋﾞﾏｽﾀｰ": 31.9,
                      "L押忍!番長4": 33,
                      "交響詩篇ｴｳﾚｶｾﾌﾞﾝTYPE-ART": 35.8,
                      "L A-SLOT+このすば": 35.2,
                      "Lｶﾞｰﾙｽﾞ&ﾊﾟﾝﾂｧｰ最終": 30.3,
                      "Lｼｬｰﾏﾝｷﾝｸﾞ": 31,
                      "Lｿﾞﾝﾋﾞﾗﾝﾄﾞｻｶﾞ": 37,
                      "LﾃﾞｨｽｸｱｯﾌﾟULTRAREMIX": 32.2,
                      "Lﾊﾞｲｵﾊｻﾞｰﾄﾞ ｳﾞｨﾚｯｼﾞ": 32.9,
                      "L黄門ちゃま天": 30.5,
                      "L今日から俺は!! ﾊﾟﾁｽﾛ編": 34.5,
                      "L主役は銭形4": 32,
                      "L転生したらｽﾗｲﾑだった件": 36,
                      "L桃太郎電鉄 ﾊﾟﾁｽﾛも定番!": 33.7,
                      "ｸﾗﾝｷｰｸﾚｽﾄ": 39.4,
                      "ﾀﾞﾝまち2": 36,
                      "L 009 RE:CYBORG": 38.7,
                      "Lｷﾝ肉ﾏﾝ 7人の悪魔超人編": 30.9,
                      "Lｺｰﾄﾞｷﾞｱｽ 復活のﾙﾙｰｼｭ": 32.3,
                      "Lｻﾗﾘｰﾏﾝ金太郎": 32,
                      "Lとある魔術の禁書目録": 34,
                      "Lﾊﾟﾁｽﾛ ﾗﾌﾞ嬢3 Wご指名": 32.4,
                      "Lﾏｸﾛｽﾌﾛﾝﾃｨｱ4": 32,
                      "Lﾏｼﾞｶﾙﾊﾛｳｨﾝ8": 34.3,
                      "Lﾜﾝﾊﾟﾝﾏﾝ": 31.9,
                      "L七つの魔剣が支配する": 33,
                      "L新･必殺仕置人 回胴": 32.4,
                      "L真･北斗無双": 31,
                      "L戦姫絶唱ｼﾝﾌｫｷﾞｱ正義の歌": 31.7,
                      "L超華祭": 34,
                      }
    start = [int(item) if item != "-" else 0 for item in start]
    dedama = [int(item) if item != "-" else 0 for item in dedama]
    if koinmochi_dict[machine_name]:
        koinmochi = koinmochi_dict[machine_name]
    else:
        koinmochi = 31
    current_medals = 0
    for i in range(len(start)):
        temp_start = start[i]
        temp_dedama = dedama[i]
        decrease_medal = temp_start / koinmochi * 50
        current_medals += temp_dedama - decrease_medal
    final_decrease_medal = final_start / koinmochi * 50
    current_medals = current_medals - final_decrease_medal
    return current_medals
#print(cal_samai_from_bonus_history())