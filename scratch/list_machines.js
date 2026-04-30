const fs = require('fs');
const data = JSON.parse(fs.readFileSync('d:/PycharmProjects/pachislot/docs/data.json', 'utf8'));
const machineNames = new Set();
data.forEach(row => {
    machineNames.add(row['機種名']);
});
console.log(Array.from(machineNames).sort());
