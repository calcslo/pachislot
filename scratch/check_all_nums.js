const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const hanaNums = new Set();
const jugNums = new Set();

data.forEach(row => {
    const num = String(row['台番号']).padStart(4, '0');
    const name = row['機種名'];
    
    if (name === 'LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV') {
        hanaNums.add(num);
    }
    if (['ｺﾞｰｺﾞｰｼﾞｬｸﾞﾗｰ3', 'ｳﾙﾄﾗﾐﾗｸﾙｼﾞｬｸﾞﾗｰ', 'ｼﾞｬｸﾞﾗｰｶﾞｰﾙｽﾞSS', 'ﾐｽﾀｰｼﾞｬｸﾞﾗｰ'].includes(name)) {
        jugNums.add(num);
    }
});

console.log("Hana Hana Numbers:", Array.from(hanaNums).sort());
console.log("Juggler Numbers:", Array.from(jugNums).sort());
