(()=>{
  if(window.GlucoPlatePantryUi)return;

  const activeProfileId=()=>window.GlucoPlateUserData?.activeProfileId?.()||localStorage.getItem('glucoplate_active_profile_id')||'default';
  const token=()=>localStorage.getItem('glucoplate_firebase_id_token');
  const headers=()=>({'Content-Type':'application/json','Authorization':`Bearer ${token()}`});
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

  async function api(path,options={}){
    const response=await fetch(path,{...options,headers:{...headers(),...(options.headers||{})}});
    if(!response.ok){
      let detail='Pantry request failed.';
      try{detail=(await response.json()).detail||detail}catch(_error){}
      throw new Error(detail);
    }
    return response.status===204?null:response.json();
  }

  function ensureStyles(){
    if(document.getElementById('pantryUiStyles'))return;
    const style=document.createElement('style');
    style.id='pantryUiStyles';
    style.textContent=`
      .pantry-launcher{position:fixed;right:18px;bottom:86px;z-index:72;border:0;border-radius:999px;padding:12px 16px;background:#245d46;color:#fff;font-weight:900;box-shadow:0 12px 30px rgba(0,0,0,.18)}
      .pantry-overlay{position:fixed;inset:0;z-index:95;background:rgba(33,31,29,.58);backdrop-filter:blur(14px);display:grid;place-items:center;padding:16px}
      .pantry-panel{width:min(900px,100%);max-height:92dvh;overflow:auto;background:var(--bg,#f7f4ef);border-radius:24px;padding:22px}
      .pantry-head,.pantry-summary,.pantry-actions{display:flex;gap:12px;align-items:center;justify-content:space-between}.pantry-head h2{margin:4px 0}.pantry-close{border:1px solid #ddd;background:#fff;border-radius:12px;width:40px;height:40px}
      .pantry-summary{justify-content:flex-start;flex-wrap:wrap;margin:14px 0}.pantry-pill{padding:7px 10px;border-radius:999px;background:#fff;border:1px solid #e7ded4;font-size:.78rem;font-weight:800}.pantry-pill.warn{background:#fff3d6}.pantry-pill.danger{background:#ffe3df}
      .pantry-form{display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr auto;gap:8px;margin:14px 0}.pantry-form input,.pantry-form select{min-width:0;padding:10px;border:1px solid #ddd;border-radius:12px;background:#fff}.pantry-form button{border:0;border-radius:12px;padding:10px 14px;background:#245d46;color:#fff;font-weight:900}
      .pantry-list{display:grid;gap:9px}.pantry-item{display:grid;grid-template-columns:1fr auto auto;gap:10px;align-items:center;background:#fff;border:1px solid #e7ded4;border-radius:16px;padding:13px}.pantry-item small{display:block;color:#756f69;margin-top:4px}.pantry-status{font-size:.72rem;font-weight:900;padding:6px 8px;border-radius:999px;background:#eef5f1}.pantry-status.use_soon{background:#fff3d6}.pantry-status.expired{background:#ffe3df}.pantry-delete{border:0;background:transparent;font-size:1.1rem}.pantry-empty{text-align:center;padding:30px;color:#756f69}
      @media(max-width:700px){.pantry-form{grid-template-columns:1fr 1fr}.pantry-form .wide,.pantry-form button{grid-column:1/-1}.pantry-item{grid-template-columns:1fr auto}.pantry-status{grid-column:1}.pantry-delete{grid-column:2;grid-row:1/3}}
    `;
    document.head.appendChild(style);
  }

  async function load(){
    const result=await api(`/api/pantry/items?profile_id=${encodeURIComponent(activeProfileId())}`);
    renderList(result);
    return result;
  }

  function renderList(result){
    const list=document.getElementById('pantryItemList');
    const summary=document.getElementById('pantrySummary');
    if(!list||!summary)return;
    summary.innerHTML=`<span class="pantry-pill">${result.count||0} items</span><span class="pantry-pill warn">${result.use_soon_count||0} use soon</span><span class="pantry-pill danger">${result.expired_count||0} expired</span>`;
    const items=Array.isArray(result.items)?result.items:[];
    list.innerHTML=items.length?items.map(item=>`<div class="pantry-item"><div><strong>${esc(item.name)}</strong><small>${esc(item.quantity??'')} ${esc(item.unit||'')} · ${esc(item.location||item.category||'Pantry')}</small></div><span class="pantry-status ${esc(item.expiration_status||'unknown')}">${esc(item.expiration_status||'unknown').replace('_',' ')}</span><button class="pantry-delete" data-id="${esc(item.id)}" aria-label="Delete ${esc(item.name)}">×</button></div>`).join(''):'<div class="pantry-empty">Your pantry is empty. Add an ingredient to start pantry-aware recommendations.</div>';
    list.querySelectorAll('[data-id]').forEach(button=>button.onclick=async()=>{
      if(!confirm('Remove this pantry item?'))return;
      await api(`/api/pantry/items/${encodeURIComponent(button.dataset.id)}?profile_id=${encodeURIComponent(activeProfileId())}`,{method:'DELETE'});
      await load();
    });
  }

  function close(){document.getElementById('pantryOverlay')?.remove()}

  async function open(){
    if(!token()){window.toast?.('Sign in to manage your pantry.');return}
    ensureStyles();close();
    const overlay=document.createElement('div');
    overlay.id='pantryOverlay';overlay.className='pantry-overlay';
    overlay.innerHTML=`<section class="pantry-panel"><div class="pantry-head"><div><span class="eyebrow">AI Pantry Intelligence</span><h2>My pantry</h2></div><button class="pantry-close" aria-label="Close">×</button></div><div id="pantrySummary" class="pantry-summary"></div><form id="pantryForm" class="pantry-form"><input class="wide" name="name" placeholder="Ingredient name" required maxlength="160"><input name="quantity" type="number" min="0" step="0.01" placeholder="Qty"><input name="unit" placeholder="Unit"><select name="location"><option value="pantry">Pantry</option><option value="refrigerator">Refrigerator</option><option value="freezer">Freezer</option></select><input name="expiration_date" type="date"><button type="submit">Add item</button></form><div id="pantryItemList" class="pantry-list"></div></section>`;
    document.body.appendChild(overlay);
    overlay.querySelector('.pantry-close').onclick=close;
    overlay.addEventListener('click',event=>{if(event.target===overlay)close()});
    overlay.querySelector('#pantryForm').onsubmit=async event=>{
      event.preventDefault();
      const form=new FormData(event.currentTarget);
      const payload={name:String(form.get('name')||'').trim(),unit:String(form.get('unit')||'').trim()||null,location:String(form.get('location')||'pantry'),expiration_date:String(form.get('expiration_date')||'')||null,profile_id:activeProfileId()};
      const quantity=String(form.get('quantity')||'').trim();if(quantity)payload.quantity=Number(quantity);
      await api('/api/pantry/items',{method:'POST',body:JSON.stringify(payload)});
      event.currentTarget.reset();await load();window.toast?.('Added to pantry.');
    };
    try{await load()}catch(error){close();window.toast?.(error.message)}
  }

  function mount(){
    if(document.getElementById('pantryLauncher'))return;
    const button=document.createElement('button');button.id='pantryLauncher';button.className='pantry-launcher';button.textContent='🥕 Pantry';button.onclick=open;document.body.appendChild(button);
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
  window.GlucoPlatePantryUi={open,close,load};
})();
