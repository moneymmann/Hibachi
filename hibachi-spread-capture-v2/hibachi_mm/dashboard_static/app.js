const cards=document.getElementById('cards'); const log=document.getElementById('log');
const keys=['best_bid','best_ask','mid','equity','reason'];
function render(d){cards.innerHTML=''; keys.forEach(k=>{const e=document.createElement('div');e.className='card';e.innerText=`${k}: ${d[k]??'-'}`;cards.appendChild(e);});}
const ws=new WebSocket('ws://127.0.0.1:8787/ws/dashboard');
ws.onmessage=(ev)=>{const d=JSON.parse(ev.data); if(d.latest){render(d.latest)} else {render(d); log.textContent=(log.textContent+'\n'+ev.data).trim();}};
