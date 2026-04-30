const fs = require('fs');
const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const names = [...new Set(data.map(r => r['機種名']))];
const matching = names.filter(n => n.includes('ﾊﾅ') || n.includes('ｼﾞｬｸﾞﾗｰ'));
console.log(matching.join('\n'));
