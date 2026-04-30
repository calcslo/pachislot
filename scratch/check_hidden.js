const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const num875 = data.find(r => String(r['台番号']).padStart(4, '0') === '0875');
const name = num875['機種名'];
console.log("Name:", JSON.stringify(name));
console.log("Length:", name.length);

const num845 = data.find(r => String(r['台番号']).padStart(4, '0') === '0845');
const name845 = num845['機種名'];
console.log("Name 845:", JSON.stringify(name845));
console.log("Length 845:", name845.length);
