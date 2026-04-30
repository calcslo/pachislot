const fs = require('fs');
const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const m874 = data.find(r => r['台番号'] === '0874' && r['日付'] === '2026-04-29');
const m875 = data.find(r => r['台番号'] === '0875' && r['日付'] === '2026-04-29');

console.log('0874:');
console.log(JSON.stringify(m874));
console.log('Hex:', Buffer.from(m874['機種名']).toString('hex'));

console.log('\n0875:');
console.log(JSON.stringify(m875));
console.log('Hex:', Buffer.from(m875['機種名']).toString('hex'));
