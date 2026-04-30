const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const allNames = new Set();
data.forEach(row => allNames.add(row['機種名']));

const funky = Array.from(allNames).filter(n => n.includes('ﾌｧﾝｷｰ'));
const my = Array.from(allNames).filter(n => n.includes('ﾏｲｼﾞｬｸﾞﾗｰ'));

console.log("Funky:", funky);
console.log("My:", my);
