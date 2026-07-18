(()=>{
  if(window.GlucoPlateShoppingList)return;

  const profileId=()=>window.GlucoPlateUserData?.activeProfileId?.()||localStorage.getItem('glucoplate_active_profile_id')||'default';
  const token=()=>localStorage.getItem('glucoplate_firebase_id_token');
  const headers=()=>({'Content-Type':'application/json','Authorization':`Bearer ${token()}`});
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

  async function api(path,options={}){
    const response=await fetch(path,{...options,headers:{...headers(),...(options.headers||{})}});
    if(!response.ok){
      let detail='Shopping list request failed.';
      try{detail=(await response.json()).detail||detail}catch(_error){}
      throw new Error(detail);
    }
    return response.status===204?null:response.json();
  }

  function ensureStyles(){
    if(document.getElementById('shoppingListStyles'))return;
    const style=document.createElement('style');
    style.id='shoppingListStyles';
    style.textContent=`
      .shopping-launcher{position:fixed;right:18px;bottom:142px;z-index:72;border:0;border-radius:999px;padding:12px 16px;background:#a54520;color:#fff;font-weight:900;box-shadow:0 12px 30px rgba(0,0,0,.18)}
      .shopping-overlay{position:fixed;inset:0;z-index:96;background:rgba(33,31,29,.58);backdrop-filter:blur(14px);display:grid;place-items:center;padding:16px}
      .shopping-panel{width:min(720px,100%);max-height:92dvh;overflow:auto;background:var(--bg,#f7f4ef);border-radius:24px;padding:22px}.shopping-head,.shopping-actions{display:flex;align-items:center;justify-content:space-between;gap:12px}.shopping-head h2{margin:4px 0}.shopping-close{border:1px solid #ddd;background:#fff;border-radius:12px;width:40px;height:40px}
      .shopping-list{display:grid;gap:9px;margin-top:16px}.shopping-item{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:center;background:#fff;border:1px solid #e7ded4;border-radius:16px;padding:13px}.shopping-item.checked strong{text-decoration:line-through;color:#756f69}.shopping-item small{display:block;color:#756f69;margin-top:3px}.shopping-delete{border:0;background:transparent;font-size:1.1rem}.shopping-empty{text-align:center;padding:30px;color:#756f69}.shopping-clear{border:1px solid #e7ded4;background:#fff;border-radius:12px;padding:9px 12px;font-weight:800}
    `;
    document.head.appendChild(style);
  }

  async function addItems(names,sourceRecipe=null){
    const clean=[...new Set((names||[]).map(name=>String(name||'').trim()).filter(Boolean))];
    if(!clean.length)return {added_count:0,items:[]};
    if(!token()){window.toast?.('Sign in to save a shopping list.');return {added_count:0,items:[]}}
    const result=await api('/api/shopping-list/items',{method:'POST',body:JSON.stringify({profile_id:profileId(),items:clean.map(name=>({name,source_recipe:sourceRecipe}))})});
    window.toast?.(result.added_count?`Added ${result.added_count} item${result.added_count===1?'':'s'} to your shopping list.`:'Those items are already on your shopping list.');
    return result;
  }

  async function load(){
    return api(`/api/shopping-list/items?profile_id=${encodeURIComponent(profileId())}`);
  }

  function close(){document.getElementById('shoppingListOverlay')?.remove()}

  async function open(){
    if(!token()){window.toast?.('Sign in to view your shopping list.');return}
    ensureStyles();close();
    const overlay=document.createElement('div');
    overlay.id='shoppingListOverlay';overlay.className='shopping-overlay';
    overlay.innerHTML=`<section class="shopping-panel"><div class="shopping-head"><div><span class="eyebrow">Shopping gaps</span><h2>My shopping list</h2></div><button class="shopping-close" aria-label="Close">×</button></div><div class="shopping-actions"><span id="shoppingCount">Loading…</span><button id="clearCheckedBtn" class="shopping-clear">Clear checked</button></div><div id="shoppingItemList" class="shopping-list"></div></section>`;
    document.body.appendChild(overlay);
    overlay.querySelector('.shopping-close').onclick=close;
    overlay.addEventListener('click',event=>{if(event.target===overlay)close()});
    const render=async()=>{
      const result=await load();
      const items=Array.isArray(result.items)?result.items:[];
      overlay.querySelector('#shoppingCount').textContent=`${result.remaining_count||0} remaining · ${result.count||0} total`;
      const list=overlay.querySelector('#shoppingItemList');
      list.innerHTML=items.length?items.map(item=>`<div class="shopping-item ${item.checked?'checked':''}"><input type="checkbox" data-check-id="${esc(item.id)}" ${item.checked?'checked':''}><div><strong>${esc(item.name)}</strong>${item.source_recipe?`<small>From ${esc(item.source_recipe)}</small>`:''}</div><button class="shopping-delete" data-delete-id="${esc(item.id)}" aria-label="Delete ${esc(item.name)}">×</button></div>`).join(''):'<div class="shopping-empty">Your shopping list is empty.</div>';
      list.querySelectorAll('[data-check-id]').forEach(input=>input.onchange=async()=>{await api(`/api/shopping-list/items/${encodeURIComponent(input.dataset.checkId)}`,{method:'PUT',body:JSON.stringify({checked:input.checked,profile_id:profileId()})});await render()});
      list.querySelectorAll('[data-delete-id]').forEach(button=>button.onclick=async()=>{await api(`/api/shopping-list/items/${encodeURIComponent(button.dataset.deleteId)}?profile_id=${encodeURIComponent(profileId())}`,{method:'DELETE'});await render()});
    };
    overlay.querySelector('#clearCheckedBtn').onclick=async()=>{await api(`/api/shopping-list/checked?profile_id=${encodeURIComponent(profileId())}`,{method:'DELETE'});await render()};
    try{await render()}catch(error){close();window.toast?.(error.message)}
  }

  function mount(){
    if(document.getElementById('shoppingListLauncher'))return;
    const button=document.createElement('button');button.id='shoppingListLauncher';button.className='shopping-launcher';button.textContent='🛒 List';button.onclick=open;document.body.appendChild(button);
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
  window.GlucoPlateShoppingList={addItems,load,open,close};
})();
