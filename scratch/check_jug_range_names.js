const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const jugRange = {};
for (let i = 1092; i <= 1112; i++) {
    const num = String(i);
    const entries = data.filter(r => String(r['台番号']) === num);
    const names = new Set(entries.map(r => r['機種名']));
    if (names.size > 0) {
        jugRange[num] = Array.from(names);
    }
}

console.log(JSON.stringify(jugRange, null, 2));
