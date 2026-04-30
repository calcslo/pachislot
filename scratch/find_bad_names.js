const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const jugModels = ['ｺﾞｰｺﾞｰｼﾞｬｸﾞﾗｰ3', 'ｳﾙﾄﾗﾐﾗｸﾙｼﾞｬｸﾞﾗｰ', 'ｼﾞｬｸﾞﾗｰｶﾞｰﾙｽﾞSS', 'ﾐｽﾀｰｼﾞｬｸﾞﾗｰ'];
const hanaModels = ['LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV'];

const badMachines = [];
data.forEach(row => {
    const name = row['機種名'];
    const num = row['台番号'];
    if (name.includes('ﾊﾅﾊﾅ') || name.includes('ｼﾞｬｸﾞﾗｰ')) {
        if (!jugModels.includes(name) && !hanaModels.includes(name)) {
            badMachines.push({ num, name });
        }
    }
});

console.log(badMachines);
