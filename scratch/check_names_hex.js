const fs = require('fs');
const appJs = fs.readFileSync('docs/app.js', 'utf8');
const machineGroupsMatch = appJs.match(/MACHINE_GROUPS = ({[\s\S]*?});/);
if (machineGroupsMatch) {
    const mg = eval('(' + machineGroupsMatch[1] + ')');
    for (const k in mg) {
        console.log(`${k}:`);
        mg[k].forEach(name => {
            const hex = Buffer.from(name).toString('hex');
            console.log(`  ${name} (${hex})`);
        });
    }
}

const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const names = [...new Set(data.map(r => r['機種名']))];
console.log('\nData names:');
names.forEach(name => {
    if (name.includes('ﾊﾅﾊﾅ') || name.includes('ｼﾞｬｸﾞﾗｰ')) {
        const hex = Buffer.from(name).toString('hex');
        console.log(`  ${name} (${hex})`);
    }
});
