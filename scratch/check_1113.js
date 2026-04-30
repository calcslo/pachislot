const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const num1113 = data.find(r => String(r['台番号']).padStart(4, '0') === '1113');
console.log("Machine 1113:", num1113 ? num1113['機種名'] : "Not found");
