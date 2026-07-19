(()=>{
  let sdk=null,authClient=null,authEmulatorConnected=false,currentMode=location.pathname.endsWith('/register.html')?'register':'login';
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
    if(settings.auth_emulator_url&&!authEmulatorConnected){
      api.connectAuthEmulator(authClient,settings.auth_emulator_url,{disableWarnings:true});
      authEmulatorConnected=true;
    }
    await api.setPersistence(authClient,api.browserLocalPersistence);
    return authClient;
  }
  const authStyle=`
    #enterpriseAuthGate{position:fixed;inset:0;z-index:9999;display:grid;place-items:center;padding:22px;background:radial-gradient(circle at 15% 0%,#fff2e6,transparent 35%),#f7f4ef;font-family:Inter,ui-sans-serif,system-ui,sans-serif;color:#211f1d}
    #enterpriseAuthGate.hidden{display:none}.enterprise-auth-card{width:min(460px,100%);background:#fff;border:1px solid #e7ded4;border-radius:28px;padding:28px;box-shadow:0 24px 70px rgba(59,43,30,.16)}
    .enterprise-auth-brand{display:flex;gap:12px;align-items:center;margin-bottom:22px}.enterprise-auth-logo{width:52px;height:52px;border-radius:17px;display:grid;place-items:center;background:linear-gradient(135deg,#f26a2e,#ff9e3d);font-size:1.45rem}.enterprise-auth-brand strong,.enterprise-auth-brand span{display:block}.enterprise-auth-brand span{font-size:.78rem;color:#756f69;margin-top:3px}
    .enterprise-auth-tabs{display:grid;grid-template-columns:1fr 1fr;gap:6px;padding:5px;background:#f3ede6;border-radius:15px;margin-bottom:20px}.enterprise-auth-tab{border:0;border-radius:11px;padding:10px;background:transparent;font-weight:850}.enterprise-auth-tab.active{background:#fff;box-shadow:0 4px 14px rgba(59,43,30,.08)}
    .enterprise-auth-card h1{font-size:1.9rem;letter-spacing:-.04em;margin:0 0 6px}.enterprise-auth-copy{color:#756f69;font-size:.9rem;line-height:1.5;margin:0 0 18px}.enterprise-auth-field{display:grid;gap:7px;margin-top:13px}.enterprise-auth-field label{font-size:.78rem;font-weight:850}.enterprise-auth-field input{width:100%;border:1px solid #e7ded4;border-radius:15px;padding:13px 14px;outline:none}.enterprise-auth-field input:focus{border-color:#efa076;box-shadow:0 0 0 4px rgba(242,106,46,.10)}
    .enterprise-auth-submit,.enterprise-auth-google{width:100%;border:0;border-radius:16px;padding:14px;font-weight:900;margin-top:16px}.enterprise-auth-submit{background:linear-gradient(135deg,#f26a2e,#ff9e3d);color:#fff}.enterprise-auth-google{background:#fff;border:1px solid #e7ded4;color:#211f1d;margin-top:10px}.enterprise-auth-error{min-height:20px;color:#a92f24;font-size:.82rem;margin-top:12px}.enterprise-auth-note{font-size:.75rem;color:#756f69;margin-top:14px;line-height:1.45}
  `;
  function ensureGate(){
    if(!document.getElementById('enterpriseAuthStyles')){const style=document.createElement('style');style.id='enterpriseAuthStyles';style.textContent=authStyle;document.head.appendChild(style)}
    if(document.getElementById('enterpriseAuthGate'))return;
    document.body.insertAdjacentHTML('beforeend',`<div id="enterpriseAuthGate"><div class="enterprise-auth-card"><div class="enterprise-auth-brand"><div class="enterprise-auth-logo">🍽️</div><div><strong>GlucoPlate Enterprise</strong><span>Secure company access</span></div></div><div class="enterprise-auth-tabs"><button id="enterpriseLoginTab" class="enterprise-auth-tab" type="button">Sign in</button><button id="enterpriseRegisterTab" class="enterprise-auth-tab" type="button">Register</button></div><h1 id="enterpriseAuthTitle">Welcome back</h1><p id="enterpriseAuthCopy" class="enterprise-auth-copy">Continue with the Google account connected to GlucoPlate.</p><form id="enterpriseAuthForm"><div id="enterpriseAccessCodeField" class="enterprise-auth-field" style="display:none"><label for="enterpriseAccessCode">Organization access code</label><input id="enterpriseAccessCode" inputmode="numeric" autocomplete="one-time-code" /></div><button id="enterpriseGoogle" class="enterprise-auth-google" type="button"><span aria-hidden="true">G</span> Continue with Google</button><div id="enterpriseAuthError" class="enterprise-auth-error"></div><div id="enterpriseAuthNote" class="enterprise-auth-note">Returning members only need their Google account.</div></form></div></div>`);
    document.getElementById('enterpriseLoginTab').addEventListener('click',()=>setMode('login'));
    document.getElementById('enterpriseRegisterTab').addEventListener('click',()=>setMode('register'));
    document.getElementById('enterpriseAuthForm').addEventListener('submit',event=>event.preventDefault());
    document.getElementById('enterpriseGoogle').addEventListener('click',signInGoogle);
    setMode(currentMode);
  }
  function setMode(mode){
    currentMode=mode;const registering=mode==='register';
    document.getElementById('enterpriseLoginTab').classList.toggle('active',!registering);
    document.getElementById('enterpriseRegisterTab').classList.toggle('active',registering);
    const codeField=document.getElementById('enterpriseAccessCodeField'),codeInput=document.getElementById('enterpriseAccessCode');
    codeField.style.display=registering?'grid':'none';codeInput.required=registering;
    document.getElementById('enterpriseAuthTitle').textContent=registering?'Join your organization':'Welcome back';
    document.getElementById('enterpriseAuthCopy').textContent=registering?'Enter your organization access code once, then connect your Google account.':'Continue with the Google account connected to GlucoPlate.';
    document.getElementById('enterpriseGoogle').innerHTML=registering?'<span aria-hidden="true">G</span> Register with Google':'<span aria-hidden="true">G</span> Continue with Google';
    document.getElementById('enterpriseAuthNote').textContent=registering?'The access code is used only for initial organization enrollment.':'Returning members do not need an access code.';
    setError('');
  }
  const setError=message=>{const target=document.getElementById('enterpriseAuthError');if(target)target.textContent=message||''};
  const accessCode=()=>document.getElementById('enterpriseAccessCode')?.value.trim()||'';
  async function enroll(user,code){
    const token=await user.getIdToken();
    const response=await fetch('/api/firebase-auth/enterprise/enroll',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify({access_code:code})});
    if(!response.ok)throw new Error((await response.json()).detail||'Company enrollment failed.');
    await user.getIdToken(true);
    return syncSession(user);
  }
  async function getIdToken(forceRefresh=false){
    const client=await getAuthClient();
    const user=client.currentUser;
    if(!user)throw new Error('Sign in before using authenticated features.');
    const freshToken=await user.getIdToken(Boolean(forceRefresh));
    localStorage.setItem('glucoplate_firebase_id_token',freshToken);
    return freshToken;
  }
  async function syncSession(user){
    if(!user){localStorage.removeItem('glucoplate_firebase_session');localStorage.removeItem('glucoplate_firebase_id_token');showGate();renderPanel();return null}
    const token=await user.getIdToken();
    const response=await fetch('/api/firebase-auth/session',{headers:{Authorization:`Bearer ${token}`}});
    if(!response.ok)throw new Error((await response.json()).detail||'Could not verify Firebase session.');
    const session=await response.json();
    localStorage.setItem('glucoplate_firebase_session',JSON.stringify(session));
    localStorage.setItem('glucoplate_firebase_id_token',token);
    if(session.enterprise)hideGate();else showGate();
    window.dispatchEvent(new CustomEvent('glucoplate:auth-session-changed',{detail:{session}}));
    renderPanel();return session;
  }
  async function signInGoogle(){
    setError('');const registering=currentMode==='register',code=accessCode();
    if(registering&&!code)return setError('Enter your organization access code first.');
    const button=document.getElementById('enterpriseGoogle');button.disabled=true;
    try{
      const api=await loadSdk(),client=await getAuthClient();
      let user=registering?client.currentUser:null;
      if(!user){
        const provider=new api.GoogleAuthProvider();provider.setCustomParameters({prompt:'select_account'});
        user=(await api.signInWithPopup(client,provider)).user;
      }
      if(registering){
        await enroll(user,code);notify('Registration complete. Welcome to GlucoPlate.');
      }else{
        const session=await syncSession(user);
        if(!session?.enterprise){
          setMode('register');
          return setError('This Google account is not registered yet. Enter your organization access code to continue.');
        }
        notify('Signed in with Google.');
      }
    }catch(error){if(error?.code!=='auth/popup-closed-by-user')setError((error.message||'Google sign-in failed.').replace('Firebase: ',''));}
    finally{button.disabled=false}
  }
  async function signOut(){
    try{const api=await loadSdk(),client=await getAuthClient();await api.signOut(client);notify('Signed out.')}catch(error){notify(error.message||'Sign-out failed.');}
  }
  function showGate(){ensureGate();document.getElementById('enterpriseAuthGate').classList.remove('hidden')}
  function hideGate(){ensureGate();document.getElementById('enterpriseAuthGate').classList.add('hidden')}
  function panelHtml(){
    const session=JSON.parse(localStorage.getItem('glucoplate_firebase_session')||'null'),user=session?.user,enterprise=session?.enterprise;
    const adminRoles=new Set(['platform_admin','enterprise_owner','enterprise_admin','admin']);
    const adminLink=user&&enterprise&&adminRoles.has(enterprise.role)?'<a href="/static/admin.html" class="btn secondary" style="text-decoration:none">Admin dashboard</a>':'';
    return `<div id="firebaseAuthPanel" style="margin-top:16px;padding:16px;border:1px solid #e7ded4;border-radius:18px;background:#fff"><strong style="display:block">Enterprise account</strong><span style="display:block;color:#756f69;font-size:.82rem;margin:5px 0 12px">${user&&enterprise?`${user.name||user.email} · ${enterprise.company_name} · ${enterprise.role}`:'Sign in with your company access code.'}</span><div style="display:flex;gap:8px;flex-wrap:wrap">${user&&enterprise?`${adminLink}<button id="firebaseSignOutBtn" class="btn ghost" type="button">Sign out</button>`:'<button id="firebaseOpenLoginBtn" class="btn primary" type="button">Sign in</button>'}</div></div>`;
  }
  function renderPanel(){
    document.getElementById('firebaseAuthPanel')?.remove();
    const profile=document.getElementById('profileView');const target=profile||document.querySelector('main')||document.body;
    target.insertAdjacentHTML('beforeend',panelHtml());
    document.getElementById('firebaseSignOutBtn')?.addEventListener('click',signOut);
    document.getElementById('firebaseOpenLoginBtn')?.addEventListener('click',showGate);
  }
  function hasCachedEnterpriseSession(){
    try{return Boolean(JSON.parse(localStorage.getItem('glucoplate_firebase_session')||'null')?.enterprise)}catch{return false}
  }
  window.addEventListener('DOMContentLoaded',async()=>{
    ensureGate();
    if(hasCachedEnterpriseSession())hideGate();else showGate();
    renderPanel();
    try{const api=await loadSdk(),client=await getAuthClient();api.onAuthStateChanged(client,user=>syncSession(user).catch(error=>{setError(error.message);showGate()}))}catch(error){setError(error.message);console.info('Firebase Auth unavailable:',error.message)}
  });
  window.GlucoPlateFirebaseAuth={signInGoogle,signOut,syncSession,getAuthClient,getIdToken,showGate,renderPanel};
})();