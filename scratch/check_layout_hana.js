const fs = require('fs');
const layout = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/layout.json', 'utf8'));
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const hanaNums = new Set();
data.forEach(row => {
    if (row['機種名'] === 'LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV') {
        hanaNums.add(String(row['台番号']).padStart(4, '0'));
    }
});

let inLayout = 0;
layout.forEach(row => {
    row.forEach(cell => {
        if (cell !== '') {
            const num = String(cell).padStart(4, '0');
            if (hanaNums.has(num)) inLayout++;
        }
    });
});

console.log("Hana Hana in Data:", hanaNums.size);
console.log("Hana Hana in Layout:", inLayout);
