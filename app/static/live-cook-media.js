(()=>{
  const notify=message=>typeof window.toast==='function'?window.toast(message):console.info(message);
  const SDK_URL='https://cdn.jsdelivr.net/npm/livekit-client@2.17.2/dist/livekit-client.umd.min.js';
  let stream=null,access=null,busy=false,liveRoom=null,sdkPromise=null;
  async function authToken(forceRefresh=false){const provider=window.GlucoPlateFirebaseAuth?.getIdToken;if(typeof provider==='function')return provider(forceRefresh);const cached=localStorage.getItem('glucoplate_firebase_id_token')||'';if(!cached)throw new Error('Sign in before using live video.');return cached}
  async function api(path,options={}){const request=async forceRefresh=>fetch(path,{...options,headers:{'Content-Type':'application/json',Authorization:'Bearer '+await authToken(forceRefresh),...(options.headers||{})}});let response=await request(false);if(response.status===401&&window.GlucoPlateFirebaseAuth?.getIdToken)response=await request(true);const body=await response.json().catch(()=>({}));if(!response.ok)throw new Error(body.detail||'Live media is unavailable.');return body}
  function ensureStyles(){if(document.querySelector('link[data-live-media-styles]'))return;const link=document.createElement('link');link.rel='stylesheet';link.href='/static/live-cook-media.css';link.dataset.liveMediaStyles='1';document.head.appendChild(link)}
  function loadLiveKit(){if(window.LivekitClient)return Promise.resolve(window.LivekitClient);if(sdkPromise)return sdkPromise;sdkPromise=new Promise((resolve,reject)=>{const script=document.createElement('script');script.src=SDK_URL;script.async=true;script.crossOrigin='anonymous';script.onload=()=>window.LivekitClient?resolve(window.LivekitClient):reject(new Error('LiveKit loaded without a browser client.'));script.onerror=()=>reject(new Error('The video-call client could not be loaded.'));document.head.appendChild(script)});return sdkPromise}
  async function saveState(state){const room=window.GlucoPlateLiveCookRooms?.getRoom?.();if(!room)return;await api('/api/live-cook-rooms/'+encodeURIComponent(room.id)+'/media/state',{method:'PUT',body:JSON.stringify(state)})}
  const tracks=kind=>stream?.getTracks?.().filter(track=>track.kind===kind)||[];
  const connected=()=>Boolean(stream||liveRoom);
  const cameraEnabled=()=>liveRoom?Boolean(liveRoom.localParticipant?.isCameraEnabled):tracks('video').some(track=>track.enabled);
  const microphoneEnabled=()=>liveRoom?Boolean(liveRoom.localParticipant?.isMicrophoneEnabled):tracks('audio').some(track=>track.enabled);
  function safeName(participant,fallback){return String(participant?.name||participant?.identity||fallback||'Cook').split(':').pop().slice(0,80)}
  function publications(participant){return Array.from(participant?.trackPublications?.values?.()||[])}
  function attachTrack(track,parent){if(!track||!parent)return;const element=track.attach();element.autoplay=true;element.playsInline=true;if(track.kind==='video')element.className='live-media-video';else element.className='live-media-audio';parent.appendChild(element)}
  function renderProviderTiles(section){
    const grid=section.querySelector('[data-media-grid]');if(!grid)return;
    if(stream){const tile=document.createElement('div');tile.className='live-media-tile local';tile.innerHTML='<div class="live-media-tile-label">You</div>';const video=document.createElement('video');video.muted=true;video.autoplay=true;video.playsInline=true;video.srcObject=stream;tile.prepend(video);grid.appendChild(tile);return}
    if(!liveRoom)return;
    const addParticipant=(participant,label,local=false)=>{const tile=document.createElement('div');tile.className='live-media-tile'+(local?' local':'');tile.dataset.participantIdentity=participant.identity||'local';tile.innerHTML='<div class="live-media-tile-placeholder"><span>◉</span><strong>'+label+'</strong><small>Camera is off</small></div><div class="live-media-tile-label">'+label+(local?' · You':'')+'</div>';let hasVideo=false;publications(participant).forEach(publication=>{const track=publication.track;if(!track)return;if(track.kind==='video'){hasVideo=true;attachTrack(track,tile)}else if(!local)attachTrack(track,section)});if(hasVideo)tile.classList.add('has-video');grid.appendChild(tile)};
    addParticipant(liveRoom.localParticipant,safeName(liveRoom.localParticipant,access?.participant?.display_name),true);
    Array.from(liveRoom.remoteParticipants?.values?.()||[]).forEach(participant=>addParticipant(participant,safeName(participant,'Cook')));
  }
  function render(){
    const room=window.GlucoPlateLiveCookRooms?.getRoom?.(),body=document.getElementById('liveRoomBody');if(!room||!body)return;ensureStyles();const phase=room.state?.session_status||'waiting';let section=body.querySelector('[data-live-media]');if(phase==='completed'){section?.remove();stopMedia(false);return}if(!section){section=document.createElement('section');section.dataset.liveMedia='1';body.prepend(section)}
    const on=connected(),camera=cameraEnabled(),microphone=microphoneEnabled(),remote=Boolean(liveRoom);
    section.innerHTML='<div class="live-media-header"><div><span>LIVE VIDEO</span><strong>Cook face to face</strong></div><span class="live-media-status">'+(remote?'Connected':on?'Preview ready':'Off')+'</span></div><div class="live-media-grid'+(on?'':' is-empty')+'" data-media-grid></div>'+(on?'':'<div class="live-media-empty"><span>◉</span><strong>Video is optional</strong><small>The recipe, timer, and chat keep working without it.</small></div>')+'<div class="live-media-actions">'+(on?'<button type="button" data-media-mic>'+(microphone?'Mute':'Unmute')+'</button><button type="button" data-media-camera>'+(camera?'Camera off':'Camera on')+'</button><button type="button" class="live-media-leave" data-media-leave>Leave call</button>':'<button type="button" class="live-media-enable" data-media-enable>Join video call</button>')+'</div><p class="live-media-note">'+(remote?'Encrypted in transit through the configured LiveKit room. Recording is off.':access?.configuration_error?'Video calls need Render LiveKit credentials. Private preview remains available.':'Camera preview is private until a LiveKit provider is configured.')+'</p>';
    renderProviderTiles(section);
  }
  function bindLiveKitEvents(sdk){
    const refresh=()=>render();
    liveRoom.on(sdk.RoomEvent.TrackSubscribed,refresh).on(sdk.RoomEvent.TrackUnsubscribed,refresh).on(sdk.RoomEvent.LocalTrackPublished,refresh).on(sdk.RoomEvent.LocalTrackUnpublished,refresh).on(sdk.RoomEvent.ParticipantConnected,refresh).on(sdk.RoomEvent.ParticipantDisconnected,refresh).on(sdk.RoomEvent.Reconnecting,()=>{notify('Video is reconnecting…');render()}).on(sdk.RoomEvent.Reconnected,refresh).on(sdk.RoomEvent.Disconnected,()=>{liveRoom=null;render()});
  }
  async function startMedia(){
    if(busy||connected())return;busy=true;
    try{
      const room=window.GlucoPlateLiveCookRooms?.getRoom?.();if(!room)throw new Error('Join a live room first.');
      access=(await api('/api/live-cook-rooms/'+encodeURIComponent(room.id)+'/media/access')).access;
      await saveState({connection_state:'requesting'});
      if(access?.remote_enabled&&access?.provider==='livekit'){
        const sdk=await loadLiveKit();liveRoom=new sdk.Room({adaptiveStream:true,dynacast:true});bindLiveKitEvents(sdk);await liveRoom.connect(access.server_url,access.token);await liveRoom.localParticipant.setCameraEnabled(true);await liveRoom.localParticipant.setMicrophoneEnabled(true);
      }else{
        if(!navigator.mediaDevices?.getUserMedia){await saveState({connection_state:'unsupported'});throw new Error('Camera and microphone are not supported on this device.')}
        stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:true});
      }
      await saveState({connection_state:'connected',camera_enabled:true,microphone_enabled:true});window.DeviceManager?.haptic?.('success');render();
    }catch(error){const denied=error?.name==='NotAllowedError';if(liveRoom){liveRoom.disconnect();liveRoom=null}await saveState({connection_state:denied?'denied':'failed',camera_enabled:false,microphone_enabled:false}).catch(()=>{});notify(denied?'Camera permission was declined. Cooking controls still work.':error.message)}
    finally{busy=false}
  }
  async function toggle(kind){
    if(liveRoom){if(kind==='video')await liveRoom.localParticipant.setCameraEnabled(!cameraEnabled());else await liveRoom.localParticipant.setMicrophoneEnabled(!microphoneEnabled())}
    else{const list=tracks(kind);if(!list.length)return;const enabled=!list.some(track=>track.enabled);list.forEach(track=>{track.enabled=enabled})}
    const enabled=kind==='video'?cameraEnabled():microphoneEnabled();await saveState(kind==='video'?{camera_enabled:enabled}:{microphone_enabled:enabled}).catch(()=>{});render();
  }
  async function stopMedia(report=true){stream?.getTracks?.().forEach(track=>track.stop());stream=null;if(liveRoom){liveRoom.disconnect();liveRoom=null}if(report)await saveState({connection_state:'idle',camera_enabled:false,microphone_enabled:false}).catch(()=>{});render()}
  function handleClick(event){if(event.target.closest?.('[data-media-enable]'))startMedia();else if(event.target.closest?.('[data-media-mic]'))toggle('audio');else if(event.target.closest?.('[data-media-camera]'))toggle('video');else if(event.target.closest?.('[data-media-leave]'))stopMedia()}
  window.addEventListener('DOMContentLoaded',()=>{document.body.addEventListener('click',handleClick);render()});window.addEventListener('glucoplate:live-room-updated',render);window.addEventListener('pagehide',()=>stopMedia(false));window.GlucoPlateLiveMedia={startMedia,stopMedia,toggle,getStream:()=>stream,getRoom:()=>liveRoom};
})();