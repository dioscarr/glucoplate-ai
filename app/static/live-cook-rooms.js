(()=>{
  const token=()=>localStorage.getItem('glucoplate_firebase_id_token')||'';
  const notify=message=>typeof window.toast==='function'?window.toast(message):console.info(message);
  const escapeHtml=value=>String(value??'').replace(/[&<>'\"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','\"':'&quot;'}[ch]));
  let room=null,pollTimer=null,applyingRemote=false,lastRevision=0,dismissed=false;

  function errorMessage(body,status){
    const detail=body?.detail;
    if(Array.isArray(detail)){
      const fields=detail.map(item=>Array.isArray(item?.loc)?item.loc.at(-1):null).filter(Boolean).join(', ');
      const messages=detail.map(item=>item?.msg).filter(Boolean).join('; ');
      return `${fields?fields+': ':''}${messages||'The request was rejected.'}`;
    }
    return typeof detail==='string'&&detail.trim()?detail:`Request failed (${status})`;
  }

  async function authToken(forceRefresh=false){
    const provider=window.GlucoPlateFirebaseAuth?.getIdToken;
    if(typeof provider==='function')return provider(forceRefresh);
    const cached=token();
    if(!cached)throw new Error('Sign in before using a live cook room.');
    return cached;
  }

  async function api(path,options={}){
    const request=async forceRefresh=>{
      const currentToken=await authToken(forceRefresh);
      return fetch(path,{...options,headers:{'Content-Type':'application/json',Authorization:`Bearer ${currentToken}`,...(options.headers||{})}});
    };
    let response=await request(false);
    if(response.status===401&&typeof window.GlucoPlateFirebaseAuth?.getIdToken==='function'){
      response=await request(true);
    }
    const body=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(errorMessage(body,response.status));
    return body;
  }

  function currentRecipe(){return window.currentRecipe||null}
  function displayName(){
    const value=localStorage.getItem('glucoplate_display_name')||localStorage.getItem('glucoplate_user_name')||'Cook';
    return String(value).trim().slice(0,80)||'Cook';
  }
  function normalizeInviteCode(value){return String(value||'').toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,12)}

  function ensureStyles(){
    if(document.getElementById('liveCookRoomStyles'))return;
    const style=document.createElement('style');style.id='liveCookRoomStyles';style.textContent=`
      .live-room-launch{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.75rem}.live-room-panel{position:fixed;right:1rem;bottom:1rem;width:min(390px,calc(100vw - 2rem));max-height:78vh;overflow:auto;background:var(--surface,#fff);color:var(--text,#201a17);border:1px solid var(--border,#ddd);border-radius:18px;box-shadow:0 18px 50px rgba(0,0,0,.22);z-index:10000;padding:1rem}.live-room-panel[hidden]{display:none}.live-room-panel header{display:flex;justify-content:space-between;gap:.5rem;align-items:start}.live-room-code{font-weight:800;letter-spacing:.14em}.live-room-row{display:flex;gap:.5rem;align-items:center;margin:.65rem 0}.live-room-row input{flex:1}.live-room-members,.live-room-feed,.live-room-chat{display:grid;gap:.4rem;margin:.5rem 0}.live-room-member,.live-room-event,.live-room-message{padding:.5rem .65rem;border-radius:12px;background:var(--surfaceAlt,#f6f1ed);font-size:.9rem}.live-room-message strong{display:block}.live-room-panel h4{margin:.85rem 0 .35rem}.live-room-actions{display:flex;gap:.4rem;flex-wrap:wrap}.live-room-close{border:0;background:transparent;font-size:1.25rem}.live-room-empty{opacity:.7;font-size:.9rem}`;document.head.appendChild(style);
    const link=document.createElement('link');link.rel='stylesheet';link.href='/static/live-cook-room-premium.css';link.dataset.liveRoomPremium='1';document.head.appendChild(link);
  }

  function ensurePanel(){
    ensureStyles();
    let panel=document.getElementById('liveCookRoomPanel');
    if(panel)return panel;
    panel=document.createElement('aside');panel.id='liveCookRoomPanel';panel.className='live-room-panel';panel.hidden=true;
    panel.innerHTML=`<header><div><strong>Live Cook Room</strong><div id="liveRoomTitle"></div></div><button class="live-room-close" type="button" aria-label="Close">×</button></header><div id="liveRoomBody"></div>`;
    panel.querySelector('.live-room-close').onclick=()=>setDismissed(true);
    document.body.appendChild(panel);ensureReopenButton();return panel;
  }

  function ensureReopenButton(){
    let button=document.getElementById('liveRoomReopen');
    if(button)return button;
    button=document.createElement('button');
    button.id='liveRoomReopen';
    button.className='live-room-reopen';
    button.type='button';
    button.textContent='Open live room';
    button.hidden=true;
    button.onclick=()=>setDismissed(false);
    document.body.appendChild(button);
    return button;
  }

  function setDismissed(value){
    dismissed=Boolean(value);
    const panel=ensurePanel(),reopen=ensureReopenButton();
    panel.hidden=dismissed||!room;
    reopen.hidden=!dismissed||!room;
  }

  function launchControls(){
    const cook=document.getElementById('cookMode');if(!cook)return;
    const hasRecipe=Boolean(currentRecipe()),existing=cook.querySelector('.live-room-launch');
    if(existing?.dataset.hasRecipe===String(hasRecipe))return;
    existing?.remove();
    const wrap=document.createElement('div');wrap.className='live-room-launch';wrap.dataset.hasRecipe=String(hasRecipe);
    wrap.innerHTML=hasRecipe
      ?'<button type="button" class="btn" data-live-create>Start live room</button><button type="button" class="btn ghost" data-live-browse>Live now</button><button type="button" class="live-room-code-link" data-live-join>Have an invite code?</button>'
      :'<button type="button" class="btn" data-live-browse>Browse live rooms</button><button type="button" class="live-room-code-link" data-live-join>Have an invite code?</button>';
    wrap.querySelector('[data-live-create]')?.addEventListener('click',createRoom);
    wrap.querySelector('[data-live-browse]').onclick=browseLiveRooms;
    wrap.querySelector('[data-live-join]').onclick=promptJoin;
    const target=cook.querySelector('[data-cook-live-slot]');
    target?target.appendChild(wrap):(cook.querySelector('.cook-controls')||cook).insertAdjacentElement('afterend',wrap);
  }

  function ensureDirectory(){
    let directory=document.getElementById('liveRoomDirectory');
    if(directory)return directory;
    directory=document.createElement('section');
    directory.id='liveRoomDirectory';
    directory.className='live-room-directory';
    directory.hidden=true;
    directory.innerHTML='<header><div><strong>Live now</strong><span>Cooking across your organization</span></div><button type="button" aria-label="Close live rooms" data-close-directory>×</button></header><div data-live-directory-body></div>';
    directory.querySelector('[data-close-directory]').onclick=()=>directory.hidden=true;
    directory.addEventListener('click',event=>{
      const button=event.target.closest?.('[data-join-room-id]');
      if(button)joinRoomById(button.dataset.joinRoomId,button);
    });
    document.body.appendChild(directory);
    return directory;
  }

  async function joinRoomById(roomId,button=null){
    if(!roomId)return;
    if(button)button.disabled=true;
    try{
      const result=await api(`/api/live-cook-rooms/join/${encodeURIComponent(roomId)}`,{method:'POST',body:JSON.stringify({display_name:displayName()})});
      ensureDirectory().hidden=true;
      activate(result.room);
      notify(`Joined ${result.room.title||'live cooking room'}.`);
      return result.room;
    }catch(error){notify(error.message);throw error}
    finally{if(button?.isConnected)button.disabled=false}
  }

  async function browseLiveRooms(){
    const directory=ensureDirectory(),body=directory.querySelector('[data-live-directory-body]');
    directory.hidden=false;
    body.innerHTML='<div class="live-room-directory-empty">Loading live rooms…</div>';
    try{
      const result=await api('/api/live-cook-rooms/active');
      const rooms=result.rooms||[];
      body.innerHTML=rooms.length?rooms.map(item=>`
        <article class="live-room-directory-card">
          <div><strong>${escapeHtml(item.title||'Live Cook Room')}</strong><span>${escapeHtml(item.host_name||'Host')} · ${Number(item.participant_count||0)} cooking · ${escapeHtml(item.session_status||'waiting')}</span></div>
          <button type="button" data-join-room-id="${escapeHtml(item.id)}">Join</button>
        </article>`).join(''):'<div class="live-room-directory-empty">No live cooking rooms right now.</div>';
    }catch(error){body.innerHTML=`<div class="live-room-directory-empty">${escapeHtml(error.message)}</div>`}
  }

  function consumeLiveRoomDeepLink(attempt=0){
    const url=new URL(location.href),roomId=url.searchParams.get('live_room');
    if(!roomId)return;
    const hasAuth=Boolean(localStorage.getItem('glucoplate_firebase_id_token')||window.GlucoPlateFirebaseAuth?.getIdToken);
    if(!hasAuth&&attempt<20){setTimeout(()=>consumeLiveRoomDeepLink(attempt+1),500);return}
    joinRoomById(roomId).then(()=>{
      url.searchParams.delete('live_room');
      history.replaceState({},'',url.pathname+url.search+url.hash);
    }).catch(()=>{});
  }

  async function createRoom(){
    const recipe=currentRecipe();if(!recipe){notify('Open a recipe before starting a room.');return}
    try{
      const result=await api('/api/live-cook-rooms',{method:'POST',body:JSON.stringify({recipe,title:recipe.title,display_name:displayName(),visibility:'private'})});
      activate(result.room);notify(`Room ${result.room.invite_code} created.`);
    }catch(error){notify(error.message)}
  }

  async function promptJoin(){
    const entered=prompt('Enter the 6-character cook room code');if(entered===null)return;
    const code=normalizeInviteCode(entered);
    if(code.length<4){notify('Enter a valid cook room code.');return}
    try{const result=await api('/api/live-cook-rooms/join',{method:'POST',body:JSON.stringify({invite_code:code,display_name:displayName()})});activate(result.room)}catch(error){notify(error.message)}
  }

  function activate(next){room=next;dismissed=false;lastRevision=Number(room.state?.revision||0);render();startPolling();syncRemoteState(room)}

  function startPolling(){clearInterval(pollTimer);pollTimer=setInterval(refresh,1800)}
  async function refresh(){if(!room)return;try{const result=await api(`/api/live-cook-rooms/${room.id}`);room=result.room;render();syncRemoteState(room)}catch(error){clearInterval(pollTimer);notify(error.message)}}

  function syncRemoteState(next){
    const revision=Number(next.state?.revision||0);if(revision<=lastRevision)return;lastRevision=revision;
    const remoteStep=Number(next.state?.current_step||0);
    if(typeof window.cookIndex==='number'&&window.cookIndex!==remoteStep){
      applyingRemote=true;window.cookIndex=remoteStep;if(typeof window.renderCookStep==='function')window.renderCookStep();applyingRemote=false;
    }
  }

  async function sendState(updates){if(!room||applyingRemote)return;try{const result=await api(`/api/live-cook-rooms/${room.id}/state`,{method:'PATCH',body:JSON.stringify(updates)});room=result.room;lastRevision=Number(room.state?.revision||lastRevision);render()}catch(error){notify(error.message)}}
  async function setReady(ready){try{room=(await api(`/api/live-cook-rooms/${room.id}/ready`,{method:'PUT',body:JSON.stringify({ready})})).room;render()}catch(error){notify(error.message)}}
  async function chat(kind='message'){
    const input=document.getElementById('liveRoomChatInput');const message=kind==='help'?'I need help with this step.':input?.value.trim();if(!message)return;
    try{await api(`/api/live-cook-rooms/${room.id}/chat`,{method:'POST',body:JSON.stringify({message,kind})});if(input)input.value='';refresh()}catch(error){notify(error.message)}
  }
  async function leave(){if(!room)return;try{await api(`/api/live-cook-rooms/${room.id}/participants/me`,{method:'DELETE'});clearInterval(pollTimer);room=null;dismissed=false;ensurePanel().hidden=true;ensureReopenButton().hidden=true;notify('You left the cook room.')}catch(error){notify(error.message)}}

  function render(){
    const panel=ensurePanel();panel.hidden=dismissed;ensureReopenButton().hidden=!dismissed;
    panel.querySelector('#liveRoomTitle').textContent=room.title||'Live Cook Room';
    const participants=room.participants||[],activity=room.activity||[],messages=room.chat||[];
    panel.querySelector('#liveRoomBody').innerHTML=`
      <div class="live-room-row"><span>Invite:</span><span class="live-room-code">${escapeHtml(room.invite_code)}</span><button type="button" data-copy-code>Copy</button></div>
      <div class="live-room-actions"><button type="button" data-ready>Ready</button><button type="button" data-not-ready>Not ready</button><button type="button" data-help>Need help</button><button type="button" data-leave>Leave</button></div>
      <h4>Participants</h4><div class="live-room-members">${participants.length?participants.map(p=>`<div class="live-room-member">${escapeHtml(p.display_name||'Cook')} · ${p.ready?'ready':'not ready'}${p.online===false?' · away':''}</div>`).join(''):'<div class="live-room-empty">No participants yet.</div>'}</div>
      <h4>Chat</h4><div class="live-room-chat">${messages.length?messages.slice(-8).map(m=>`<div class="live-room-message"><strong>${escapeHtml(m.display_name||'Cook')}</strong>${escapeHtml(m.message||'')}</div>`).join(''):'<div class="live-room-empty">No messages yet.</div>'}</div>
      <div class="live-room-row"><input id="liveRoomChatInput" maxlength="1000" placeholder="Message the room"><button type="button" data-send>Send</button></div>
      <h4>Activity</h4><div class="live-room-feed">${activity.length?activity.slice(0,10).map(a=>`<div class="live-room-event">${escapeHtml(a.message||a.type)}</div>`).join(''):'<div class="live-room-empty">Room activity will appear here.</div>'}</div>`;
    panel.querySelector('[data-copy-code]').onclick=async()=>{await navigator.clipboard?.writeText(room.invite_code);notify('Invite code copied.')};
    panel.querySelector('[data-ready]').onclick=()=>setReady(true);panel.querySelector('[data-not-ready]').onclick=()=>setReady(false);panel.querySelector('[data-help]').onclick=()=>chat('help');panel.querySelector('[data-leave]').onclick=leave;panel.querySelector('[data-send]').onclick=()=>chat('message');panel.querySelector('#liveRoomChatInput').onkeydown=e=>{if(e.key==='Enter')chat('message')};
    window.dispatchEvent(new CustomEvent('glucoplate:live-room-updated',{detail:{roomId:room.id,revision:Number(room.state?.revision||0)}}));
  }

  function wrapCookNavigation(){
    for(const [name,delta] of [['nextStep',1],['prevStep',-1]]){
      const original=window[name];if(typeof original!=='function'||original.__liveRoomWrapped)continue;
      const wrapped=function(...args){const result=original.apply(this,args);queueMicrotask(()=>{if(room)sendState({current_step:Number(window.cookIndex||0)})});return result};wrapped.__liveRoomWrapped=true;window[name]=wrapped;
    }
  }

  const observer=new MutationObserver(()=>{launchControls();wrapCookNavigation()});
  window.addEventListener('DOMContentLoaded',()=>{ensurePanel();ensureDirectory();launchControls();wrapCookNavigation();observer.observe(document.body,{childList:true,subtree:true});consumeLiveRoomDeepLink()});
  window.addEventListener('pagehide',()=>clearInterval(pollTimer));
  window.GlucoPlateLiveCookRooms={createRoom,promptJoin,browseLiveRooms,joinRoomById,refresh,getRoom:()=>room};
})();
