const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const num875 = data.find(r => String(r['台番号']).padStart(4, '0') === '0875');
console.log("Machine 875:", num875 ? num875['機種名'] : "Not found");

const num1097 = data.find(r => String(r['台番号']).padStart(4, '0') === '1097');
console.log("Machine 1097:", num1097 ? num1097['機種名'] : "Not found");
