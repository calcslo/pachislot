const fs = require('fs');
const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const machines = ['0845', '0874', '0875', '0953', '1092', '1096', '1097'];
machines.forEach(n => {
    const mData = data.filter(r => r['台番号'] === n).sort((a, b) => b['日付'].localeCompare(a['日付']));
    console.log(`Machine ${n}:`);
    const recent = mData.slice(0, 5);
    recent.forEach(r => console.log(`  ${r['日付']}: ${r['機種名']}`));
    const old = mData.filter(r => r['日付'] <= '2026-04-21').slice(0, 2);
    old.forEach(r => console.log(`  ${r['日付']} (OLD): ${r['機種名']}`));
});
