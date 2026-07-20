(()=>{
  window.can=permission=>Boolean(window.__glucoplateAuthorization?.permissions?.includes(permission));
  window.loadAuthorization=async()=>{
    const profile=await window.api('/api/enterprise/authorization/profile');
    profile.permissions=Array.isArray(profile.permissions)?profile.permissions:[];
    profile.visibility=Array.isArray(profile.visibility)?profile.visibility:[];
    window.__glucoplateAuthorization=profile;
    window.GlucoPlateAuthorization={profile:()=>({...profile}),can:window.can};
    return profile;
  };
})();
