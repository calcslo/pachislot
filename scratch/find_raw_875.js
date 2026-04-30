const fs = require('fs');
const data = fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8');

const target = '"台番号": "0875"';
const idx = data.indexOf(target);
if (idx !== -1) {
    const start = Math.max(0, idx - 100);
    const end = Math.min(data.length, idx + 200);
    console.log(data.substring(start, end));
} else {
    console.log("Not found with 0875");
    const target2 = '"台番号": 875';
    const idx2 = data.indexOf(target2);
    if (idx2 !== -1) {
        const start = Math.max(0, idx2 - 100);
        const end = Math.min(data.length, idx2 + 200);
        console.log(data.substring(start, end));
    } else {
        console.log("Not found with 875");
    }
}
