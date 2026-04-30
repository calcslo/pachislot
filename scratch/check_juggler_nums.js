const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const name = 'ｼﾞｬｸﾞﾗｰｶﾞｰﾙｽﾞSS';
const entries = data.filter(r => r['機種名'] === name);
const nums = new Set(entries.map(r => String(r['台番号'])));
console.log(`${name} Numbers:`, Array.from(nums).sort());

const name2 = 'ｳﾙﾄﾗﾐﾗｸﾙｼﾞｬｸﾞﾗｰ';
const entries2 = data.filter(r => r['機種名'] === name2);
const nums2 = new Set(entries2.map(r => String(r['台番号'])));
console.log(`${name2} Numbers:`, Array.from(nums2).sort());
