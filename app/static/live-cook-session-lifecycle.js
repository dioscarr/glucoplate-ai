(()=>{
  const notify=message=>typeof window.toast==='function'?window.toast(message):console.info(message);
  let pending=false,confirming=false;

  async function authToken(forceRefresh=false){
    const provider=window.GlucoPlateFirebaseAuth?.getIdToken;
    if(typeof provider==='function')return provider(forceRefresh);
    const cached=localStorage.getItem('glucoplate_firebase_id_token')||'';
    if(!cached)throw new Error('Sign in before using a live cook room.');
    return cached;
  }

  function currentUid(){
    try{return JSON.parse(localStorage.getItem('glucoplate_firebase_session')||'null')?.user?.uid||''}
    catch{return''}
  }

  async function transition(action){
    const room=window.GlucoPlateLiveCookRooms?.getRoom?.();
    if(!room)throw new Error('The live cook room is no longer available.');
    const request=async forceRefresh=>fetch(`/api/live-cook-rooms/${encodeURIComponent(room.id)}/${action}`,{
      method:'POST',
      headers:{'Content-Type':'application/json',Authorization:`Bearer ${await authToken(forceRefresh)}`}
    });
    let response=await request(false);
    if(response.status===401&&typeof window.GlucoPlateFirebaseAuth?.getIdToken==='function')response=await request(true);
    const body=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(body.detail||'Could not update the cooking session');
    await window.GlucoPlateLiveCookRooms?.refresh?.();
    return body.room;
  }

  function renderConfirmation(banner){
    confirming=true;
    banner.innerHTML=`
      <div class="live-room-confirm" role="alertdialog" aria-labelledby="liveRoomFinishTitle">
        <strong id="liveRoomFinishTitle">Finish this cooking session?</strong>
        <span>Everyone will leave the live room. Recipe progress, timers, and activity will be saved.</span>
        <div class="live-room-confirm-actions">
          <button type="button" data-cancel-complete>Keep cooking</button>
          <button type="button" class="live-room-danger" data-confirm-complete>Finish now</button>
        </div>
        <small>Only the host can finish the room.</small>
      </div>`;
  }

  async function handleClick(event){
    const actionControl=event.target.closest?.('[data-start-session],[data-complete-session],[data-confirm-complete],[data-cancel-complete]');
    if(!actionControl||pending)return;
    if(actionControl.matches('[data-cancel-complete]')){confirming=false;enhance();return}
    if(actionControl.matches('[data-complete-session]')){renderConfirmation(actionControl.closest('[data-session-lifecycle]'));return}
    const action=actionControl.matches('[data-start-session]')?'start':'complete';
    pending=true;actionControl.disabled=true;
    try{
      await transition(action);
      confirming=false;
      notify(action==='start'?'Cooking session started.':'Cooking session completed and saved.');
    }catch(error){notify(error.message)}
    finally{pending=false;if(actionControl.isConnected)actionControl.disabled=false}
  }

  function installHandlers(body){
    if(body.dataset.lifecycleHandlers==='1')return;
    body.dataset.lifecycleHandlers='1';
    body.addEventListener('click',handleClick);
  }

  function enhance(){
    const room=window.GlucoPlateLiveCookRooms?.getRoom?.();
    const body=document.getElementById('liveRoomBody');
    if(!room||!body)return;
    installHandlers(body);
    const phase=room.state?.session_status||'waiting';
    const isHost=String(room.host_uid||'')===String(currentUid());
    let banner=body.querySelector('[data-session-lifecycle]');
    if(!banner){
      banner=document.createElement('section');
      banner.dataset.sessionLifecycle='1';
      body.prepend(banner);
    }
    if(confirming&&isHost&&phase==='active'){renderConfirmation(banner);return}
    confirming=false;
    const label=phase==='active'?'Cooking in progress':phase==='completed'?'Session completed':'Waiting for the host';
    const detail=phase==='waiting'?'Get ready while the host prepares the room.':phase==='active'?'Progress, timers, and activity are syncing live.':'The room is closed and its progress has been saved.';
    const action=isHost&&phase==='waiting'?'<button type="button" data-start-session>Start cooking</button>':isHost&&phase==='active'?'<button type="button" class="live-room-danger-outline" data-complete-session>Finish session</button>':'';
    banner.innerHTML=`<div class="live-room-lifecycle-copy"><strong>${label}</strong><span>${detail}</span></div>${action}`;
  }

  window.addEventListener('DOMContentLoaded',enhance);
  window.addEventListener('glucoplate:live-room-updated',enhance);
})();