const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const result = {};
for (let i = 1092; i <= 1112; i++) {
    const num = String(i);
    const entries = data.filter(r => String(r['台番号']) === num);
    if (entries.length > 0) {
        entries.sort((a, b) => b['日付'].localeCompare(a['日付']));
        result[num] = entries[0]['日付'];
    }
}

console.log(JSON.stringify(result, null, 2));
