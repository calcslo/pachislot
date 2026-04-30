const fs = require('fs');
const data = fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8');

const match = data.match(/"機種名":"([^"]+)"/);
if (match) {
    console.log(`Name: ${match[1]}`);
    console.log(`Hex: ${Buffer.from(match[1]).toString('hex')}`);
}
