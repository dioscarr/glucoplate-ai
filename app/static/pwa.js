(()=>{
  const addHead=(tag,attrs)=>{const el=document.createElement(tag);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v));document.head.appendChild(el)};
  if(!document.querySelector('link[rel="manifest"]'))addHead('link',{rel:'manifest',href:'/static/manifest.webmanifest'});
  if(!document.querySelector('meta[name="theme-color"]'))addHead('meta',{name:'theme-color',content:'#f26a2e'});
  if(!document.querySelector('meta[name="apple-mobile-web-app-capable"]'))addHead('meta',{name:'apple-mobile-web-app-capable',content:'yes'});
  if(!document.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]'))addHead('meta',{name:'apple-mobile-web-app-status-bar-style',content:'default'});
  if(!document.querySelector('link[rel="apple-touch-icon"]'))addHead('link',{rel:'apple-touch-icon',href:'/static/icons/icon-192.svg'});

  let deferredInstall=null;
  let wakeLock=null;
  window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();deferredInstall=event;renderPwaPanel()});

  const standalone=()=>window.matchMedia('(display-mode: standalone)').matches||window.navigator.standalone===true;
  const isiOS=()=>/iphone|ipad|ipod/i.test(navigator.userAgent);
  const pushSupported=()=>('serviceWorker'in navigator)&&('Notification'in window)&&('PushManager'in window);
  const b64ToBytes=value=>{const pad='='.repeat((4-value.length%4)%4),base64=(value+pad).replace(/-/g,'+').replace(/_/g,'/'),raw=atob(base64);return Uint8Array.from([...raw].map(c=>c.charCodeAt(0)))};

  function installNativeStyles(){
    if(document.getElementById('iosPwaStyles'))return;
    const style=document.createElement('style');
    style.id='iosPwaStyles';
    style.textContent=`
      :root{--safe-top:env(safe-area-inset-top,0px);--safe-right:env(safe-area-inset-right,0px);--safe-bottom:env(safe-area-inset-bottom,0px);--safe-left:env(safe-area-inset-left,0px);--ios-spring:cubic-bezier(.2,.85,.25,1.15)}
      body{padding-left:var(--safe-left);padding-right:var(--safe-right);-webkit-tap-highlight-color:transparent}
      .app-header{padding-top:max(8px,var(--safe-top))!important}
      .bottom-nav{padding-bottom:max(8px,var(--safe-bottom))!important}
      button,.btn,.tab,.food-chip,.recipe-idea{touch-action:manipulation;-webkit-user-select:none;user-select:none}
      .ios-press{transition:transform 140ms var(--ios-spring),filter 140ms ease!important}
      .ios-press:active{transform:scale(.965)!important;filter:brightness(.97)}
      #iosSheetBackdrop{position:fixed;inset:0;z-index:1200;background:rgba(0,0,0,.28);backdrop-filter:blur(8px);opacity:0;transition:opacity 220ms ease;padding:0 10px max(10px,var(--safe-bottom));display:flex;align-items:flex-end}
      #iosSheetBackdrop.open{opacity:1}
      #iosSheet{width:min(620px,100%);margin:0 auto;background:rgba(250,250,250,.96);border:1px solid rgba(0,0,0,.08);border-radius:26px 26px 20px 20px;box-shadow:0 24px 70px rgba(0,0,0,.24);padding:9px 14px 16px;transform:translateY(105%);transition:transform 320ms var(--ios-spring)}
      #iosSheetBackdrop.open #iosSheet{transform:translateY(0)}
      .ios-sheet-grabber{width:42px;height:5px;border-radius:999px;background:#c7c7cc;margin:0 auto 14px}
      .ios-sheet-action{width:100%;border:0;background:#fff;padding:15px;border-radius:16px;margin-top:8px;font-weight:800;text-align:left}
      .ios-sheet-action strong{display:block}.ios-sheet-action span{display:block;color:#777;font-size:.78rem;margin-top:3px;font-weight:600}
      .ios-native-bar{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
      .ios-status{font-size:.76rem;color:#756f69;margin-top:8px;line-height:1.35}
      @media(prefers-reduced-motion:reduce){#iosSheetBackdrop,#iosSheet,.ios-press{transition:none!important}}
    `;
    document.head.appendChild(style);
    document.querySelectorAll('button,.btn,.tab,.food-chip,.recipe-idea').forEach(el=>el.classList.add('ios-press'));
    new MutationObserver(()=>document.querySelectorAll('button:not(.ios-press),.btn:not(.ios-press),.tab:not(.ios-press),.food-chip:not(.ios-press),.recipe-idea:not(.ios-press)').forEach(el=>el.classList.add('ios-press'))).observe(document.body,{childList:true,subtree:true});
  }

  async function registerWorker(){if(!('serviceWorker'in navigator))return null;return navigator.serviceWorker.register('/static/sw.js',{scope:'/'}).then(()=>navigator.serviceWorker.ready)}

  async function subscribe(){
    if(!pushSupported()){showMessage('Push notifications are not supported on this device.');return}
    if(isiOS()&&!standalone()){showInstallSheet();return}
    const permission=await Notification.requestPermission();
    if(permission!=='granted'){showMessage('Notification permission was not granted.');return}
    const registration=await registerWorker();
    const config=await fetch('/api/push/config').then(r=>r.json());
    if(!config.vapid_public_key){showMessage('Push is ready in the app, but the server VAPID key is not configured yet.');return}
    let subscription=await registration.pushManager.getSubscription();
    if(!subscription)subscription=await registration.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:b64ToBytes(config.vapid_public_key)});
    const session=JSON.parse(localStorage.getItem('glucoplate_session')||'null');
    await fetch('/api/push/subscriptions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subscription:subscription.toJSON(),user_id:session?.user?.user_id||null,profile_id:session?.active_profile?.profile_id||null})});
    if('setAppBadge'in navigator)navigator.setAppBadge(1).catch(()=>{});
    showMessage('Phone notifications are enabled.');
    renderPwaPanel();
  }

  async function install(){
    if(deferredInstall){deferredInstall.prompt();await deferredInstall.userChoice;deferredInstall=null;renderPwaPanel();return}
    if(isiOS()&&!standalone()){showInstallSheet();return}
    showMessage('Use your browser menu and choose Install app or Add to Home Screen.');
  }

  async function shareApp(){
    const data={title:'GlucoPlate AI',text:'Discover recipes and cook step by step with GlucoPlate.',url:location.href};
    if(navigator.share){try{await navigator.share(data);return}catch(error){if(error?.name==='AbortError')return}}
    try{await navigator.clipboard.writeText(location.href);showMessage('App link copied.')}catch{showMessage('Copy the address from your browser to share GlucoPlate.')}
  }

  async function toggleWakeLock(){
    if(!('wakeLock'in navigator)){showMessage('Keep-screen-awake is not supported on this device.');return}
    if(wakeLock){await wakeLock.release();wakeLock=null;showMessage('Screen wake lock released.');renderPwaPanel();return}
    try{wakeLock=await navigator.wakeLock.request('screen');wakeLock.addEventListener('release',()=>{wakeLock=null;renderPwaPanel()});showMessage('Screen will stay awake while you cook.');renderPwaPanel()}catch{showMessage('Unable to keep the screen awake right now.')}
  }

  function showInstallSheet(){
    document.getElementById('iosSheetBackdrop')?.remove();
    const backdrop=document.createElement('div');
    backdrop.id='iosSheetBackdrop';
    backdrop.innerHTML=`<div id="iosSheet" role="dialog" aria-modal="true" aria-label="Install GlucoPlate"><div class="ios-sheet-grabber"></div><h2 style="margin:0 4px 6px;font-size:1.35rem">Add GlucoPlate to iPhone</h2><p style="margin:0 4px 10px;color:#6e6e73;line-height:1.4">Safari does not show an automatic install popup. Use the iOS Share sheet:</p><button class="ios-sheet-action ios-press" type="button"><strong>1. Tap Share</strong><span>The square with the upward arrow in Safari.</span></button><button class="ios-sheet-action ios-press" type="button"><strong>2. Choose Add to Home Screen</strong><span>Scroll the Share sheet if the option is lower down.</span></button><button class="ios-sheet-action ios-press" type="button"><strong>3. Open the new GlucoPlate icon</strong><span>Then enable notifications from inside the installed app.</span></button><button id="closeIosSheet" class="btn primary full ios-press" type="button" style="margin-top:12px">Got it</button></div>`;
    document.body.appendChild(backdrop);
    requestAnimationFrame(()=>backdrop.classList.add('open'));
    const close=()=>{backdrop.classList.remove('open');setTimeout(()=>backdrop.remove(),240)};
    backdrop.addEventListener('click',event=>{if(event.target===backdrop)close()});
    document.getElementById('closeIosSheet').onclick=close;
    let startY=0;
    const sheet=backdrop.querySelector('#iosSheet');
    sheet.addEventListener('touchstart',event=>{startY=event.touches[0].clientY},{passive:true});
    sheet.addEventListener('touchend',event=>{if(event.changedTouches[0].clientY-startY>70)close()},{passive:true});
  }

  function showMessage(message){
    if(typeof window.toast==='function')window.toast(message);
    else{
      let node=document.getElementById('pwaMessage');
      if(!node){node=document.createElement('div');node.id='pwaMessage';node.style='position:fixed;left:50%;bottom:calc(88px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);z-index:999;background:#211f1d;color:white;padding:11px 15px;border-radius:999px;max-width:90%;text-align:center;font:600 13px system-ui';document.body.appendChild(node)}
      node.textContent=message;clearTimeout(node._timer);node._timer=setTimeout(()=>node.remove(),6000)
    }
  }

  function panelHtml(){
    const notificationText=('Notification'in window&&Notification.permission==='granted')?'Notifications enabled':'Enable notifications';
    const instruction=isiOS()&&!standalone()?'On iPhone: open in Safari, tap Share, then Add to Home Screen.':'Use iOS-style sharing, phone notifications, offline mode, and Cook Mode screen wake lock.';
    return `<div id="pwaPanel" style="margin-top:16px;padding:16px;border:1px solid #e7ded4;border-radius:20px;background:#fff;box-shadow:0 10px 28px rgba(59,43,30,.08)"><strong style="display:block">iPhone & app features</strong><span style="display:block;color:#756f69;font-size:.82rem;margin:5px 0 12px">${instruction}</span><div class="ios-native-bar"><button id="installPwaBtn" class="btn secondary ios-press" type="button">${standalone()?'App installed':'Install app'}</button><button id="enablePushBtn" class="btn primary ios-press" type="button">${notificationText}</button><button id="sharePwaBtn" class="btn ghost ios-press" type="button">Share</button><button id="wakeLockBtn" class="btn ghost ios-press" type="button">${wakeLock?'Keep awake: On':'Keep screen awake'}</button></div><div class="ios-status">${standalone()?'Running as an installed Home Screen app.':'Install for the most native iPhone experience.'}</div></div>`
  }

  function renderPwaPanel(){
    document.getElementById('pwaPanel')?.remove();
    const home=document.getElementById('homeView');
    const profile=document.getElementById('profileView');
    const target=home?.querySelector('.card')||profile?.querySelector('.card')||document.querySelector('main')||document.body;
    target.insertAdjacentHTML('beforeend',panelHtml());
    document.getElementById('installPwaBtn').onclick=install;
    document.getElementById('enablePushBtn').onclick=subscribe;
    document.getElementById('sharePwaBtn').onclick=shareApp;
    document.getElementById('wakeLockBtn').onclick=toggleWakeLock;
  }

  function enhanceTransitions(){
    if(typeof window.showView!=='function')return;
    const original=window.showView;
    window.showView=id=>{
      if(document.startViewTransition&&!window.matchMedia('(prefers-reduced-motion: reduce)').matches){document.startViewTransition(()=>original(id))}
      else original(id)
    }
  }

  function trackViewport(){
    if(!window.visualViewport)return;
    const update=()=>document.documentElement.style.setProperty('--visual-height',`${window.visualViewport.height}px`);
    window.visualViewport.addEventListener('resize',update);
    update();
  }

  document.addEventListener('visibilitychange',async()=>{
    if(document.visibilityState==='visible'&&wakeLock&&'wakeLock'in navigator){try{wakeLock=await navigator.wakeLock.request('screen')}catch{wakeLock=null}}
  });

  window.addEventListener('DOMContentLoaded',()=>{
    installNativeStyles();
    trackViewport();
    enhanceTransitions();
    registerWorker().catch(()=>{});
    renderPwaPanel();
  });

  window.GlucoPlatePwa={install,subscribe,registerWorker,shareApp,toggleWakeLock,showInstallSheet};
})();