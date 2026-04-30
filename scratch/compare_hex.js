const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const num845 = data.find(r => String(r['台番号']).padStart(4, '0') === '0845');
const num875 = data.find(r => String(r['台番号']).padStart(4, '0') === '0875');

console.log("845 Name:", num845['機種名']);
console.log("845 Hex:", Buffer.from(num845['機種名']).toString('hex'));
console.log("875 Name:", num875['機種名']);
console.log("875 Hex:", Buffer.from(num875['機種名']).toString('hex'));
