(()=>{
  const notify=message=>typeof window.toast==='function'?window.toast(message):console.info(message);
  const escapeHtml=value=>String(value??'').replace(/[&<>'"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
  let pending=false,confirming=false,confirmAction='complete',showingHistory=false,historyData=null,historyRoomId='';

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

  async function request(path,options={}){
    const send=async forceRefresh=>fetch(path,{...options,headers:{'Content-Type':'application/json',Authorization:`Bearer ${await authToken(forceRefresh)}`,...(options.headers||{})}});
    let response=await send(false);
    if(response.status===401&&typeof window.GlucoPlateFirebaseAuth?.getIdToken==='function')response=await send(true);
    const body=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(body.detail||'Could not update the cooking session');
    return body;
  }

  async function transition(action){
    const room=window.GlucoPlateLiveCookRooms?.getRoom?.();
    if(!room)throw new Error('The live cook room is no longer available.');
    const body=await request(`/api/live-cook-rooms/${encodeURIComponent(room.id)}/${action}`,{method:'POST'});
    await window.GlucoPlateLiveCookRooms?.refresh?.();
    return body.room;
  }

  function renderConfirmation(banner,action){
    confirming=true;confirmAction=action;
    const abandoning=action==='abandon';
    banner.innerHTML=`
      <div class="live-room-confirm" role="alertdialog" aria-labelledby="liveRoomFinishTitle">
        <strong id="liveRoomFinishTitle">${abandoning?'End this session early?':'Finish this cooking session?'}</strong>
        <span>${abandoning?'The timeline will be saved as ended early.':'Everyone will leave the live room. Recipe progress, timers, and activity will be saved.'}</span>
        <div class="live-room-confirm-actions">
          <button type="button" data-cancel-complete>Keep cooking</button>
          <button type="button" class="live-room-danger" data-confirm-complete data-confirm-lifecycle="${action}">${abandoning?'End early':'Finish now'}</button>
        </div>
        <small>Only the host can close the room. This action is recorded once.</small>
      </div>`;
  }

  function eventIcon(type){
    if(type.includes('completed'))return '✓';
    if(type.includes('abandoned'))return '■';
    if(type.includes('timer'))return '◷';
    if(type.includes('ingredient'))return '◇';
    if(type.includes('help')||type.includes('question'))return '?';
    if(type.includes('participant'))return '●';
    return '•';
  }

  function formatTime(value){
    const date=new Date(value);if(Number.isNaN(date.getTime()))return'';
    return date.toLocaleString([],{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
  }

  function renderHistory(history){
    const events=history.events||[],feedback=history.my_feedback,summary=history.feedback_summary||{};
    const timeline=events.length?events.map(event=>`<li><span class="live-history-icon">${escapeHtml(eventIcon(String(event.type||'')))}</span><div><strong>${escapeHtml(event.message||String(event.type||'Session update').replaceAll('_',' '))}</strong><small>${escapeHtml(formatTime(event.created_at))}${event.actor_name?' · '+escapeHtml(event.actor_name):''}</small></div></li>`).join(''):'<li class="live-history-empty">No timeline events were recorded.</li>';
    const feedbackPanel=feedback?`<div class="live-feedback-saved"><strong>Thanks for sharing</strong><span>Your rating: ${escapeHtml(feedback.rating)}/5${feedback.would_cook_again?' · Would cook again':''}</span></div>`:`
      <form data-post-cook-feedback>
        <div class="live-feedback-heading"><strong>How did it go?</strong><span>Private feedback helps personalize future recipes.</span></div>
        <label><span>Rating</span><select name="rating" required><option value="5">5 — Loved it</option><option value="4">4 — Great</option><option value="3">3 — Good</option><option value="2">2 — Needs work</option><option value="1">1 — Not for me</option></select></label>
        <label class="live-feedback-check"><input type="checkbox" name="would_cook_again" checked><span>I would cook this again</span></label>
        <label><span>Optional note</span><textarea name="note" maxlength="500" placeholder="What worked or what would you change?"></textarea></label>
        <button type="submit">Save feedback</button>
      </form>`;
    return `<section class="live-session-history" data-session-history>
      <header><div><span>PRIVATE COOK HISTORY</span><strong>${escapeHtml(history.title||'Cooking session')}</strong><small>${escapeHtml(history.status||'completed')} · ${events.length} event${events.length===1?'':'s'}${summary.average_rating?' · '+summary.average_rating+'/5 average':''}</small></div><button type="button" data-close-history aria-label="Close timeline">×</button></header>
      <ol class="live-history-timeline">${timeline}</ol>
      ${feedbackPanel}
      <p class="live-history-recording">No video was recorded. This history contains cooking events only.</p>
    </section>`;
  }

  async function loadHistory(){
    const room=window.GlucoPlateLiveCookRooms?.getRoom?.();if(!room)return;
    showingHistory=true;historyRoomId=room.id;historyData=null;enhance();
    try{historyData=(await request(`/api/live-cook-rooms/${encodeURIComponent(room.id)}/history`)).history}
    catch(error){showingHistory=false;notify(error.message)}
    enhance();
  }

  async function submitFeedback(form){
    const room=window.GlucoPlateLiveCookRooms?.getRoom?.();if(!room)return;
    const data=new FormData(form);
    await request(`/api/live-cook-rooms/${encodeURIComponent(room.id)}/feedback`,{method:'POST',body:JSON.stringify({rating:Number(data.get('rating')),would_cook_again:data.get('would_cook_again')==='on',note:String(data.get('note')||'')})});
    historyData=(await request(`/api/live-cook-rooms/${encodeURIComponent(room.id)}/history`)).history;
    notify('Post-cook feedback saved.');
    enhance();
  }

  async function handleClick(event){
    const control=event.target.closest?.('[data-start-session],[data-complete-session],[data-abandon-session],[data-confirm-lifecycle],[data-confirm-complete],[data-cancel-complete],[data-view-history],[data-close-history]');
    if(!control||pending)return;
    if(control.matches('[data-cancel-complete]')){confirming=false;enhance();return}
    if(control.matches('[data-close-history]')){showingHistory=false;enhance();return}
    if(control.matches('[data-view-history]')){loadHistory();return}
    if(control.matches('[data-complete-session]')){renderConfirmation(control.closest('[data-session-lifecycle]'),'complete');return}
    if(control.matches('[data-abandon-session]')){renderConfirmation(control.closest('[data-session-lifecycle]'),'abandon');return}
    const action=control.matches('[data-start-session]')?'start':control.dataset.confirmLifecycle||confirmAction;
    pending=true;control.disabled=true;
    try{
      await transition(action);
      confirming=false;
      notify(action==='start'?'Cooking session started.':action==='complete'?'Cooking session completed and saved.':'Cooking session ended early and saved.');
    }catch(error){notify(error.message)}
    finally{pending=false;if(control.isConnected)control.disabled=false}
  }

  async function handleSubmit(event){
    const form=event.target.closest?.('[data-post-cook-feedback]');if(!form||pending)return;
    event.preventDefault();pending=true;
    try{await submitFeedback(form)}
    catch(error){notify(error.message)}
    finally{pending=false}
  }

  function installHandlers(body){
    if(body.dataset.lifecycleHandlers==='1')return;
    body.dataset.lifecycleHandlers='1';
    body.addEventListener('click',handleClick);
    body.addEventListener('submit',handleSubmit);
  }

  function enhance(){
    const room=window.GlucoPlateLiveCookRooms?.getRoom?.();
    const body=document.getElementById('liveRoomBody');
    if(!room||!body)return;
    installHandlers(body);
    if(historyRoomId&&historyRoomId!==room.id){showingHistory=false;historyData=null;historyRoomId=''}
    const phase=room.state?.session_status||'waiting';
    const isHost=String(room.host_uid||'')===String(currentUid());
    let banner=body.querySelector('[data-session-lifecycle]');
    if(!banner){banner=document.createElement('section');banner.dataset.sessionLifecycle='1';body.prepend(banner)}
    if(confirming&&isHost&&phase==='active'){renderConfirmation(banner,confirmAction);return}
    confirming=false;
    const terminal=phase==='completed'||phase==='abandoned';
    const label=phase==='active'?'Cooking in progress':phase==='completed'?'Session completed':phase==='abandoned'?'Session ended early':'Waiting for the host';
    const detail=phase==='waiting'?'Get ready while the host prepares the room.':phase==='active'?'Progress, timers, and activity are syncing live.':phase==='abandoned'?'The room closed early. Its private timeline and progress were saved.':'The room is closed and its private timeline has been saved.';
    const action=isHost&&phase==='waiting'?'<button type="button" data-start-session>Start cooking</button>':isHost&&phase==='active'?'<div class="live-room-lifecycle-actions"><button type="button" class="live-room-danger-outline" data-abandon-session>End early</button><button type="button" data-complete-session>Finish session</button></div>':terminal?'<button type="button" data-view-history>'+(showingHistory?'Refresh timeline':'View timeline')+'</button>':'';
    banner.innerHTML=`<div class="live-room-lifecycle-copy"><strong>${label}</strong><span>${detail}</span></div>${action}`;
    body.querySelector('[data-session-history]')?.remove();
    if(showingHistory){
      const shell=document.createElement('div');
      shell.innerHTML=historyData?renderHistory(historyData):'<section class="live-session-history live-history-loading" data-session-history><span>Loading saved timeline…</span></section>';
      banner.after(shell.firstElementChild);
    }
  }

  window.addEventListener('DOMContentLoaded',enhance);
  window.addEventListener('glucoplate:live-room-updated',enhance);
})();
