const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const jugModels = ['ｺﾞｰｺﾞｰｼﾞｬｸﾞﾗｰ3', 'ｳﾙﾄﾗﾐﾗｸﾙｼﾞｬｸﾞﾗｰ', 'ｼﾞｬｸﾞﾗｰｶﾞｰﾙｽﾞSS', 'ﾐｽﾀｰｼﾞｬｸﾞﾗｰ'];
const latestDates = {};

data.forEach(row => {
    const num = String(row['台番号']).padStart(4, '0');
    const name = row['機種名'];
    const date = row['日付'];
    if (jugModels.includes(name)) {
        if (!latestDates[num] || date > latestDates[num].date) {
            latestDates[num] = { date, name };
        }
    }
});

const result = Object.entries(latestDates).map(([num, info]) => ({ num, ...info }));
result.sort((a, b) => parseInt(a.num) - parseInt(b.num));
console.log(result);
