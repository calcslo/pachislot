const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const machineCounts = {};
const machineNums = {};

data.forEach(row => {
    const name = row['機種名'];
    const num = String(row['台番号']).padStart(4, '0');
    if (!machineCounts[name]) {
        machineCounts[name] = 0;
        machineNums[name] = new Set();
    }
    machineCounts[name]++;
    machineNums[name].add(num);
});

for (const name in machineCounts) {
    if (name.includes('ﾊﾅﾊﾅ') || name.includes('ｼﾞｬｸﾞﾗｰ')) {
        console.log(`${name}: ${machineNums[name].size} machines`);
    }
}
