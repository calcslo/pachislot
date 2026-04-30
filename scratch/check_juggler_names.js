const fs = require('fs');
const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const machines = [];
for (let i = 1092; i <= 1112; i++) {
    const num = String(i).padStart(4, '0');
    const mData = data.filter(r => r['台番号'] === num && r['日付'] === '2026-04-29');
    if (mData.length > 0) {
        machines.push({ num, name: mData[0]['機種名'] });
    }
}

machines.forEach(m => {
    console.log(`${m.num}: ${m.name} (${Buffer.from(m.name).toString('hex')})`);
});
