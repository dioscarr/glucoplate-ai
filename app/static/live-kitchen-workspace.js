(()=>{
  if(window.GlucoPlateLiveKitchenWorkspace)return;

  let mode=new URL(location.href).searchParams.get('view')==='workspace'?'workspace':'compact';
  let activeTab='room';
  let insight=null;
  let generating=false;
  let error='';
  const selected=new Set();

  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const room=()=>window.GlucoPlateLiveCookRooms?.getRoom?.()||null;

  async function authToken(forceRefresh=false){
    const provider=window.GlucoPlateFirebaseAuth?.getIdToken;
    if(typeof provider==='function')return provider(forceRefresh);
    const cached=localStorage.getItem('glucoplate_firebase_id_token');
    if(!cached)throw new Error('Sign in to create a kitchen brief.');
    return cached;
  }

  async function api(path,options={}){
    const request=async forceRefresh=>fetch(path,{...options,headers:{'Content-Type':'application/json',Authorization:`Bearer ${await authToken(forceRefresh)}`,...(options.headers||{})}});
    let response=await request(false);
    if(response.status===401&&typeof window.GlucoPlateFirebaseAuth?.getIdToken==='function')response=await request(true);
    const body=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(body.detail||'Kitchen brief request failed.');
    return body;
  }

  function updateUrl(){
    const url=new URL(location.href);
    if(mode==='workspace')url.searchParams.set('view','workspace');
    else url.searchParams.delete('view');
    const next=url.pathname+url.search+url.hash;
    if(mode==='workspace'&&new URL(location.href).searchParams.get('view')!=='workspace')history.pushState(history.state||{},'',next);
    else history.replaceState(history.state||{},'',next);
  }

  function setMode(next,{updateHistory=true}={}){
    mode=next==='workspace'?'workspace':'compact';
    const panel=document.getElementById('liveCookRoomPanel');
    if(!panel)return;
    panel.classList.toggle('is-full-page',mode==='workspace');
    panel.dataset.viewMode=mode;
    panel.querySelector('[data-live-expand]')?.setAttribute('aria-label',mode==='workspace'?'Return to compact view':'Expand Live Kitchen');
    panel.querySelector('[data-live-expand]')?.setAttribute('title',mode==='workspace'?'Compact view':'Full-page workspace');
    panel.querySelector('[data-live-expand]')?.replaceChildren(document.createTextNode(mode==='workspace'?'↙':'↗'));
    document.documentElement.classList.toggle('live-kitchen-open',mode==='workspace');
    if(updateHistory)updateUrl();
    organize();
    if(mode==='workspace')queueMicrotask(()=>{
      const title=panel.querySelector('#liveRoomTitle');
      if(title){title.tabIndex=-1;title.focus()}
    });
  }

  function ensureExpand(){
    const panel=document.getElementById('liveCookRoomPanel');
    const header=panel?.querySelector('.live-room-header');
    if(!header||header.querySelector('[data-live-expand]'))return;
    const actions=document.createElement('div');
    actions.className='live-room-header-actions';
    actions.innerHTML='<button type="button" class="live-room-expand" data-live-expand aria-label="Expand Live Kitchen" title="Full-page workspace">↗</button>';
    const close=header.querySelector('.live-room-close');
    if(close){header.insertBefore(actions,close);actions.appendChild(close)}
    else header.appendChild(actions);
    actions.querySelector('[data-live-expand]').onclick=()=>setMode(mode==='workspace'?'compact':'workspace');
  }

  function ensureNavigation(body){
    let nav=body.querySelector('[data-live-workspace-nav]');
    if(nav)return nav;
    nav=document.createElement('nav');
    nav.className='live-workspace-nav';
    nav.dataset.liveWorkspaceNav='1';
    nav.setAttribute('aria-label','Live Kitchen workspace');
    nav.innerHTML=['cook','room','ai','list'].map(tab=>`<button type="button" data-workspace-tab="${tab}" aria-pressed="${tab===activeTab}">${tab==='ai'?'AI brief':tab==='list'?'Shopping':tab[0].toUpperCase()+tab.slice(1)}</button>`).join('');
    nav.addEventListener('click',event=>{
      const button=event.target.closest?.('[data-workspace-tab]');
      if(!button)return;
      activeTab=button.dataset.workspaceTab;
      organize();
    });
    body.prepend(nav);
    return nav;
  }

  function classify(body){
    body.querySelectorAll('[data-workspace-zone]').forEach(node=>delete node.dataset.workspaceZone);
    body.querySelector('.live-room-invite')?.setAttribute('data-workspace-zone','room');
    body.querySelector('.live-room-actions')?.setAttribute('data-workspace-zone','room');
    body.querySelector('.live-room-members')?.setAttribute('data-workspace-zone','room');
    body.querySelector('.live-room-chat')?.setAttribute('data-workspace-zone','room');
    body.querySelector('#liveRoomChatInput')?.closest('.live-room-row')?.setAttribute('data-workspace-zone','room');
    body.querySelector('.live-room-feed')?.setAttribute('data-workspace-zone','room');
    body.querySelector('[data-live-transcript]')?.setAttribute('data-workspace-zone','room');
    body.querySelectorAll('.live-room-shared-state,[data-live-media],[data-session-lifecycle],.live-session-history').forEach(node=>node.dataset.workspaceZone='cook');
    body.querySelector('[data-live-insight]')?.setAttribute('data-workspace-zone','ai');
    body.querySelector('[data-live-shopping-draft]')?.setAttribute('data-workspace-zone','list');
    body.querySelectorAll('h4').forEach(heading=>{
      const label=heading.textContent.trim().toLowerCase();
      heading.dataset.workspaceZone=label.includes('participant')||label.includes('chat')||label.includes('activity')?'room':'cook';
    });
  }

  function organize(){
    ensureExpand();
    const panel=document.getElementById('liveCookRoomPanel');
    const body=panel?.querySelector('#liveRoomBody');
    if(!panel||!body)return;
    panel.classList.toggle('is-full-page',mode==='workspace');
    const nav=ensureNavigation(body);
    nav.querySelectorAll('[data-workspace-tab]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.workspaceTab===activeTab)));
    renderInsights(body);
    classify(body);
    body.dataset.activeTab=activeTab;
  }

  function summaryList(items,empty){
    return items?.length?`<ul>${items.map(item=>`<li>${esc(item)}</li>`).join('')}</ul>`:`<p class="live-insight-muted">${esc(empty)}</p>`;
  }

  function renderInsights(body){
    let card=body.querySelector('[data-live-insight]');
    if(!card){card=document.createElement('section');card.className='live-insight-card';card.dataset.liveInsight='1';body.appendChild(card)}
    let shopping=body.querySelector('[data-live-shopping-draft]');
    if(!shopping){shopping=document.createElement('section');shopping.className='live-shopping-draft';shopping.dataset.liveShoppingDraft='1';body.appendChild(shopping)}

    if(generating){
      card.innerHTML='<div class="live-insight-heading"><div><span>AI KITCHEN BRIEF</span><h3>Reading the room…</h3></div></div><div class="live-insight-skeleton" aria-label="Generating summary"></div>';
      shopping.innerHTML='<div class="live-insight-empty">Shopping suggestions will appear after the brief is ready.</div>';
      return;
    }
    if(error){
      card.innerHTML=`<div class="live-insight-heading"><div><span>AI KITCHEN BRIEF</span><h3>Brief unavailable</h3></div><button type="button" data-generate-insight>Try again</button></div><p class="live-insight-error">${esc(error)}</p>`;
      card.querySelector('[data-generate-insight]').onclick=generate;
      shopping.innerHTML='<div class="live-insight-empty">Nothing has been added to your list.</div>';
      return;
    }
    if(!insight){
      card.innerHTML='<div class="live-insight-heading"><div><span>AI KITCHEN BRIEF</span><h3>Turn conversation into clarity</h3></div><button type="button" data-generate-insight>Generate brief</button></div><p>Summarize decisions and surface explicit shopping needs from this room. Nothing is added automatically.</p>';
      card.querySelector('[data-generate-insight]').onclick=generate;
      shopping.innerHTML='<div class="live-insight-empty"><strong>No suggestions yet</strong><span>Generate the Kitchen Brief to review items mentioned in conversation.</span></div>';
      return;
    }

    const updated=new Date(insight.generated_at).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'});
    card.innerHTML=`<div class="live-insight-heading"><div><span>AI KITCHEN BRIEF · ${esc(insight.provider)}</span><h3>${esc(insight.headline)}</h3></div><button type="button" data-generate-insight>Refresh</button></div><p>${esc(insight.overview)}</p><div class="live-insight-columns"><div><h4>Decisions</h4>${summaryList(insight.decisions,'No decisions captured yet.')}</div><div><h4>Next actions</h4>${summaryList(insight.action_items,'No actions captured yet.')}</div></div><small>Updated ${esc(updated)} · ${Number(insight.message_count||0)} messages reviewed</small>`;
    card.querySelector('[data-generate-insight]').onclick=generate;

    const items=insight.suggested_items||[];
    shopping.innerHTML=items.length?`<div class="live-insight-heading"><div><span>SUGGESTED FROM CONVERSATION</span><h3>Review before adding</h3></div><span>${items.length} found</span></div><div class="live-shopping-items">${items.map(item=>`<label class="live-shopping-item"><input type="checkbox" data-suggestion-id="${esc(item.id)}" ${selected.has(item.id)?'checked':''}><div><input class="live-shopping-name" data-name-for="${esc(item.id)}" value="${esc(item.name)}" aria-label="Shopping item name"><small>${esc(item.reason)} · ${Math.round(Number(item.confidence||0)*100)}% confidence</small></div></label>`).join('')}</div><button type="button" class="live-shopping-add" data-add-suggestions>Add selected to shopping list</button><p class="live-insight-muted">Suggestions stay private to your list and are never added without confirmation.</p>`:'<div class="live-insight-empty"><strong>No explicit shopping needs found</strong><span>Try refreshing after someone mentions something to buy or replace.</span></div>';
    shopping.querySelectorAll('[data-suggestion-id]').forEach(input=>input.onchange=()=>input.checked?selected.add(input.dataset.suggestionId):selected.delete(input.dataset.suggestionId));
    shopping.querySelector('[data-add-suggestions]')?.addEventListener('click',addSelected);
  }

  async function generate(){
    const current=room();if(!current)return;
    generating=true;error='';organize();
    try{
      const result=await api(`/api/live-cook-rooms/${encodeURIComponent(current.id)}/insights`,{method:'POST',body:JSON.stringify({provider:'auto'})});
      insight=result.insight;
      selected.clear();
      (insight.suggested_items||[]).forEach(item=>{if(Number(item.confidence||0)>=.7)selected.add(item.id)});
    }catch(exc){error=exc.message}
    finally{generating=false;organize()}
  }

  async function addSelected(){
    const current=room();
    const ids=[...selected];
    const names=ids.map(id=>document.querySelector(`[data-name-for="${CSS.escape(id)}"]`)?.value.trim()).filter(Boolean);
    if(!names.length){window.toast?.('Select at least one item to add.');return}
    const button=document.querySelector('[data-add-suggestions]');if(button)button.disabled=true;
    try{
      await window.GlucoPlateShoppingList?.addItems?.(names,current?.title||'Live Kitchen');
      selected.clear();
      window.GlucoPlateShoppingList?.open?.();
    }catch(exc){window.toast?.(exc.message)}
    finally{if(button?.isConnected)button.disabled=false}
  }

  function onKeydown(event){
    if(event.key==='Escape'&&mode==='workspace'){event.preventDefault();setMode('compact')}
  }

  function mount(){
    ensureExpand();
    setMode(mode,{updateHistory:false});
    organize();
    document.addEventListener('keydown',onKeydown);
    window.addEventListener('popstate',()=>setMode(new URL(location.href).searchParams.get('view')==='workspace'?'workspace':'compact',{updateHistory:false}));
  }

  window.addEventListener('glucoplate:live-room-updated',()=>queueMicrotask(organize));
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
  window.GlucoPlateLiveKitchenWorkspace={expand:()=>setMode('workspace'),compact:()=>setMode('compact'),generate,getMode:()=>mode};
})();