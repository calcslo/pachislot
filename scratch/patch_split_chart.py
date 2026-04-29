new_func = (
    "function renderSplitBarChart(splitWrapperId, labelCanvasId, barCanvasId, items, opts={}, chartKey='machine'){\n"
    "    const step = opts.step || 500;\n"
    "    const initRange = opts.initRange || 4000;\n"
    "    const rowH = opts.rowH || 18;\n"
    "    const fontSize = opts.fontSize || 11;\n"
    "    const labelRatio = 0.4;\n"
    "\n"
    "    if(!items.length) return;\n"
    "    const vals = items.map(i=>i.avg);\n"
    "    const dataMax = vals.reduce((a,b)=>Math.max(a,b), 0);\n"
    "    const dataMin = vals.reduce((a,b)=>Math.min(a,b), 0);\n"
    "    const axisMax = Math.max(initRange, Math.ceil(Math.abs(dataMax)/step)*step);\n"
    "    const axisMin = Math.min(-initRange, -Math.ceil(Math.abs(dataMin)/step)*step);\n"
    "\n"
    "    const n = items.length;\n"
    "    const h = Math.max(200, n * rowH + 50);\n"
    "\n"
    "    const labelCvs = document.getElementById(labelCanvasId);\n"
    "    if(!labelCvs) return;\n"
    "    const labelPane = labelCvs.parentElement;\n"
    "\n"
    '    const tmpCtx = labelCvs.getContext("2d");\n'
    "    tmpCtx.font = `bold ${fontSize}px Inter, Noto Sans JP, sans-serif`;\n"
    "    let maxLW = 80;\n"
    "    items.forEach(i=>{ const w=tmpCtx.measureText(i.label).width; if(w>maxLW)maxLW=w; });\n"
    "    const labelCvsW = Math.ceil(maxLW) + 24;\n"
    "\n"
    "    labelCvs.width = labelCvsW;\n"
    "    labelCvs.height = h;\n"
    '    labelCvs.style.width = labelCvsW + "px";\n'
    '    labelCvs.style.height = h + "px";\n'
    "\n"
    "    const wrapper = splitWrapperId ? document.getElementById(splitWrapperId) : labelPane.parentElement;\n"
    "    const totalW = wrapper ? (wrapper.clientWidth || 600) : 600;\n"
    "    const labelPaneW = Math.floor(totalW * labelRatio);\n"
    "    const barPaneW = totalW - labelPaneW;\n"
    "\n"
    '    labelPane.style.width = labelPaneW + "px";\n'
    '    labelPane.style.flexShrink = "0";\n'
    '    labelPane.style.overflowX = "auto";\n'
    '    labelPane.style.overflowY = "hidden";\n'
    '    labelPane.style.height = h + "px";\n'
    "\n"
    "    const barCvs = document.getElementById(barCanvasId);\n"
    "    if(!barCvs) return;\n"
    "    const barPane = barCvs.parentElement;\n"
    '    barPane.style.overflowX = "auto";\n'
    '    barPane.style.overflowY = "hidden";\n'
    '    barPane.style.height = h + "px";\n'
    "\n"
    "    const totalRange = axisMax - axisMin;\n"
    "    const initTotalRange = initRange * 2;\n"
    "    const scaleFactor = Math.max(1, totalRange / initTotalRange);\n"
    "    const barCvsW = Math.max(barPaneW, Math.round(barPaneW * scaleFactor));\n"
    '    barCvs.style.width = barCvsW + "px";\n'
    '    barCvs.style.height = h + "px";\n'
    "\n"
    '    const keyL = chartKey+"-labels", keyB = chartKey;\n'
    "    if(charts[keyL])charts[keyL].destroy();\n"
    "    if(charts[keyB])charts[keyB].destroy();\n"
    "\n"
    "    const gridColorFn = (ctx2) => {\n"
    "        const v = ctx2.tick ? ctx2.tick.value : (ctx2.value ?? 0);\n"
    '        return (v === 0) ? "rgba(255,255,255,0.4)" : "rgba(128,128,128,0.15)";\n'
    "    };\n"
    "\n"
    "    charts[keyL] = new Chart(labelCvs, {\n"
    '        type: "bar",\n'
    "        data: { labels: items.map(i=>i.label), datasets: [{ data: vals, backgroundColor:'transparent', borderColor:'transparent' }] },\n"
    "        options: {\n"
    "            indexAxis:'y', responsive:false, maintainAspectRatio:false, animation:false,\n"
    "            plugins: { legend:{display:false}, datalabels:{display:false}, tooltip:{enabled:false} },\n"
    "            scales: {\n"
    "                x: { display:false, min:axisMin, max:axisMax },\n"
    "                y: { position:'right', grid:{display:false},\n"
    "                     ticks:{ font:{size:fontSize,weight:'bold'}, autoSkip:false, maxRotation:0, color:Chart.defaults.color },\n"
    "                     afterFit(scale){ scale.width = labelCvsW; } }\n"
    "            },\n"
    "            layout: { padding:{ top:0, bottom:30 } }\n"
    "        }\n"
    "    });\n"
    "\n"
    "    charts[keyB] = new Chart(barCvs, {\n"
    "        type:'bar',\n"
    "        data:{ labels:items.map(i=>i.label), datasets:[{ label:'差枚', data:vals,\n"
    "            backgroundColor:vals.map(v=>v>0?'rgba(78,143,224,0.78)':'rgba(224,92,92,0.78)'), borderRadius:3 }] },\n"
    "        options:{\n"
    "            indexAxis:'y', responsive:false, maintainAspectRatio:false,\n"
    "            plugins:{ legend:{display:false}, datalabels:{display:false} },\n"
    "            scales:{\n"
    "                x:{ min:axisMin, max:axisMax, ticks:{stepSize:step,font:{size:10}}, grid:{color:gridColorFn} },\n"
    "                y:{ display:false, grid:{display:false}, ticks:{autoSkip:false} }\n"
    "            },\n"
    "            layout:{ padding:{ top:0, bottom:0 } }\n"
    "        }\n"
    "    });\n"
    "}\n"
)

lines = open('docs/app.js', encoding='utf-8').readlines()
# Lines 763-851 (0-indexed: 762-850)
result = lines[:762] + [new_func] + lines[851:]
open('docs/app.js', 'w', encoding='utf-8').writelines(result)
print('Done, total lines:', len(result))
