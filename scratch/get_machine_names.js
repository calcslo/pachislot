const fs = require('fs');
const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const names = [...new Set(data.map(r => r['機種名']))];
console.log(names.sort().join('\n'));
