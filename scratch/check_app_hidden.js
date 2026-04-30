const fs = require('fs');
const content = fs.readFileSync('d:/PycharmProjects/pachislot/docs/app.js', 'utf8');

const match = content.match(/hanahana: \['([^']+)'\]/);
if (match) {
    console.log("App.js Hana Name:", JSON.stringify(match[1]));
    console.log("App.js Hana Length:", match[1].length);
}
