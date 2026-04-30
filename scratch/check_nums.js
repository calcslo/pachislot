const fs = require('fs');
const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const modelToNums = {};
data.forEach(r => {
    const m = r['機種名'];
    const n = r['台番号'];
    if (!modelToNums[m]) modelToNums[m] = new Set();
    modelToNums[m].add(n);
});

for (const m in modelToNums) {
    if (m.includes('ﾊﾅﾊﾅ') || m.includes('ｼﾞｬｸﾞﾗｰ')) {
        const nums = [...modelToNums[m]].sort();
        console.log(`${m}: ${nums.length} machines (${nums[0]}-${nums[nums.length-1]})`);
        if (nums.length < 20) console.log(nums.join(', '));
    }
}
