const fs = require('fs');
const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const machineDates = {};
data.forEach(r => {
    const n = r['台番号'];
    if (!machineDates[n]) machineDates[n] = new Set();
    machineDates[n].add(r['日付']);
});

const names = ['1092', '1096', '1097', '1112'];
names.forEach(n => {
    if (machineDates[n]) {
        const dates = [...machineDates[n]].sort();
        console.log(`Machine ${n}: ${dates.length} days (${dates[0]} to ${dates[dates.length-1]})`);
    } else {
        console.log(`Machine ${n}: No data`);
    }
});

const latestDate = [...new Set(data.map(r => r['日付']))].sort().pop();
console.log(`\nLatest date: ${latestDate}`);
const latestMachines = data.filter(r => r['日付'] === latestDate).map(r => r['台番号']);
console.log(`Machines on latest date: ${latestMachines.length}`);
