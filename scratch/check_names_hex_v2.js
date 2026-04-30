const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const names = new Set();
data.forEach(row => names.add(row['機種名']));

for (const name of names) {
    if (name.includes('ﾊﾅﾊﾅ') || name.includes('ｼﾞｬｸﾞﾗｰ')) {
        console.log(`Name: "${name}"`);
        console.log(`Hex: ${Buffer.from(name).toString('hex')}`);
    }
}
