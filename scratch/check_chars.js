const fs = require('fs');
const content = fs.readFileSync('d:/PycharmProjects/pachislot/docs/app.js', 'utf8');

const match = content.match(/hanahana: \['([^']+)'\]/);
if (match) {
    console.log("Hana Name in app.js:", match[1]);
    for (let i = 0; i < match[1].length; i++) {
        console.log(`${i}: ${match[1][i]} (U+${match[1].charCodeAt(i).toString(16).padStart(4, '0')})`);
    }
}
