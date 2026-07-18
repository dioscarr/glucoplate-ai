(()=>{
  const notify=message=>typeof window.toast==='function'?window.toast(message):console.info(message);
  const escapeHtml=value=>String(value??'').replace(/[&<>'"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
  let clock=null,busy=false;

  async function authToken(forceRefresh=false){
    const provider=window.GlucoPlateFirebaseAuth?.getIdToken;
    if(typeof provider==='function')return provider(forceRefresh);
    const cached=localStorage.getItem('glucoplate_firebase_id_token')||'';
    if(!cached)throw new Error('Sign in before using shared cooking controls.');
    return cached;
  }

  async function api(path,options={}){
    const request=async forceRefresh=>fetch(path,{...options,headers:{'Content-Type':'application/json',Authorization:`Bearer ${await authToken(forceRefresh)}`,...(options.headers||{})}});
    let response=await request(false);
    if(response.status===401&&typeof window.GlucoPlateFirebaseAuth?.getIdToken==='function')response=await request(true);
    const body=await response.json().catch(()=>({}));
    if(!response.ok){
      const error=new Error(typeof body.detail==='string'?body.detail:'Shared cooking state could not be updated');
      error.status=response.status;
      throw error;
    }
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

  async function latestRoom(){
    await window.GlucoPlateLiveCookRooms?.refresh?.();
    return window.GlucoPlateLiveCookRooms?.getRoom?.();
  }

  async function mutate(path,method,payloadFactory,retry=true){
    let room=window.GlucoPlateLiveCookRooms?.getRoom?.();
    if(!room)throw new Error('The live cook room is no longer available.');
    try{
      const result=await api(path(room),{method,body:JSON.stringify(payloadFactory(room))});
      await latestRoom();
      return result;
    }catch(error){
      if(error.status===409&&retry){
        room=await latestRoom();
        if(!room)throw error;
        return mutate(path,method,payloadFactory,false);
      }
      throw error;
    }
  }

  async function setIngredient(index,checked){
    return mutate(
      room=>`/api/live-cook-rooms/${encodeURIComponent(room.id)}/ingredients`,
      'PUT',
      room=>({ingredient_index:index,checked,expected_revision:Number(room.state?.revision||0)})
    );
  }

  async function timerAction(action,durationSeconds){
    return mutate(
      room=>`/api/live-cook-rooms/${encodeURIComponent(room.id)}/timer`,
      'POST',
      room=>({action,duration_seconds:durationSeconds||undefined,expected_revision:Number(room.state?.revision||0)})
    );
  }

  async function handleInteraction(event){
    const body=document.getElementById('liveRoomBody');
    if(!body||busy)return;
    const ingredient=event.target.closest?.('[data-ingredient-index]');
    const timerButton=event.target.closest?.('[data-timer-action]');
    if(!ingredient&&!timerButton)return;

    event.preventDefault();
    busy=true;
    const control=ingredient||timerButton;
    control.disabled=true;
    try{
      if(ingredient){
        await setIngredient(Number(ingredient.dataset.ingredientIndex),ingredient.checked);
      }else{
        const section=timerButton.closest('[data-shared-cooking-state]');
        const action=timerButton.dataset.timerAction;
        const minutes=Number(section?.querySelector('[data-timer-minutes]')?.value||0);
        if(action==='start'&&(!Number.isFinite(minutes)||minutes<1))throw new Error('Enter at least 1 minute.');
        await timerAction(action,action==='start'?Math.round(minutes*60):undefined);
      }
    }catch(error){
      notify(error.message);
      await latestRoom().catch(()=>{});
    }finally{
      busy=false;
      if(control.isConnected)control.disabled=false;
    }
  }

  function installDelegatedHandlers(body){
    if(body.dataset.sharedStateHandlers==='1')return;
    body.dataset.sharedStateHandlers='1';
    body.addEventListener('change',handleInteraction);
    body.addEventListener('click',handleInteraction);
  }

  function enhance(){
    const room=window.GlucoPlateLiveCookRooms?.getRoom?.();
    const body=document.getElementById('liveRoomBody');
    if(!room||!body)return;
    installDelegatedHandlers(body);
    const phase=room.state?.session_status||'waiting';
    let section=body.querySelector('[data-shared-cooking-state]');
    if(!section){
      section=document.createElement('section');
      section.dataset.sharedCookingState='1';
      section.className='live-room-shared-state';
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
        :'<input data-timer-minutes type="number" inputmode="numeric" min="1" max="1440" value="5" aria-label="Timer minutes"><button type="button" data-timer-action="start">Start timer</button>';

    section.innerHTML=`
      <div class="live-room-shared-section"><div class="live-room-section-heading"><div><strong>Shared ingredients</strong><span>Tap an image to enlarge and hear its name</span></div><span aria-hidden="true">🥬</span></div><ul class="ingredient-list live-room-ingredient-list">${ingredients.length?ingredients.map((item,index)=>{const label=ingredientLabel(item,index),icon=window.GlucoPlateIngredients?.ingredientIconFor?.(label)||'🥄';return `<li><label><input type="checkbox" data-ingredient-index="${index}" ${checks[String(index)]?'checked':''} ${active?'':'disabled'}><span class="ingredient-icon" aria-hidden="true">${icon}</span><span>${escapeHtml(label)}</span></label></li>`}).join(''):'<li class="live-room-empty">No ingredients are attached to this recipe.</li>'}</ul></div>
      <div class="live-room-shared-section"><div class="live-room-section-heading"><div><strong>Shared timer</strong><span>Keep every cook on the same pace</span></div><span aria-hidden="true">⏱</span></div><div class="live-room-timer-controls"><output data-shared-timer-clock style="font-size:1.35rem;font-weight:800">${formatSeconds(time)}</output><span>${escapeHtml(timer.status||'idle')}</span>${active?timerButtons:'<span class="live-room-empty">Available after the host starts cooking.</span>'}</div></div>`;

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