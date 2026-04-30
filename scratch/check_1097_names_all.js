const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const num1097 = data.filter(r => String(r['台番号']) === '1097');
const names = new Set(num1097.map(r => r['機種名']));
console.log("Machine 1097 all names:", Array.from(names));

const num1096 = data.filter(r => String(r['台番号']) === '1096');
const names1096 = new Set(num1096.map(r => r['機種名']));
console.log("Machine 1096 all names:", Array.from(names1096));
