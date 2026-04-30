const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const num1097 = data.filter(r => String(r['台番号']).padStart(4, '0') === '1097');
console.log("Machine 1097 entries:", num1097.slice(0, 3).map(r => ({ date: r['日付'], name: r['機種名'] })));

const num1096 = data.filter(r => String(r['台番号']).padStart(4, '0') === '1096');
console.log("Machine 1096 entries:", num1096.slice(0, 3).map(r => ({ date: r['日付'], name: r['機種名'] })));
