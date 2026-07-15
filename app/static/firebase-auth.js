(()=>{
  let sdk=null,authClient=null;
  const notify=message=>typeof window.toast==='function'?window.toast(message):console.info(message);
  const loadSdk=async()=>{
    if(sdk)return sdk;
    const appSdk=await import('https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js');
    const authSdk=await import('https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js');
    sdk={...appSdk,...authSdk};return sdk;
  };
  const config=async()=>fetch('/api/firebase-auth/config').then(response=>response.json());
  async function getAuthClient(){
    if(authClient)return authClient;
    const settings=await config();
    if(!settings.client_configured)throw new Error('Firebase Authentication is not configured yet.');
    const api=await loadSdk();
    const app=api.getApps().length?api.getApp():api.initializeApp(settings.firebase_config);
    authClient=api.getAuth(app);
    await api.setPersistence(authClient,api.browserLocalPersistence);
    return authClient;
  }
  async function syncSession(user){
    if(!user){localStorage.removeItem('glucoplate_firebase_session');renderPanel();return null}
    const token=await user.getIdToken();
    const response=await fetch('/api/firebase-auth/session',{headers:{Authorization:`Bearer ${token}`}});
    if(!response.ok)throw new Error((await response.json()).detail||'Could not verify Firebase session.');
    const session=await response.json();
    localStorage.setItem('glucoplate_firebase_session',JSON.stringify(session));
    localStorage.setItem('glucoplate_firebase_id_token',token);
    renderPanel();return session;
  }
  async function signInGoogle(){
    try{const api=await loadSdk(),client=await getAuthClient();await api.signInWithPopup(client,new api.GoogleAuthProvider());notify('Signed in with Google.')}catch(error){if(error?.code!=='auth/popup-closed-by-user')notify(error.message||'Google sign-in failed.')}
  }
  async function signInGuest(){
    try{const api=await loadSdk(),client=await getAuthClient();await api.signInAnonymously(client);notify('Continuing as guest.')}catch(error){notify(error.message||'Guest sign-in failed.')}
  }
  async function signOut(){
    try{const api=await loadSdk(),client=await getAuthClient();await api.signOut(client);localStorage.removeItem('glucoplate_firebase_id_token');notify('Signed out.')}catch(error){notify(error.message||'Sign-out failed.')}
  }
  function panelHtml(){
    const session=JSON.parse(localStorage.getItem('glucoplate_firebase_session')||'null'),user=session?.user;
    return `<div id="firebaseAuthPanel" style="margin-top:16px;padding:16px;border:1px solid #e7ded4;border-radius:18px;background:#fff"><strong style="display:block">Account</strong><span style="display:block;color:#756f69;font-size:.82rem;margin:5px 0 12px">${user?`Signed in as ${user.name||user.email||'Guest'}`:'Sign in to sync recipes and notifications across devices.'}</span><div style="display:flex;gap:8px;flex-wrap:wrap">${user?'<button id="firebaseSignOutBtn" class="btn ghost" type="button">Sign out</button>':'<button id="firebaseGoogleBtn" class="btn primary" type="button">Continue with Google</button><button id="firebaseGuestBtn" class="btn secondary" type="button">Continue as guest</button>'}</div></div>`;
  }
  function renderPanel(){
    document.getElementById('firebaseAuthPanel')?.remove();
    const profile=document.getElementById('profileView');const target=profile?.querySelector('.card')||document.querySelector('main')||document.body;
    target.insertAdjacentHTML('beforeend',panelHtml());
    document.getElementById('firebaseGoogleBtn')?.addEventListener('click',signInGoogle);
    document.getElementById('firebaseGuestBtn')?.addEventListener('click',signInGuest);
    document.getElementById('firebaseSignOutBtn')?.addEventListener('click',signOut);
  }
  window.addEventListener('DOMContentLoaded',async()=>{
    renderPanel();
    try{const api=await loadSdk(),client=await getAuthClient();api.onAuthStateChanged(client,user=>syncSession(user).catch(error=>notify(error.message)))}catch(error){console.info('Firebase Auth unavailable:',error.message)}
  });
  window.GlucoPlateFirebaseAuth={signInGoogle,signInGuest,signOut,syncSession,getAuthClient};
})();
