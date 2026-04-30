const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const num875 = data.filter(r => String(r['台番号']).padStart(4, '0') === '0875');
num875.sort((a, b) => b['日付'].localeCompare(a['日付']));
console.log("Machine 875 latest entries:", num875.slice(0, 5).map(r => ({ date: r['日付'], model: r['機種名'] })));

const num845 = data.filter(r => String(r['台番号']).padStart(4, '0') === '0845');
num845.sort((a, b) => b['日付'].localeCompare(a['日付']));
console.log("Machine 845 latest entries:", num845.slice(0, 5).map(r => ({ date: r['日付'], model: r['機種名'] })));
