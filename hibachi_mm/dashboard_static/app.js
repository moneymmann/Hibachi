(async()=>{const r=await fetch('/api/dashboard');const d=await r.json();document.getElementById('kpi').textContent=JSON.stringify(d);})();
