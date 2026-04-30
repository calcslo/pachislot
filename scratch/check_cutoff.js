const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));

const cutoff = '2026-04-21';
const result = {
    hana_post_cutoff: new Set(),
    jug_post_cutoff: new Set(),
    models_post_cutoff: new Set()
};

data.forEach(row => {
    const date = row['日付'];
    const num = String(row['台番号']).padStart(4, '0');
    const name = row['機種名'];
    
    if (date > cutoff) {
        if (name === 'LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV') {
            result.hana_post_cutoff.add(num);
        }
        if (['ｺﾞｰｺﾞｰｼﾞｬｸﾞﾗｰ3', 'ｳﾙﾄﾗﾐﾗｸﾙｼﾞｬｸﾞﾗｰ', 'ｼﾞｬｸﾞﾗｰｶﾞｰﾙｽﾞSS', 'ﾐｽﾀｰｼﾞｬｸﾞﾗｰ'].includes(name)) {
            result.jug_post_cutoff.add(num);
            result.models_post_cutoff.add(name);
        }
    }
});

console.log("Hana Hana Numbers > Cutoff:", Array.from(result.hana_post_cutoff).sort());
console.log("Juggler Numbers > Cutoff:", Array.from(result.jug_post_cutoff).sort());
console.log("Juggler Models > Cutoff:", Array.from(result.models_post_cutoff));
