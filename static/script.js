// Minimal veshcalc frontend logic
const exprInput = document.getElementById('expr-input');
const addBtn = document.getElementById('add-btn');
const exprList = document.getElementById('expr-list');
const xminInput = document.getElementById('xmin');
const xmaxInput = document.getElementById('xmax');
const exportBtn = document.getElementById('export-btn');
const messageEl = document.getElementById('message');
const algInput = document.getElementById('alg-input');
const algResult = document.getElementById('alg-result');
const keyboard = document.querySelector('.keyboard');

let expressions = [];
let debounceTimer = null;
const exampleButtons = document.querySelectorAll('.example');
const view3dCheckbox = document.getElementById('view3d');

function debounce(fn, delay=300){
  return function(...args){
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(()=>fn(...args), delay);
  }
}

function renderExprList(){
  exprList.innerHTML = '';
  expressions.forEach((e, i)=>{
    const div = document.createElement('div');
    div.className = 'expr-item';
    div.innerHTML = `<span class="expr-text">${e}</span>`;
    const del = document.createElement('button');
    del.textContent = 'Delete';
    del.onclick = ()=>{ expressions.splice(i,1); updateAll(); };
    const diff = document.createElement('button');
    diff.textContent = 'Differentiate';
    diff.onclick = ()=>{ expressions[i] = 'diff(' + e + ')'; updateAll(); };
    div.appendChild(diff);
    div.appendChild(del);
    exprList.appendChild(div);
  })
}

async function evaluateExpression(expr){
  const payload = { expression: expr, xmin: parseFloat(xminInput.value), xmax: parseFloat(xmaxInput.value) };
  const res = await fetch('/evaluate', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
  const json = await res.json();
  if(!res.ok){
    throw new Error(json.error || 'Evaluation failed');
  }
  return json;
}

function displayMessage(text, isError=true){
  messageEl.textContent = text || '';
  messageEl.style.color = isError ? '#b91c1c' : '#065f46';
  if(text){
    setTimeout(()=>{ messageEl.textContent = '' }, 6000);
  }
}

// Keyboard handling
if(keyboard){
  keyboard.addEventListener('click', (e)=>{
    const t = e.target;
    if(!t.classList.contains('key')) return;
    const v = t.textContent;
    if(v === 'C'){
      exprInput.value = '';
      algInput.value = '';
      return;
    }
    // If the algebra input is focused, append there, else main expr
    if(document.activeElement === algInput){
      algInput.value += v;
    } else {
      exprInput.value += v;
    }
  })
}

// Algebra actions
document.querySelectorAll('.alg-btn').forEach(btn=>{
  btn.addEventListener('click', async ()=>{
    const action = btn.dataset.action;
    const expr = algInput.value.trim();
    if(!expr) { displayMessage('Enter expression for algebra', true); return; }
    try{
      const res = await fetch('/algebra', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ action, expr }) });
      const json = await res.json();
      if(!res.ok){ displayMessage(json.error || 'Algebra error', true); return; }
      algResult.textContent = Array.isArray(json.result) ? json.result.join(', ') : json.result;
    }catch(err){ displayMessage('Algebra request failed', true); }
  })
})

async function updateAll(){
  renderExprList();
  const traces = [];
  const rootMarkers = [];
  for(const e of expressions){
    try{
      const data = await evaluateExpression(e);
      if(data.mode === 'cartesian'){
        traces.push({ x: data.x, y: data.y, name: data.expr });
      } else if(data.mode === 'parametric'){
        traces.push({ x: data.x, y: data.y, mode: 'lines', name: data.expr });
      } else if(data.mode === 'implicit'){
        // show contour using z as intensity
        traces.push({ z: data.Z, x: data.X[0], y: data.Y.map(r=>r[0]), type: 'contour', name: data.expr });
      } else if(data.mode === 'equation'){
        // plot the function f(x)=left-right and add root markers
        traces.push({ x: data.x, y: data.y, name: data.expr });
        if(data.roots && data.roots.length){
          data.roots.forEach(r=>{ if(r !== null){ rootMarkers.push({ x:[r], y:[0], mode:'markers', marker:{size:10}, name: data.expr + ' root' }) } })
        }
      } else if(data.mode === 'surface'){
        // 3D surface
        const X = data.X; const Y = data.Y; const Z = data.Z;
        if(view3dCheckbox.checked){
          traces.push({ x: X[0], y: Y.map(r=>r[0]), z: Z, type: 'surface', name: data.expr });
        } else {
          traces.push({ z: Z, x: X[0], y: Y.map(r=>r[0]), type: 'contour', name: data.expr });
        }
      } else if(data.mode === 'polar'){
        traces.push({ x: data.x, y: data.y, mode: 'lines', name: data.expr });
      } else if(data.mode === 'inequality'){
        // render mask as heatmap/contour
        traces.push({ z: data.Z, x: data.X[0], y: data.Y.map(r=>r[0]), type: 'heatmap', colorscale:'Blues', opacity:0.6, name: data.expr });
      }
    }catch(err){
      console.error('Error:', err.message);
    }
  }
  Plotly.react('plot', traces.concat(rootMarkers), { margin: { t: 30 } });
}

addBtn.addEventListener('click', ()=>{
  const val = exprInput.value.trim();
  if(!val) return;
  // validate with server before adding
  evaluateExpression(val).then(_=>{
    expressions.push(val);
    exprInput.value = '';
    displayMessage('Expression added', false);
    updateAll();
  }).catch(err=>{
    displayMessage('Error: ' + err.message, true);
    console.error('Validation error:', err.message);
  });
});

exampleButtons.forEach(btn=>{
  btn.addEventListener('click', ()=>{
    const val = btn.textContent.trim();
    expressions.push(val);
    updateAll();
  })
});

view3dCheckbox.addEventListener('change', ()=>updateAll());

xminInput.addEventListener('change', debounce(()=>updateAll(), 250));
xmaxInput.addEventListener('change', debounce(()=>updateAll(), 250));

exportBtn.addEventListener('click', ()=>{
  Plotly.toImage('plot', {format: 'png', height: 600, width: 800}).then(function(url){
    const a = document.createElement('a');
    a.href = url;
    a.download = 'veshcalc.png';
    document.body.appendChild(a);
    a.click();
    a.remove();
  })
});

// initial empty plot
Plotly.newPlot('plot', [], { margin: { t: 30 } });
