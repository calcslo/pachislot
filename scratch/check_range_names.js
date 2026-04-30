const fs = require('fs');
const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const machines = [];
for (let i = 845; i <= 998; i++) {
    const num = String(i).padStart(4, '0');
    const mData = data.filter(r => r['台番号'] === num && r['日付'] === '2026-04-29');
    if (mData.length > 0) {
        machines.push({ num, name: mData[0]['機種名'] });
    }
}

const nameGroups = {};
machines.forEach(m => {
    if (!nameGroups[m.name]) nameGroups[m.name] = [];
    nameGroups[m.name].push(m.num);
});

for (const name in nameGroups) {
    const nums = nameGroups[name];
    console.log(`${name}: ${nums.length} machines (${nums[0]}-${nums[nums.length-1]})`);
}
