const fs = require('fs');
const layout = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/layout.json', 'utf8'));

layout.forEach((row, rIdx) => {
    row.forEach((cell, cIdx) => {
        if (cell === 854 || cell === '854' || cell === 855 || cell === '855') {
            console.log(`Found ${cell} at [${rIdx}, ${cIdx}]`);
        }
    });
});
