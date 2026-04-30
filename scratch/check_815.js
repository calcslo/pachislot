const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const num815 = data.find(r => String(r['台番号']).padStart(4, '0') === '0815');
console.log("Machine 815:", num815 ? num815['機種名'] : "Not found");
