const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const hanaNums = [];
for (let i = 845; i <= 874; i++) hanaNums.push(String(i).padStart(4, '0'));

const jugNums = [];
for (let i = 1092; i <= 1096; i++) jugNums.push(String(i)); // 1092-1096

const result = {
    hana: {},
    jug: {},
    all_hana_jug_candidates: {}
};

data.forEach(row => {
    const num = String(row['台番号']).padStart(4, '0');
    const name = row['機種名'];
    
    if (hanaNums.includes(num)) {
        result.hana[name] = (result.hana[name] || 0) + 1;
    }
    if (jugNums.includes(num)) {
        result.jug[name] = (result.jug[name] || 0) + 1;
    }
    
    if (name.includes('ﾊﾅﾊﾅ') || name.includes('ｼﾞｬｸﾞﾗｰ')) {
        result.all_hana_jug_candidates[name] = (result.all_hana_jug_candidates[name] || 0) + 1;
    }
});

console.log(JSON.stringify(result, null, 2));
