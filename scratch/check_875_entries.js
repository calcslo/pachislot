const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const num875 = data.filter(r => String(r['台番号']).padStart(4, '0') === '0875');
num875.forEach(r => {
    console.log(`Date: ${r['日付']}, Name: ${r['機種名']}, Hex: ${Buffer.from(r['機種名']).toString('hex')}`);
});
