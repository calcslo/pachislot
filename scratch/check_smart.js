const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const names = new Set();
data.forEach(row => {
    if (row['機種名'].includes('ｽﾏｰﾄ')) {
        names.add(row['機種名']);
    }
});

console.log(Array.from(names));
