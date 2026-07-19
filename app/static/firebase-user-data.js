(()=>{
  const nativeFetch=window.fetch.bind(window);
  const ACTIVE_PROFILE_KEY='glucoplate_active_profile_id';
  const INTERACTION_QUEUE_KEY='glucoplate_flavor_memory_queue_v1';
  const INTERACTION_QUEUE_LIMIT=100;
  const SIGNAL_DEDUPE_MS=2500;
  const recentSignals=new Map();
  let flushingSignals=false;
  const routeMap=new Map([
    ['/api/recipes/save','/api/user-data/recipes'],
    ['/api/recipes/list','/api/user-data/recipes'],
    ['/api/recipes/recents','/api/user-data/recents']
  ]);

  const activeProfileId=()=>localStorage.getItem(ACTIVE_PROFILE_KEY)||'default';
  function setActiveProfile(profile){
    const id=typeof profile==='string'?profile:profile?.id;
    if(!id)throw new Error('A profile id is required.');
    localStorage.setItem(ACTIVE_PROFILE_KEY,id);
    localStorage.setItem('glucoplate_active_profile',JSON.stringify(typeof profile==='string'?{id}:profile));
    window.dispatchEvent(new CustomEvent('glucoplate:profilechange',{detail:{profile_id:id}}));
    renderProfilePanel().catch(()=>{});
    return id;
  }

  function normalizeRequest(input,init={}){
    const rawUrl=typeof input==='string'?input:input.url;
    const url=new URL(rawUrl,window.location.origin);
    const mapped=routeMap.get(url.pathname);
    if(!mapped)return {input,init,originalPath:url.pathname};
    const headers=new Headers(init.headers||(typeof input!=='string'?input.headers:undefined));
    const token=localStorage.getItem('glucoplate_firebase_id_token');
    if(token)headers.set('Authorization',`Bearer ${token}`);
    let body=init.body;
    if(body&&['/api/recipes/save','/api/recipes/recents'].includes(url.pathname)){
      try{body=JSON.stringify({recipe:JSON.parse(body)})}catch(_error){}
      headers.set('Content-Type','application/json');
    }
    const originalPath=url.pathname;
    url.pathname=mapped;
    return {input:url.toString(),init:{...init,headers,body},originalPath};
  }

  function parseRecipeBody(body){
    if(!body||typeof body!=='string')return null;
    try{
      const parsed=JSON.parse(body);
      return parsed?.recipe||parsed;
    }catch(_error){return null}
  }

  window.fetch=async(input,init={})=>{
    const originalBody=init.body;
    const normalized=normalizeRequest(input,init);
    const response=await nativeFetch(normalized.input,normalized.init);
    if(response.ok&&normalized.originalPath==='/api/recipes/save'){
      const recipe=parseRecipeBody(originalBody);
      trackInteraction('saved',recipe,'recipe-save').catch(()=>{});
    }
    return response;
  };

  async function authToken(forceRefresh=false){
    const provider=window.GlucoPlateFirebaseAuth?.getIdToken;
    if(typeof provider==='function')return provider(Boolean(forceRefresh));
    const cached=localStorage.getItem('glucoplate_firebase_id_token');
    if(!cached)throw new Error('Sign in is required.');
    return cached;
  }

  async function authenticatedRequest(path,options={}){
    const request=async forceRefresh=>{
      const headers=new Headers(options.headers||{});
      headers.set('Authorization',`Bearer ${await authToken(forceRefresh)}`);
      if(options.body&&!headers.has('Content-Type'))headers.set('Content-Type','application/json');
      return nativeFetch(path,{...options,headers});
    };
    let response=await request(false);
    if(response.status===401&&typeof window.GlucoPlateFirebaseAuth?.getIdToken==='function')response=await request(true);
    if(!response.ok){
      let message='Request failed.';
      try{message=(await response.json()).detail||message}catch(_error){}
      const error=new Error(message);error.status=response.status;throw error;
    }
    return response.status===204?null:response.json();
  }

  const profileQuery=path=>`${path}${path.includes('?')?'&':'?'}profile_id=${encodeURIComponent(activeProfileId())}`;
  const api={
    activeProfileId,
    setActiveProfile,
    listProfiles:()=>authenticatedRequest('/api/user-data/profiles'),
    createProfile:profile=>authenticatedRequest('/api/user-data/profiles',{method:'POST',body:JSON.stringify(profile)}),
    deleteProfile:profileId=>authenticatedRequest(`/api/user-data/profiles/${encodeURIComponent(profileId)}`,{method:'DELETE'}),
    listSavedRecipes:()=>authenticatedRequest('/api/user-data/recipes'),
    deleteSavedRecipe:recipeId=>authenticatedRequest(`/api/user-data/recipes/${encodeURIComponent(recipeId)}`,{method:'DELETE'}),
    recordCooked:payload=>authenticatedRequest('/api/user-data/cooking-history',{method:'POST',body:JSON.stringify({...payload,profile_id:activeProfileId()})}),
    listCookingHistory:(limit=50)=>authenticatedRequest(profileQuery(`/api/user-data/cooking-history?limit=${limit}`)),
    recordRecipeInteraction:payload=>authenticatedRequest('/api/user-data/recipe-interactions',{method:'POST',body:JSON.stringify({...payload,profile_id:payload.profile_id||activeProfileId()})}),
    listRecipeInteractions:(limit=100)=>authenticatedRequest(profileQuery(`/api/user-data/recipe-interactions?limit=${limit}`)),
    getFlavorMemory:()=>authenticatedRequest(profileQuery('/api/user-data/flavor-memory')),
    getPreferences:()=>authenticatedRequest(profileQuery('/api/user-data/preferences')),
    savePreferences:preferences=>authenticatedRequest('/api/user-data/preferences',{method:'PUT',body:JSON.stringify({preferences,profile_id:activeProfileId()})})
  };

  function recipeFromDocument(){
    const title=document.querySelector('#result .recipe-hero h1')?.textContent?.trim();
    if(!title)return null;
    const summary=document.querySelector('#result .recipe-hero p')?.textContent?.trim()||null;
    const pills=[...document.querySelectorAll('#result .recipe-kicker .pill')].map(item=>item.textContent.trim()).filter(Boolean);
    return {title,summary,tags:pills};
  }

  function readInteractionQueue(){
    try{const value=JSON.parse(localStorage.getItem(INTERACTION_QUEUE_KEY)||'[]');return Array.isArray(value)?value.slice(-INTERACTION_QUEUE_LIMIT):[]}
    catch{return[]}
  }
  function writeInteractionQueue(items){
    const trimmed=items.slice(-INTERACTION_QUEUE_LIMIT);
    if(trimmed.length)localStorage.setItem(INTERACTION_QUEUE_KEY,JSON.stringify(trimmed));
    else localStorage.removeItem(INTERACTION_QUEUE_KEY);
  }
  function signalFingerprint(payload){
    const recipeKey=payload.recipe_id||String(payload.recipe_name||'').trim().toLowerCase();
    return [payload.profile_id,payload.interaction_type,recipeKey,payload.source].join(':');
  }
  function isDuplicateSignal(payload){
    const key=signalFingerprint(payload),now=Date.now(),previous=recentSignals.get(key)||0;
    recentSignals.set(key,now);
    for(const [fingerprint,time] of recentSignals)if(now-time>SIGNAL_DEDUPE_MS*4)recentSignals.delete(fingerprint);
    return now-previous<SIGNAL_DEDUPE_MS;
  }
  function queueInteraction(payload){
    const queued=readInteractionQueue();
    if(!queued.some(item=>signalFingerprint(item)===signalFingerprint(payload)&&item.occurred_at===payload.occurred_at)){
      queued.push(payload);writeInteractionQueue(queued);
    }
  }
  async function flushInteractionQueue(){
    if(flushingSignals||!navigator.onLine||!localStorage.getItem('glucoplate_firebase_id_token'))return;
    flushingSignals=true;
    try{
      const queued=readInteractionQueue(),remaining=[];
      for(let index=0;index<queued.length;index++){
        try{await api.recordRecipeInteraction(queued[index])}
        catch(error){remaining.push(...queued.slice(index));console.debug('Flavor Memory queue is waiting to retry.',error?.message);break}
      }
      writeInteractionQueue(remaining);
    }finally{flushingSignals=false}
  }
  async function trackInteraction(interactionType,recipe=null,source='recipe-ui'){
    if(!localStorage.getItem('glucoplate_firebase_id_token'))return null;
    const value=recipe||recipeFromDocument();
    if(!value?.title&&!value?.id&&!value?.recipe_id)return null;
    const payload={
      interaction_type:interactionType,
      recipe_id:value.id||value.recipe_id||null,
      recipe_name:value.title||value.recipe_name||null,
      cuisine:value.cuisine||value.culture||null,
      tags:Array.isArray(value.tags)?value.tags.slice(0,30):[],
      source,
      profile_id:activeProfileId(),
      occurred_at:new Date().toISOString()
    };
    if(isDuplicateSignal(payload))return null;
    try{
      const result=await api.recordRecipeInteraction(payload);
      flushInteractionQueue().catch(()=>{});
      return result;
    }catch(error){
      queueInteraction(payload);
      console.debug('Flavor Memory signal queued for retry.',{interactionType,message:error?.message});
      return null;
    }
  }

  let openedFromCookbook=false;
  document.addEventListener('click',event=>{
    const button=event.target.closest('button');
    if(!button)return;
    if(button.classList.contains('saved-item')){
      openedFromCookbook=true;
      return;
    }
    if(button.id==='generateBtn'||button.id==='ingredientGenerateBtn'||button.id==='newBtn'||button.classList.contains('dish-card')){
      openedFromCookbook=false;
    }
    if(button.id==='cookBtn'&&openedFromCookbook){
      openedFromCookbook=false;
      trackInteraction('repeated',null,'saved-recipe-cook').catch(()=>{});
      return;
    }
    if(button.id==='newBtn'){
      trackInteraction('dismissed',null,'new-recipe-action').catch(()=>{});
      return;
    }
    if(button.closest('#cookMode')&&button.textContent.trim()==='Finish'){
      const recipe=recipeFromDocument();
      trackInteraction('cooked',recipe,'cook-mode-completed').catch(()=>{});
      api.recordCooked({recipe_name:recipe?.title||null,recipe:recipe||undefined,cooked_at:new Date().toISOString()}).catch(()=>{});
    }
  },true);

  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  function ensureStyles(){
    if(document.getElementById('premiumProfileStyles'))return;
    const style=document.createElement('style');
    style.id='premiumProfileStyles';
    style.textContent=`
      #profileView{padding-bottom:8px}.profile-shell{display:grid;gap:14px}.profile-hero{position:relative;overflow:hidden;padding:24px;background:linear-gradient(145deg,var(--dark),#3a271c);color:#fff}.profile-hero:after{content:"";position:absolute;width:220px;height:220px;border-radius:50%;right:-90px;top:-110px;background:linear-gradient(135deg,var(--brand),var(--brand2));opacity:.35}.profile-identity{position:relative;z-index:1;display:grid;grid-template-columns:64px 1fr;gap:14px;align-items:center}.profile-avatar-xl{width:64px;height:64px;border-radius:22px;display:grid;place-items:center;font-size:2rem;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.18);box-shadow:0 14px 32px rgba(0,0,0,.18)}.profile-hero h1{margin:0;font-size:1.65rem;letter-spacing:-.04em}.profile-hero p{margin:5px 0 0;color:#ead8cc;font-size:.85rem}.profile-badge{display:inline-flex;margin-top:10px;padding:6px 9px;border-radius:999px;background:rgba(255,255,255,.12);font-size:.7rem;font-weight:850}.profile-account-return{position:relative;z-index:2;display:inline-flex;align-items:center;gap:7px;margin-top:12px;min-height:44px;padding:9px 12px;border:1px solid rgba(255,255,255,.24);border-radius:14px;background:rgba(255,255,255,.12);color:#fff;font-weight:850;touch-action:manipulation}.profile-account-return:focus-visible{outline:3px solid #ffc49f;outline-offset:3px}.profile-stats{position:relative;z-index:1;display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:20px}.profile-stat{padding:12px;border-radius:16px;background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.1)}.profile-stat strong,.profile-stat span{display:block}.profile-stat strong{font-size:1.2rem}.profile-stat span{color:#dbc8bc;font-size:.68rem;margin-top:3px}.profile-section{padding:19px}.profile-section-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:14px}.profile-section h2{margin:0;font-size:1.2rem}.profile-section p{margin:4px 0 0;color:var(--muted);font-size:.8rem;line-height:1.45}.profile-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.profile-person{position:relative;text-align:left;border:1px solid var(--line);border-radius:20px;padding:15px;background:#fff;color:var(--text);min-height:112px;transition:.18s}.profile-person:hover{transform:translateY(-1px);box-shadow:var(--soft)}.profile-person.active{border-color:var(--brand);background:linear-gradient(145deg,#fff,#fff4ea);box-shadow:0 0 0 3px rgba(242,106,46,.09)}.profile-person .avatar{font-size:1.75rem}.profile-person strong,.profile-person small{display:block}.profile-person strong{margin-top:8px}.profile-person small{color:var(--muted);margin-top:3px}.active-check{position:absolute;right:11px;top:11px;width:23px;height:23px;border-radius:50%;display:grid;place-items:center;background:var(--brand);color:#fff;font-size:.72rem}.profile-create{display:grid;grid-template-columns:58px 1fr auto;gap:9px;margin-top:13px;padding:12px;border:1px dashed var(--line);border-radius:18px;background:var(--surface2)}.profile-create input{min-width:0;border:1px solid var(--line);border-radius:13px;padding:11px;background:#fff}.profile-create .emoji-input{text-align:center;font-size:1.25rem}.memory-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.memory-card{padding:15px;border:1px solid var(--line);border-radius:18px;background:#fff}.memory-card span{font-size:1.3rem}.memory-card strong,.memory-card small{display:block}.memory-card strong{margin-top:9px}.memory-card small{margin-top:4px;color:var(--muted);line-height:1.4}.profile-safety{padding:14px;border-radius:17px;background:#eef7f2;color:#245d46;font-size:.8rem;line-height:1.5}.profile-loading{padding:34px;text-align:center;color:var(--muted)}@media(min-width:760px){.profile-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.memory-grid{grid-template-columns:repeat(4,1fr)}}@media(max-width:520px){.profile-hero{padding:20px}.profile-stats{grid-template-columns:1fr 1fr}.profile-stat:last-child{grid-column:1/-1}.profile-grid,.memory-grid{grid-template-columns:1fr 1fr}.profile-create{grid-template-columns:52px 1fr}.profile-create button{grid-column:1/-1}.profile-identity{grid-template-columns:56px 1fr}.profile-avatar-xl{width:56px;height:56px;border-radius:19px}}
    `;
    document.head.appendChild(style);
  }

  function session(){try{return JSON.parse(localStorage.getItem('glucoplate_firebase_session')||'null')||{}}catch{return{}}}
  function listFrom(result,key){if(Array.isArray(result))return result;if(Array.isArray(result?.[key]))return result[key];return[]}
  function countPrefs(value){const prefs=value?.preferences||value||{};return Object.values(prefs).reduce((total,item)=>total+(Array.isArray(item)?item.length:item?1:0),0)}

  async function renderProfilePanel(){
    const host=document.getElementById('profileView');
    if(!host)return;
    ensureStyles();
    if(!localStorage.getItem('glucoplate_firebase_id_token'))return;
    host.innerHTML='<div class="card profile-loading">Loading your personalized kitchen…</div>';
    try{
      const [profilesResult,prefsResult,historyResult,savedResult]=await Promise.allSettled([api.listProfiles(),api.getPreferences(),api.listCookingHistory(100),api.listSavedRecipes()]);
      const profiles=profilesResult.status==='fulfilled'?listFrom(profilesResult.value,'profiles'):[];
      const history=historyResult.status==='fulfilled'?listFrom(historyResult.value,'history'):[];
      const saved=savedResult.status==='fulfilled'?listFrom(savedResult.value,'recipes'):[];
      const preferenceCount=prefsResult.status==='fulfilled'?countPrefs(prefsResult.value):0;
      const active=activeProfileId();
      const options=[{id:'default',name:'My profile',avatar:'👤'},...profiles.filter(profile=>profile.id!=='default')];
      const current=options.find(profile=>profile.id===active)||options[0];
      const auth=session();
      const userName=auth.name||auth.display_name||auth.email||current.name;
      const company=auth.enterprise?.company_name||auth.enterprise?.name||'GlucoPlate';
      host.innerHTML=`<div class="profile-shell">
        <section class="card profile-hero"><div class="profile-identity"><div class="profile-avatar-xl">${esc(current.avatar||'👤')}</div><div><span class="eyebrow" style="color:#ffc49f">Personal kitchen</span><h1>${esc(current.name||userName)}</h1><p>${esc(userName)} · ${esc(company)}</p><span class="profile-badge">AI memory active for this profile</span>${active!=='default'?'<button type="button" class="profile-account-return" data-return-account>← Back to my account</button>':''}</div></div><div class="profile-stats"><div class="profile-stat"><strong>${saved.length}</strong><span>Saved recipes</span></div><div class="profile-stat"><strong>${history.length}</strong><span>Meals cooked</span></div><div class="profile-stat"><strong>${preferenceCount}</strong><span>Preferences remembered</span></div></div></section>
        <section class="card profile-section"><div class="profile-section-head"><div><h2>Who are we cooking for?</h2><p>Each person keeps separate allergies, preferences, serving defaults, and cooking history.</p></div></div><div class="profile-grid">${options.map(profile=>`<button type="button" class="profile-person ${profile.id===active?'active':''}" data-profile-id="${esc(profile.id)}"><span class="avatar">${esc(profile.avatar||'👤')}</span><strong>${esc(profile.name||'Profile')}</strong><small>${profile.id===active?'Currently selected':'Tap to switch'}</small>${profile.id===active?'<span class="active-check">✓</span>':''}</button>`).join('')}</div><form id="householdProfileForm" class="profile-create"><input id="profileAvatar" class="emoji-input" aria-label="Profile emoji" value="👤" maxlength="4"><input id="profileName" aria-label="Profile name" placeholder="Add another household member" maxlength="80" required><button class="btn secondary" type="submit">Create profile</button></form></section>
        <section class="card profile-section"><div class="profile-section-head"><div><h2>Personalization memory</h2><p>GlucoPlate uses the selected profile when generating recipes.</p></div></div><div class="memory-grid"><div class="memory-card"><span>⚠️</span><strong>Allergies</strong><small>Ingredients that must always be excluded.</small></div><div class="memory-card"><span>🥗</span><strong>Food preferences</strong><small>Cuisines, diets, likes, and dislikes.</small></div><div class="memory-card"><span>🍽️</span><strong>Serving defaults</strong><small>Generate the right amount for each person.</small></div><div class="memory-card"><span>🕘</span><strong>Cooking history</strong><small>Keep each person’s meals and progress separate.</small></div></div></section>
        <div class="profile-safety">Nutrition values are estimates and are not medical advice. Always verify ingredients for allergies and dietary requirements.</div>
      </div>`;
      host.querySelectorAll('[data-profile-id]').forEach(button=>button.onclick=()=>setActiveProfile(options.find(profile=>profile.id===button.dataset.profileId)||button.dataset.profileId));
      host.querySelector('[data-return-account]')?.addEventListener('click',()=>setActiveProfile('default'));
      host.querySelector('#householdProfileForm').onsubmit=async event=>{
        event.preventDefault();
        const form=event.currentTarget;
        const name=form.querySelector('#profileName').value.trim();
        if(!name)return;
        const button=form.querySelector('button');button.disabled=true;button.textContent='Creating…';
        try{const result=await api.createProfile({name,avatar:form.querySelector('#profileAvatar').value.trim()||'👤'});setActiveProfile(result.profile)}
        catch(error){button.disabled=false;button.textContent='Create profile';window.toast?.(error.message)}
      };
    }catch(error){host.innerHTML=`<div class="card profile-loading">${esc(error.message)}</div>`}
    finally{queueMicrotask(()=>window.GlucoPlateFirebaseAuth?.renderPanel?.())}
  }

  window.GlucoPlateUserData=api;
  window.GlucoPlateFlavorMemory={trackInteraction,recipeFromDocument,flushInteractionQueue,pendingInteractions:readInteractionQueue};
  window.addEventListener('DOMContentLoaded',()=>{renderProfilePanel().catch(()=>{});flushInteractionQueue().catch(()=>{})});
  window.addEventListener('online',()=>flushInteractionQueue().catch(()=>{}));
  window.addEventListener('glucoplate:auth-session-changed',()=>flushInteractionQueue().catch(()=>{}));
  window.addEventListener('glucoplate:profilechange',()=>{renderProfilePanel().catch(()=>{});flushInteractionQueue().catch(()=>{})});
})();