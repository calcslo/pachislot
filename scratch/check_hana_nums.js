const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const cutoff = '2026-04-21';
const result = [];

data.forEach(row => {
    if (row['日付'] > cutoff) {
        if (row['機種名'] === 'LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV') {
            result.push({ num: String(row['台番号']).padStart(4, '0'), name: row['機種名'] });
        }
    }
});

const unique = {};
result.forEach(r => unique[r.num] = r.name);
console.log(Object.keys(unique).sort());
