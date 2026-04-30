const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const allNames = new Set();
data.forEach(row => allNames.add(row['機種名']));

const list = Array.from(allNames);
const hanaCandidates = list.filter(n => /ハナハナ|ﾊﾅﾊﾅ/.test(n));
const jugCandidates = list.filter(n => /ジャグラー|ｼﾞｬｸﾞﾗｰ/.test(n));

console.log("Hana Candidates:", hanaCandidates);
console.log("Juggler Candidates:", jugCandidates);
