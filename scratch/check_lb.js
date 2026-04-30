const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const lbNames = new Set();
data.forEach(row => {
    const name = row['機種名'];
    if (name.startsWith('LB')) {
        lbNames.add(name);
    }
});

console.log(Array.from(lbNames));
