(()=>{
  const media=query=>window.matchMedia?.(query)?.matches===true;
  const ua=navigator.userAgent||'';
  const platform=navigator.platform||'';
  const touchMac=platform==='MacIntel'&&navigator.maxTouchPoints>1;
  const isIOS=/iPad|iPhone|iPod/i.test(ua)||touchMac;
  const isAndroid=/Android/i.test(ua);
  const isStandalone=()=>media('(display-mode: standalone)')||navigator.standalone===true;
  const capabilities=()=>({
    ios:isIOS,
    android:isAndroid,
    standalone:isStandalone(),
    touch:navigator.maxTouchPoints>0,
    online:navigator.onLine,
    share:typeof navigator.share==='function',
    clipboard:Boolean(navigator.clipboard),
    camera:Boolean(navigator.mediaDevices?.getUserMedia),
    wakeLock:Boolean(navigator.wakeLock?.request),
    notifications:'Notification'in window,
    push:'PushManager'in window&&'serviceWorker'in navigator,
    vibration:typeof navigator.vibrate==='function'
  });
  let wakeLock=null;
  async function requestWakeLock(){
    if(!capabilities().wakeLock)return false;
    try{wakeLock=await navigator.wakeLock.request('screen');return true}catch{return false}
  }
  async function releaseWakeLock(){
    try{await wakeLock?.release()}catch{}finally{wakeLock=null}
  }
  function haptic(pattern='light'){
    const patterns={light:10,medium:20,success:[12,35,12],warning:[20,40,20]};
    if(capabilities().vibration)navigator.vibrate(patterns[pattern]||patterns.light);
  }
  async function share({title='GlucoPlate AI',text='',url=location.href}={}){
    if(capabilities().share){await navigator.share({title,text,url});return true}
    if(capabilities().clipboard){await navigator.clipboard.writeText([title,text,url].filter(Boolean).join('\n'));return false}
    return false;
  }
  function applyDocumentState(){
    const state=capabilities();
    const root=document.documentElement;
    root.dataset.platform=state.ios?'ios':state.android?'android':'desktop';
    root.dataset.standalone=String(state.standalone);
    root.dataset.online=String(state.online);
    root.classList.toggle('is-standalone',state.standalone);
    root.classList.toggle('is-ios',state.ios);
    root.classList.toggle('is-offline',!state.online);
    window.dispatchEvent(new CustomEvent('glucoplate:devicechange',{detail:state}));
  }
  window.addEventListener('online',applyDocumentState);
  window.addEventListener('offline',applyDocumentState);
  window.matchMedia?.('(display-mode: standalone)')?.addEventListener?.('change',applyDocumentState);
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible'&&wakeLock)requestWakeLock()});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',applyDocumentState);else applyDocumentState();
  window.DeviceManager={capabilities,isIOS:()=>isIOS,isAndroid:()=>isAndroid,isStandalone,haptic,share,requestWakeLock,releaseWakeLock,applyDocumentState};
})();
