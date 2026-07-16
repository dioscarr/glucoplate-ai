(()=>{
  const nativeFetch=window.fetch.bind(window);
  const ACTIVE_PROFILE_KEY='glucoplate_active_profile_id';
  const routeMap=new Map([
    ['/api/recipes/save','/api/user-data/recipes'],
    ['/api/recipes/list','/api/user-data/recipes'],
    ['/api/recipes/recents','/api/user-data/recents']
  ]);

  const activeProfileId=()=>localStorage.getItem(ACTIVE_PROFILE_KEY)||'default';
  function setActiveProfile(profile){
    const id=typeof profile==='string'?profile:profile?.id;
    if(!id)throw new Error('A profile id is required.');
    localStorage.setItem(ACTIVE_PROFILE_KEY,id);
    localStorage.setItem('glucoplate_active_profile',JSON.stringify(typeof profile==='string'?{id}:profile));
    window.dispatchEvent(new CustomEvent('glucoplate:profilechange',{detail:{profile_id:id}}));
    return id;
  }

  function normalizeRequest(input,init={}){
    const rawUrl=typeof input==='string'?input:input.url;
    const url=new URL(rawUrl,window.location.origin);
    const mapped=routeMap.get(url.pathname);
    if(!mapped)return {input,init};

    const headers=new Headers(init.headers||(typeof input!=='string'?input.headers:undefined));
    const token=localStorage.getItem('glucoplate_firebase_id_token');
    if(token)headers.set('Authorization',`Bearer ${token}`);

    let body=init.body;
    if(body&&['/api/recipes/save','/api/recipes/recents'].includes(url.pathname)){
      try{body=JSON.stringify({recipe:JSON.parse(body)})}catch(_error){}
      headers.set('Content-Type','application/json');
    }
    url.pathname=mapped;
    return {input:url.toString(),init:{...init,headers,body}};
  }

  window.fetch=(input,init={})=>{
    const normalized=normalizeRequest(input,init);
    return nativeFetch(normalized.input,normalized.init);
  };

  async function authenticatedRequest(path,options={}){
    const token=localStorage.getItem('glucoplate_firebase_id_token');
    if(!token)throw new Error('Sign in is required.');
    const headers=new Headers(options.headers||{});
    headers.set('Authorization',`Bearer ${token}`);
    if(options.body&&!headers.has('Content-Type'))headers.set('Content-Type','application/json');
    const response=await nativeFetch(path,{...options,headers});
    if(!response.ok){
      let message='Request failed.';
      try{message=(await response.json()).detail||message}catch(_error){}
      throw new Error(message);
    }
    return response.status===204?null:response.json();
  }

  const profileQuery=path=>`${path}${path.includes('?')?'&':'?'}profile_id=${encodeURIComponent(activeProfileId())}`;

  window.GlucoPlateUserData={
    activeProfileId,
    setActiveProfile,
    listProfiles:()=>authenticatedRequest('/api/user-data/profiles'),
    createProfile:profile=>authenticatedRequest('/api/user-data/profiles',{method:'POST',body:JSON.stringify(profile)}),
    deleteProfile:profileId=>authenticatedRequest(`/api/user-data/profiles/${encodeURIComponent(profileId)}`,{method:'DELETE'}),
    listSavedRecipes:()=>authenticatedRequest('/api/user-data/recipes'),
    deleteSavedRecipe:recipeId=>authenticatedRequest(`/api/user-data/recipes/${encodeURIComponent(recipeId)}`,{method:'DELETE'}),
    recordCooked:payload=>authenticatedRequest('/api/user-data/cooking-history',{method:'POST',body:JSON.stringify({...payload,profile_id:activeProfileId()})}),
    listCookingHistory:(limit=50)=>authenticatedRequest(profileQuery(`/api/user-data/cooking-history?limit=${limit}`)),
    getPreferences:()=>authenticatedRequest(profileQuery('/api/user-data/preferences')),
    savePreferences:preferences=>authenticatedRequest('/api/user-data/preferences',{method:'PUT',body:JSON.stringify({preferences,profile_id:activeProfileId()})})
  };
})();
