const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const cutoff = '2026-04-21';
const machineDates = {};

data.forEach(row => {
    const num = String(row['台番号']).padStart(4, '0');
    const date = row['日付'];
    if (date > cutoff) {
        if (!machineDates[num]) machineDates[num] = new Set();
        machineDates[num].add(date);
    }
});

const result = [];
for (const num in machineDates) {
    result.push({ num, count: machineDates[num].size });
}

result.sort((a, b) => parseInt(a.num) - parseInt(b.num));
console.log(result.slice(0, 50));
