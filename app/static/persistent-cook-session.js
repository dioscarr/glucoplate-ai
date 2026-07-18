(()=>{
  if(window.GlucoPlateCookingSession)return;
  const CACHE_PREFIX='glucoplate_private_cooking_session_v1';
  let session=null,restoring=false,syncing=false,lastRestoredId=null;
  const notify=message=>typeof window.toast==='function'?window.toast(message):console.info(message);
  const activeProfileId=()=>window.GlucoPlateUserData?.activeProfileId?.()||localStorage.getItem('glucoplate_active_profile_id')||'default';
  function userId(){try{return JSON.parse(localStorage.getItem('glucoplate_firebase_session')||'null')?.user?.uid||'signed-out'}catch{return'signed-out'}}
  const cacheKey=()=>`${CACHE_PREFIX}:${userId()}:${activeProfileId()}`;
  function readCache(){try{return JSON.parse(localStorage.getItem(cacheKey())||'null')}catch{return null}}
  function writeCache(value){if(value)localStorage.setItem(cacheKey(),JSON.stringify(value));else localStorage.removeItem(cacheKey())}
  function recipeKey(recipe){return String(recipe?.id||recipe?.recipe_id||recipe?.title||'').trim().toLowerCase()}

  async function authToken(forceRefresh=false){
    const provider=window.GlucoPlateFirebaseAuth?.getIdToken;
    if(typeof provider==='function')return provider(Boolean(forceRefresh));
    const token=localStorage.getItem('glucoplate_firebase_id_token');
    if(!token)throw new Error('Sign in is required to sync cooking progress.');
    return token;
  }
  async function request(path,options={}){
    const send=async forceRefresh=>fetch(path,{...options,headers:{'Content-Type':'application/json',...(options.headers||{}),Authorization:`Bearer ${await authToken(forceRefresh)}`}});
    let response=await send(false);
    if(response.status===401&&typeof window.GlucoPlateFirebaseAuth?.getIdToken==='function')response=await send(true);
    const body=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(body.detail||'Cooking progress could not be synchronized.');
    return body;
  }
  function snapshot(recipe,status='active'){
    return {
      id:`local-${Date.now()}`,
      profile_id:activeProfileId(),
      recipe_id:recipe?.id||recipe?.recipe_id||null,
      recipe_name:recipe?.title||'Untitled recipe',
      recipe,
      status,
      current_step:Math.max(0,Number(window.cookIndex||0)),
      completed_steps:[],
      started_at:new Date().toISOString(),
      updated_at:new Date().toISOString()
    };
  }
  async function createRemote(local){
    const result=await request('/api/user-data/cooking-sessions',{method:'POST',body:JSON.stringify({
      recipe_id:local.recipe_id,recipe_name:local.recipe_name,recipe:local.recipe,
      current_step:local.current_step,completed_steps:local.completed_steps||[],
      started_at:local.started_at,profile_id:local.profile_id
    })});
    let remote=result.session;
    if(local.status&&local.status!=='active'){
      remote=(await request(`/api/user-data/cooking-sessions/${encodeURIComponent(remote.id)}`,{method:'PATCH',body:JSON.stringify({status:local.status,current_step:local.current_step,completed_steps:local.completed_steps||[],profile_id:local.profile_id})})).session;
    }
    return remote;
  }
  async function ensureSession(recipe){
    if(!recipe||restoring)return session;
    if(session?.status==='active'&&recipeKey(session.recipe)===recipeKey(recipe))return session;
    const local=snapshot(recipe);session=local;writeCache(local);
    if(!navigator.onLine||!localStorage.getItem('glucoplate_firebase_id_token'))return local;
    try{session=await createRemote(local);writeCache(session)}
    catch(error){console.debug('Cooking session will sync later.',error?.message)}
    return session;
  }
  async function persist(updates){
    if(!session)return;
    session={...session,...updates,_pending_sync:true,updated_at:new Date().toISOString()};writeCache(session);
    if(!navigator.onLine||String(session.id).startsWith('local-'))return;
    try{
      const result=await request(`/api/user-data/cooking-sessions/${encodeURIComponent(session.id)}`,{method:'PATCH',body:JSON.stringify({...updates,profile_id:session.profile_id})});
      session=result.session;writeCache(session);
    }catch(error){console.debug('Cooking progress saved locally for retry.',error?.message)}
  }
  function completedSteps(index){return Array.from({length:Math.max(0,index)},(_,step)=>step)}
  async function syncLocalSession(){
    if(syncing||!navigator.onLine||!localStorage.getItem('glucoplate_firebase_id_token'))return;
    const local=session||readCache();
    if(!local||(!String(local.id||'').startsWith('local-')&&!local._pending_sync))return;
    syncing=true;
    try{
      if(String(local.id||'').startsWith('local-'))session=await createRemote(local);
      else{
        const updates={current_step:local.current_step,completed_steps:local.completed_steps||[],status:local.status||'active',timer:local.timer,profile_id:local.profile_id};
        session=(await request(`/api/user-data/cooking-sessions/${encodeURIComponent(local.id)}`,{method:'PATCH',body:JSON.stringify(updates)})).session;
      }
      writeCache(session);
    }catch(error){console.debug('Local cooking session is waiting to sync.',error?.message)}
    finally{syncing=false}
  }
  async function restoreSession(){
    if(restoring)return null;
    await syncLocalSession();
    let active=null;
    if(navigator.onLine&&localStorage.getItem('glucoplate_firebase_id_token')){
      try{active=(await request(`/api/user-data/cooking-sessions/active?profile_id=${encodeURIComponent(activeProfileId())}`)).session}
      catch(error){console.debug('Using locally cached cooking progress.',error?.message)}
    }
    active=active||readCache();
    if(!active||active.status!=='active'||!active.recipe)return null;
    if(lastRestoredId===active.id)return active;
    session=active;writeCache(active);lastRestoredId=active.id;restoring=true;
    try{
      window.currentRecipe=active.recipe;window.cookIndex=Math.max(0,Number(active.current_step||0));
      window.showView?.('cookView');window.startCookMode?.();
      notify(`Resumed ${active.recipe_name||'your cooking session'} at step ${window.cookIndex+1}.`);
    }finally{restoring=false}
    return active;
  }
  function wrapCookMode(){
    const originalStart=window.startCookMode;
    if(typeof originalStart==='function'&&!originalStart.__sessionWrapped){
      const wrapped=function(...args){const result=originalStart.apply(this,args);if(!restoring&&window.currentRecipe)queueMicrotask(()=>ensureSession(window.currentRecipe));return result};
      wrapped.__sessionWrapped=true;window.startCookMode=wrapped;
    }
    const originalNext=window.nextStep;
    if(typeof originalNext==='function'&&!originalNext.__sessionWrapped){
      const wrapped=function(...args){
        const before=Math.max(0,Number(window.cookIndex||0)),total=(window.currentRecipe?.steps||[]).length;
        const result=originalNext.apply(this,args);
        if(total&&before>=total-1)queueMicrotask(()=>persist({status:'completed',current_step:before,completed_steps:completedSteps(total)}));
        else queueMicrotask(()=>persist({status:'active',current_step:Math.max(0,Number(window.cookIndex||0)),completed_steps:completedSteps(window.cookIndex)}));
        return result;
      };
      wrapped.__sessionWrapped=true;window.nextStep=wrapped;
    }
    const originalPrev=window.prevStep;
    if(typeof originalPrev==='function'&&!originalPrev.__sessionWrapped){
      const wrapped=function(...args){const result=originalPrev.apply(this,args);queueMicrotask(()=>persist({status:'active',current_step:Math.max(0,Number(window.cookIndex||0)),completed_steps:completedSteps(window.cookIndex)}));return result};
      wrapped.__sessionWrapped=true;window.prevStep=wrapped;
    }
  }

  window.addEventListener('DOMContentLoaded',()=>{wrapCookMode();setTimeout(restoreSession,0)});
  window.addEventListener('online',()=>syncLocalSession());
  window.addEventListener('glucoplate:auth-session-changed',()=>{syncLocalSession().then(restoreSession)});
  window.addEventListener('glucoplate:profilechange',()=>{session=null;lastRestoredId=null;restoreSession()});
  window.GlucoPlateCookingSession={ensureSession,persist,restoreSession,syncLocalSession,getSession:()=>session};
})();