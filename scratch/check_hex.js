const fs = require('fs');
const content = fs.readFileSync('d:/PycharmProjects/pachislot/docs/app.js', 'utf8');
const lines = content.split('\n');

for (let i = 0; i < 15; i++) {
    console.log(`${i+1}: ${lines[i]}`);
    const hex = Buffer.from(lines[i]).toString('hex');
    console.log(`   Hex: ${hex}`);
}
