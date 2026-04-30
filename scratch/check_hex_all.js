const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const num1097 = data.filter(r => String(r['台番号']) === '1097');
const nameHexes = new Set(num1097.map(r => Buffer.from(r['機種名']).toString('hex')));
console.log("Machine 1097 Name Hexes:", Array.from(nameHexes));

const num1096 = data.filter(r => String(r['台番号']) === '1096');
const nameHexes1096 = new Set(num1096.map(r => Buffer.from(r['機種名']).toString('hex')));
console.log("Machine 1096 Name Hexes:", Array.from(nameHexes1096));
