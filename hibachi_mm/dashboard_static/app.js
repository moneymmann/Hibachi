const api=(p)=>fetch(p).then(r=>r.json());
const $=(id)=>document.getElementById(id);
let equityChart=new ApexCharts($("equityChart"),{chart:{type:'line',height:220,background:'#111827'},series:[{name:'equity',data:[]}],xaxis:{type:'datetime'}});equityChart.render();
let priceChart=new ApexCharts($("priceChart"),{chart:{type:'line',height:220,background:'#111827'},series:[{name:'mid',data:[]},{name:'mark',data:[]}],xaxis:{type:'datetime'}});priceChart.render();
async function refresh(){
  const s=await api('/api/summary');
  $('engine').textContent=JSON.stringify(s.engine,null,2);$('account').textContent=JSON.stringify(s.account,null,2);$('risk').textContent=JSON.stringify(s.risk,null,2);$('market').textContent=JSON.stringify(s.market,null,2);
  $('modeBadge').textContent=(s.engine.mode||'UNKNOWN').toUpperCase();$('modeBadge').className='badge '+((s.engine.mode||'').replace(' ','-'));
  const orders=await api('/api/open-orders');$('orders').innerHTML='<tr><th>orderId</th><th>side</th><th>role</th><th>price</th><th>qty</th><th>status</th></tr>'+orders.map(o=>`<tr><td>${o.order_id}</td><td>${o.side}</td><td>${o.order_role}</td><td>${o.price}</td><td>${o.qty}</td><td>${o.status}</td></tr>`).join('');
  const eq=(await api('/api/equity-curve')).reverse().map(x=>[x.ts_ms,Number(x.equity||0)]); equityChart.updateSeries([{name:'equity',data:eq}]);
  const pc=(await api('/api/price-curve')).reverse(); priceChart.updateSeries([{name:'mid',data:pc.map(x=>[x.ts_ms,Number(x.mid||0)])},{name:'mark',data:pc.map(x=>[x.ts_ms,Number(x.mark_price||0)])}]);
}
const ws=new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws/dashboard');
ws.onmessage=(e)=>{const d=JSON.parse(e.data);$('events').textContent=(JSON.stringify(d)+'\n'+$('events').textContent).slice(0,8000);};
refresh(); setInterval(refresh,2000);
