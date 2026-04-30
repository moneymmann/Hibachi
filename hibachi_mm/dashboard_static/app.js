async function tick(){const r=await fetch('/api/snapshot');const j=await r.json();document.getElementById('snap').textContent=JSON.stringify(j,null,2);} setInterval(tick,1000); tick();
