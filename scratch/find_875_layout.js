const fs = require('fs');
const layout = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/layout.json', 'utf8'));

layout.forEach((row, rIdx) => {
    row.forEach((cell, cIdx) => {
        if (cell === 875 || cell === '875') {
            console.log(`Found 875 at [${rIdx}, ${cIdx}]`);
        }
    });
});
