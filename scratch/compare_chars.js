const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const num845 = data.find(r => String(r['台番号']).padStart(4, '0') === '0845');
const num875 = data.find(r => String(r['台番号']).padStart(4, '0') === '0875');

function logChars(name, label) {
    console.log(`${label}: ${name}`);
    for (let i = 0; i < name.length; i++) {
        process.stdout.write(`${name.charCodeAt(i).toString(16).padStart(4, '0')} `);
    }
    console.log();
}

logChars(num845['機種名'], "845");
logChars(num875['機種名'], "875");
