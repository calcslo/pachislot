const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const allNames = new Set();
data.forEach(row => allNames.add(row['機種名']));

const fullWidthHana = Array.from(allNames).filter(n => n.includes('ハナハナ'));
const fullWidthJug = Array.from(allNames).filter(n => n.includes('ジャグラー'));

console.log("Full-width Hana:", fullWidthHana);
console.log("Full-width Jug:", fullWidthJug);
