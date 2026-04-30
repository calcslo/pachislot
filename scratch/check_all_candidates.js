const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const candidates = new Set();
data.forEach(row => {
    const name = row['機種名'];
    if (name.includes('ﾊﾅﾊﾅ') || name.includes('ｼﾞｬｸﾞﾗｰ') || name.includes('ハナハナ') || name.includes('ジャグラー')) {
        candidates.add(name);
    }
});

console.log(Array.from(candidates));
