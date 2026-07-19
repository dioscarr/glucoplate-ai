(()=>{
  const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
  let recognition=null,active=false,interim="",refreshTimer=null,busy=false;

  function room(){return window.GlucoPlateLiveCookRooms?.getRoom?.()}
  function uid(){try{return JSON.parse(localStorage.getItem("glucoplate_firebase_session")||"null")?.user?.uid||""}catch{return""}}
  function esc(value){return String(value??"").replace(/[&<>'"]/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[ch]))}
  async function token(force=false){
    if(typeof window.GlucoPlateFirebaseAuth?.getIdToken==="function")return window.GlucoPlateFirebaseAuth.getIdToken(force);
    const cached=localStorage.getItem("glucoplate_firebase_id_token")||"";
    if(!cached)throw new Error("Sign in before using live transcription.");
    return cached;
  }
  async function api(path,options={}){
    const request=async force=>fetch(path,{...options,headers:{"Content-Type":"application/json",Authorization:`Bearer ${await token(force)}`,...(options.headers||{})}});
    let response=await request(false);
    if(response.status===401&&typeof window.GlucoPlateFirebaseAuth?.getIdToken==="function")response=await request(true);
    const body=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(body.detail||"Live transcription is unavailable.");
    return body;
  }

  function section(){
    const body=document.getElementById("liveRoomBody");if(!body)return null;
    let node=body.querySelector("[data-live-transcript]");
    if(!node){node=document.createElement("section");node.className="live-transcript-card";node.dataset.liveTranscript="1";body.appendChild(node)}
    return node;
  }

  function render(state,error=""){
    const node=section();const current=room();if(!node||!current)return;
    const host=String(current.host_uid||"")===String(uid());
    const segments=state?.segments||[];
    const rows=segments.slice(-40).map(item=>`<li><div><strong>${esc(item.speaker_name||"Cook")}</strong><time>${esc(new Date(item.started_at||item.created_at).toLocaleTimeString([],{hour:"numeric",minute:"2-digit"}))}</time></div><p>${esc(item.text)}</p></li>`).join("");
    const disclosure=!state?.enabled
      ?"Audio is not being transcribed. Raw audio is never stored by this feature."
      :state.consented
        ?"Your finalized speech is being shared with this room transcript. Raw audio is not retained."
        :"Room transcription is on, but your audio is not processed until you consent.";
    node.innerHTML=`
      <div class="live-transcript-heading"><div><span>LIVE TRANSCRIPT</span><h3>What the kitchen heard</h3></div><span class="live-transcript-status ${active?"is-active":""}">${active?"Transcribing":state?.enabled?"Available":"Off"}</span></div>
      <p class="live-transcript-disclosure">${esc(disclosure)}</p>
      ${error?`<p class="live-transcript-error">${esc(error)}</p>`:""}
      <div class="live-transcript-actions">
        ${host?`<button type="button" data-room-transcription>${state?.enabled?"Turn off for room":"Enable for room"}</button>`:""}
        ${state?.enabled?`<button type="button" data-my-transcription>${active||state.consented?"Stop my transcript":"Transcribe my audio"}</button>`:""}
      </div>
      ${interim?`<div class="live-transcript-interim"><span>Listening…</span>${esc(interim)}</div>`:""}
      <ol class="live-transcript-list">${rows||"<li class='live-transcript-empty'>Finalized speech will appear here with speaker names and timestamps.</li>"}</ol>`;
    node.querySelector("[data-room-transcription]")?.addEventListener("click",()=>toggleRoom(state));
    node.querySelector("[data-my-transcription]")?.addEventListener("click",()=>active||state.consented?stopMine():startMine());
  }

  async function load(){
    const current=room();if(!current)return;
    try{const result=await api(`/api/live-cook-rooms/${encodeURIComponent(current.id)}/transcription`);render(result.transcription)}
    catch(error){render(null,error.message)}
  }

  async function toggleRoom(state){
    if(busy)return;
    const enabling=!state?.enabled;
    if(enabling&&!confirm("Enable live transcription? Participants must consent individually. Finalized transcript text is shared in this room; raw audio is not retained."))return;
    busy=true;
    try{
      if(!enabling)stopRecognition();
      const result=await api(`/api/live-cook-rooms/${encodeURIComponent(room().id)}/transcription/consent`,{method:"PUT",body:JSON.stringify({accepted:enabling,enable_room:enabling})});
      render(result.transcription);
    }catch(error){render(state,error.message)}
    finally{busy=false}
  }

  async function startMine(){
    if(!SpeechRecognition){render(null,"Live transcription is not supported by this browser. Use a Chromium browser or type important details in chat.");return}
    if(!confirm("Transcribe your microphone audio into speaker-labelled text visible to room participants? Raw audio is not retained."))return;
    try{
      const result=await api(`/api/live-cook-rooms/${encodeURIComponent(room().id)}/transcription/consent`,{method:"PUT",body:JSON.stringify({accepted:true})});
      startRecognition();
      render(result.transcription);
    }catch(error){render(null,error.message)}
  }

  async function stopMine(){
    stopRecognition();
    try{
      const result=await api(`/api/live-cook-rooms/${encodeURIComponent(room().id)}/transcription/consent`,{method:"PUT",body:JSON.stringify({accepted:false})});
      render(result.transcription);
    }catch(error){render(null,error.message)}
  }

  function startRecognition(){
    if(recognition)stopRecognition();
    recognition=new SpeechRecognition();
    recognition.continuous=true;recognition.interimResults=true;recognition.lang=document.documentElement.lang||"en-US";
    recognition.onstart=()=>{active=true;load()};
    recognition.onresult=event=>{
      let pending="";
      for(let i=event.resultIndex;i<event.results.length;i++){
        const result=event.results[i],text=result[0]?.transcript?.trim()||"";
        if(result.isFinal&&text)submit(text,Number(result[0]?.confidence||0));
        else pending+=`${text} `;
      }
      interim=pending.trim();load();
    };
    recognition.onerror=event=>{if(event.error!=="aborted")render(null,`Speech recognition stopped: ${event.error}`)};
    recognition.onend=()=>{const restart=active;recognition=null;if(restart)setTimeout(startRecognition,350)};
    recognition.start();
  }

  function stopRecognition(){active=false;interim="";if(recognition){recognition.abort();recognition=null}}
  async function submit(text,confidence){
    const now=new Date().toISOString();
    try{
      await api(`/api/live-cook-rooms/${encodeURIComponent(room().id)}/transcription/segments`,{method:"POST",body:JSON.stringify({text,confidence,provider:"browser",started_at:now,ended_at:now})});
      interim="";await load();
    }catch(error){render(null,error.message)}
  }

  function mount(){
    load();
    clearInterval(refreshTimer);refreshTimer=setInterval(load,5000);
  }
  window.addEventListener("glucoplate:live-room-updated",()=>queueMicrotask(mount));
  window.addEventListener("pagehide",()=>{stopRecognition();clearInterval(refreshTimer)});
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",mount);else mount();
  window.GlucoPlateLiveTranscript={start:startMine,stop:stopMine,refresh:load,isActive:()=>active};
})();
