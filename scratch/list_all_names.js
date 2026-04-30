const fs = require('fs');
const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const names = [...new Set(data.map(r => r['機種名']))];

console.log('All unique names:');
names.sort().forEach(n => {
    const count = data.filter(r => r['機種名'] === n).length;
    console.log(`${n}: ${count} entries`);
});
