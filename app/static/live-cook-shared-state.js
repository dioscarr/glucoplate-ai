(()=>{
  const notify=message=>typeof window.toast==='function'?window.toast(message):console.info(message);
  const escapeHtml=value=>String(value??'').replace(/[&<>'"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
  let clock=null;
  async function authToken(){
    const provider=window.GlucoPlateFirebaseAuth?.getIdToken;
    if(typeof provider==='function')return provider(false);
    const cached=localStorage.getItem('glucoplate_firebase_id_token')||'';
    if(!cached)throw new Error('Sign in before using shared cooking controls.');
    return cached;
  }

  async function api(path,options={}){
    const response=await fetch(path,{...options,headers:{'Content-Type':'application/json',Authorization:`Bearer ${await authToken()}`,...(options.headers||{})}});
    const body=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(typeof body.detail==='string'?body.detail:'Shared cooking state could not be updated');
    return body;
  }

  function ingredientLabel(item,index){
    if(typeof item==='string')return item;
    return item?.name||item?.ingredient||item?.item||`Ingredient ${index+1}`;
  }

  function remaining(timer){
    if(!timer)return 0;
    if(timer.status==='running'&&timer.ends_at){
      const end=Date.parse(timer.ends_at);
      return Number.isFinite(end)?Math.max(0,Math.ceil((end-Date.now())/1000)):0;
    }
    return Math.max(0,Number(timer.remaining_seconds||0));
  }

  function formatSeconds(total){
    const value=Math.max(0,Number(total||0));
    const hours=Math.floor(value/3600),minutes=Math.floor((value%3600)/60),seconds=value%60;
    return hours?`${hours}:${String(minutes).padStart(2,'0')}:${String(seconds).padStart(2,'0')}`:`${minutes}:${String(seconds).padStart(2,'0')}`;
  }

  async function setIngredient(room,index,checked){
    try{
      await api(`/api/live-cook-rooms/${encodeURIComponent(room.id)}/ingredients`,{method:'PUT',body:JSON.stringify({ingredient_index:index,checked,expected_revision:Number(room.state?.revision||0)})});
      await window.GlucoPlateLiveCookRooms?.refresh?.();
    }catch(error){notify(error.message);await window.GlucoPlateLiveCookRooms?.refresh?.()}
  }

  async function timerAction(room,action,durationSeconds){
    try{
      await api(`/api/live-cook-rooms/${encodeURIComponent(room.id)}/timer`,{method:'POST',body:JSON.stringify({action,duration_seconds:durationSeconds||undefined,expected_revision:Number(room.state?.revision||0)})});
      await window.GlucoPlateLiveCookRooms?.refresh?.();
    }catch(error){notify(error.message);await window.GlucoPlateLiveCookRooms?.refresh?.()}
  }

  function enhance(){
    const room=window.GlucoPlateLiveCookRooms?.getRoom?.();
    const body=document.getElementById('liveRoomBody');
    if(!room||!body)return;
    const phase=room.state?.session_status||'waiting';
    let section=body.querySelector('[data-shared-cooking-state]');
    if(!section){
      section=document.createElement('section');
      section.dataset.sharedCookingState='1';
      section.style.cssText='display:grid;gap:.8rem;margin:.8rem 0;padding:.8rem;border:1px solid var(--border,#ddd);border-radius:14px';
      const lifecycle=body.querySelector('[data-session-lifecycle]');
      lifecycle?.insertAdjacentElement('afterend',section)||body.prepend(section);
    }
    const active=phase==='active';
    const ingredients=room.recipe?.ingredients||[];
    const checks=room.state?.ingredient_checks||{};
    const timer=room.state?.timer||{status:'idle'};
    const time=remaining(timer);
    const timerButtons=timer.status==='running'
      ?'<button type="button" data-timer-action="pause">Pause</button><button type="button" data-timer-action="reset">Reset</button>'
      :timer.status==='paused'
        ?'<button type="button" data-timer-action="resume">Resume</button><button type="button" data-timer-action="reset">Reset</button>'
        :'<input data-timer-minutes type="number" min="1" max="1440" value="5" aria-label="Timer minutes"><button type="button" data-timer-action="start">Start timer</button>';

    section.innerHTML=`
      <div><strong>Shared ingredients</strong><div style="display:grid;gap:.35rem;margin-top:.45rem">${ingredients.length?ingredients.map((item,index)=>`<label style="display:flex;gap:.5rem;align-items:center"><input type="checkbox" data-ingredient-index="${index}" ${checks[String(index)]?'checked':''} ${active?'':'disabled'}><span>${escapeHtml(ingredientLabel(item,index))}</span></label>`).join(''):'<span class="live-room-empty">No ingredients are attached to this recipe.</span>'}</div></div>
      <div><strong>Shared timer</strong><div style="display:flex;gap:.45rem;align-items:center;flex-wrap:wrap;margin-top:.45rem"><output data-shared-timer-clock style="font-size:1.35rem;font-weight:800">${formatSeconds(time)}</output><span>${escapeHtml(timer.status||'idle')}</span>${active?timerButtons:'<span class="live-room-empty">Available after the host starts cooking.</span>'}</div></div>`;

    section.querySelectorAll('[data-ingredient-index]').forEach(input=>input.addEventListener('change',()=>setIngredient(room,Number(input.dataset.ingredientIndex),input.checked)));
    section.querySelectorAll('[data-timer-action]').forEach(button=>button.addEventListener('click',()=>{
      const action=button.dataset.timerAction;
      const minutes=Number(section.querySelector('[data-timer-minutes]')?.value||0);
      timerAction(room,action,action==='start'?Math.round(minutes*60):undefined);
    }));
    clearInterval(clock);
    clock=setInterval(()=>{
      const output=section.querySelector('[data-shared-timer-clock]');
      if(output)output.textContent=formatSeconds(remaining(window.GlucoPlateLiveCookRooms?.getRoom?.()?.state?.timer));
    },1000);
  }

  window.addEventListener('DOMContentLoaded',enhance);
  window.addEventListener('glucoplate:live-room-updated',enhance);
  window.addEventListener('pagehide',()=>clearInterval(clock));
})();
