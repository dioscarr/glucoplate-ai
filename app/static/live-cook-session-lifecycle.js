(()=>{
  const notify=message=>typeof window.toast==='function'?window.toast(message):console.info(message);
  async function authToken(){
    const provider=window.GlucoPlateFirebaseAuth?.getIdToken;
    if(typeof provider==='function')return provider(false);
    const cached=localStorage.getItem('glucoplate_firebase_id_token')||'';
    if(!cached)throw new Error('Sign in before using a live cook room.');
    return cached;
  }

  function currentUid(){
    try{return JSON.parse(localStorage.getItem('glucoplate_firebase_session')||'null')?.user?.uid||''}
    catch{return''}
  }

  async function transition(roomId,action){
    const response=await fetch(`/api/live-cook-rooms/${encodeURIComponent(roomId)}/${action}`,{
      method:'POST',
      headers:{'Content-Type':'application/json',Authorization:`Bearer ${await authToken()}`}
    });
    const body=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(body.detail||'Could not update the cooking session');
    await window.GlucoPlateLiveCookRooms?.refresh?.();
    return body.room;
  }

  function enhance(){
    const room=window.GlucoPlateLiveCookRooms?.getRoom?.();
    const body=document.getElementById('liveRoomBody');
    if(!room||!body)return;

    const phase=room.state?.session_status||'waiting';
    const isHost=String(room.host_uid||'')===String(currentUid());
    let banner=body.querySelector('[data-session-lifecycle]');
    if(!banner){
      banner=document.createElement('section');
      banner.dataset.sessionLifecycle='1';
      banner.style.cssText='margin:.7rem 0;padding:.75rem;border-radius:14px;background:var(--surfaceAlt,#f6f1ed);display:grid;gap:.5rem';
      body.prepend(banner);
    }

    const label=phase==='active'?'Cooking in progress':phase==='completed'?'Session completed':'Waiting for the host';
    const action=isHost&&phase==='waiting'?'<button type="button" data-start-session>Start cooking</button>':isHost&&phase==='active'?'<button type="button" data-complete-session>Finish session</button>':'';
    banner.innerHTML=`<strong>${label}</strong><span>${phase==='waiting'?'Participants can get ready before the host begins.':phase==='active'?'Shared cooking progress is now active.':'This room is read-only and saved as completed.'}</span>${action}`;

    banner.querySelector('[data-start-session]')?.addEventListener('click',async event=>{
      event.currentTarget.disabled=true;
      try{await transition(room.id,'start');notify('Cooking session started.')}
      catch(error){event.currentTarget.disabled=false;notify(error.message)}
    });
    banner.querySelector('[data-complete-session]')?.addEventListener('click',async event=>{
      if(!confirm('Finish this live cooking session?'))return;
      event.currentTarget.disabled=true;
      try{await transition(room.id,'complete');notify('Cooking session completed.')}
      catch(error){event.currentTarget.disabled=false;notify(error.message)}
    });
  }

  window.addEventListener('DOMContentLoaded',enhance);
  window.addEventListener('glucoplate:live-room-updated',enhance);
})();
