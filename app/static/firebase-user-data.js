(()=>{
  const nativeFetch=window.fetch.bind(window);
  const routeMap=new Map([
    ['/api/recipes/save','/api/user-data/recipes'],
    ['/api/recipes/list','/api/user-data/recipes'],
    ['/api/recipes/recents','/api/user-data/recents']
  ]);

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

  window.GlucoPlateUserData={
    listSavedRecipes:()=>authenticatedRequest('/api/user-data/recipes'),
    deleteSavedRecipe:recipeId=>authenticatedRequest(`/api/user-data/recipes/${encodeURIComponent(recipeId)}`,{method:'DELETE'}),
    recordCooked:payload=>authenticatedRequest('/api/user-data/cooking-history',{method:'POST',body:JSON.stringify(payload)}),
    listCookingHistory:(limit=50)=>authenticatedRequest(`/api/user-data/cooking-history?limit=${limit}`),
    getPreferences:()=>authenticatedRequest('/api/user-data/preferences'),
    savePreferences:preferences=>authenticatedRequest('/api/user-data/preferences',{method:'PUT',body:JSON.stringify({preferences})})
  };
})();
