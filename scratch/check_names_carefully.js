const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const names875 = new Set();
data.filter(r => String(r['台番号']).padStart(4, '0') === '0875').forEach(r => names875.add(r['機種名']));
console.log("875 Names:", Array.from(names875));

const names1097 = new Set();
data.filter(r => String(r['台番号']) === '1097').forEach(r => names1097.add(r['機種名']));
console.log("1097 Names:", Array.from(names1097));
