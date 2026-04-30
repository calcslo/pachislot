const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const allNames = new Set();
data.forEach(row => allNames.add(row['機種名']));

const iAmJug = Array.from(allNames).filter(n => n.includes('ｱｲﾑ'));
console.log("I am Jug:", iAmJug);
