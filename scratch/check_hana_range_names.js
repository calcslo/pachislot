const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const hanaRange = {};
for (let i = 845; i <= 959; i++) {
    const num = String(i).padStart(4, '0');
    const entries = data.filter(r => String(r['台番号']).padStart(4, '0') === num);
    const names = new Set(entries.map(r => r['機種名']));
    if (names.size > 0) {
        hanaRange[num] = Array.from(names);
    }
}

console.log(JSON.stringify(hanaRange, null, 2));
