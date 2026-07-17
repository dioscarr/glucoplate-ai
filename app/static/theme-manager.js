(()=>{
  const token=()=>localStorage.getItem('glucoplate_firebase_id_token')||'';
  const key='glucoplate_theme_studio_selected';
  const originalFetch=window.fetch.bind(window);
  let selectedId=sessionStorage.getItem(key)||'';

  function authHeaders(extra={}){return {'Content-Type':'application/json',Authorization:`Bearer ${token()}`,...extra}}
  async function api(path,options={}){
    const response=await originalFetch(path,{...options,headers:authHeaders(options.headers||{})});
    const body=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(body.detail||'Request failed');
    return body;
  }

  function rewriteThemeRequest(input,init={}){
    const raw=typeof input==='string'?input:input?.url;
    if(!raw||!selectedId)return [input,init];
    const url=new URL(raw,window.location.origin);
    if(url.pathname!=='/api/enterprise/admin/theme')return [input,init];
    const method=(init.method||'GET').toUpperCase();
    if(method==='DELETE'){
      url.searchParams.set('theme_id',selectedId);
      return [url.pathname+url.search,init];
    }
    url.pathname=`/api/enterprise/admin/themes/${encodeURIComponent(selectedId)}`;
    return [url.pathname+url.search,init];
  }

  window.fetch=(input,init={})=>{
    const [nextInput,nextInit]=rewriteThemeRequest(input,init);
    return originalFetch(nextInput,nextInit);
  };

  function renderManager(bundle){
    const host=document.getElementById('themeManager');
    if(!host)return;
    if(!selectedId||!bundle.themes.some(theme=>theme.id===selectedId))selectedId=bundle.activeThemeId||bundle.themes[0]?.id||'default';
    sessionStorage.setItem(key,selectedId);
    host.innerHTML=`<label style="margin:0;min-width:170px">Theme<select id="studioThemeSelect" style="margin-top:4px">${bundle.themes.map(theme=>`<option value="${theme.id}">${theme.name}${theme.id===bundle.activeThemeId?' · active':''}${theme.enabled?' · enabled':''}</option>`).join('')}</select></label><button id="newTheme" class="ghost" type="button">New theme</button><button id="activateTheme" type="button">Make active</button>`;
    const select=document.getElementById('studioThemeSelect');
    select.value=selectedId;
    select.onchange=()=>{selectedId=select.value;sessionStorage.setItem(key,selectedId);location.reload()};
    document.getElementById('newTheme').onclick=async()=>{
      const name=prompt('Name this theme');
      if(!name?.trim())return;
      try{
        const result=await api('/api/enterprise/admin/themes',{method:'POST',body:JSON.stringify({name:name.trim(),source_theme_id:selectedId})});
        selectedId=result.theme.id;sessionStorage.setItem(key,selectedId);location.reload();
      }catch(error){document.getElementById('themeStatus').textContent=error.message}
    };
    document.getElementById('activateTheme').onclick=async()=>{
      try{
        await api(`/api/enterprise/admin/themes/${encodeURIComponent(selectedId)}/activate`,{method:'POST'});
        localStorage.setItem(`glucoplate_theme_${JSON.parse(localStorage.getItem('glucoplate_firebase_session')||'null')?.enterprise?.company_id||'glucoplate'}`,selectedId);
        location.reload();
      }catch(error){document.getElementById('themeStatus').textContent=error.message}
    };
  }

  window.addEventListener('DOMContentLoaded',async()=>{
    try{renderManager(await api('/api/enterprise/admin/themes'))}
    catch(error){const status=document.getElementById('themeStatus');if(status)status.textContent=error.message}
  });
})();
