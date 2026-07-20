(()=>{
  window.can=permission=>Boolean(window.__glucoplateAuthorization?.permissions?.includes(permission));
  window.loadAuthorization=async()=>{
    const token=localStorage.getItem('glucoplate_firebase_id_token')||'';
    if(!token)throw new Error('Your session is not ready. Sign in again.');
    const response=await fetch('/api/enterprise/authorization/profile',{headers:{Authorization:`Bearer ${token}`}});
    const profile=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(profile.detail||'Authorization profile could not be loaded.');
    profile.permissions=Array.isArray(profile.permissions)?profile.permissions:[];
    profile.visibility=Array.isArray(profile.visibility)?profile.visibility:[];
    window.__glucoplateAuthorization=profile;
    window.GlucoPlateAuthorization={profile:()=>({...profile}),can:window.can};
    return profile;
  };
})();
