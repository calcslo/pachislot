const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const multipleNames = {};
data.forEach(row => {
    const num = String(row['台番号']);
    const name = row['機種名'];
    if (!multipleNames[num]) multipleNames[num] = new Set();
    multipleNames[num].add(name);
});

for (const num in multipleNames) {
    if (multipleNames[num].size > 1) {
        const names = Array.from(multipleNames[num]);
        if (names.some(n => n.includes('ﾊﾅﾊﾅ') || n.includes('ｼﾞｬｸﾞﾗｰ'))) {
            console.log(`Machine ${num}:`, names);
        }
    }
}
