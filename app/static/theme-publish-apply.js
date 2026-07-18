(()=>{
  const previousFetch=window.fetch.bind(window);
  const session=()=>{try{return JSON.parse(localStorage.getItem('glucoplate_firebase_session')||'null')}catch{return null}};
  const companyId=()=>session()?.enterprise?.company_id||session()?.enterprise?.enterprise_id||'glucoplate';
  const storageKey=()=>`glucoplate_theme_${companyId()}`;

  function requestInfo(input,init={}){
    const raw=typeof input==='string'?input:input?.url;
    if(!raw)return null;
    const url=new URL(raw,window.location.origin);
    return {url,method:(init.method||'GET').toUpperCase()};
  }

  window.fetch=async(input,init={})=>{
    const info=requestInfo(input,init);
    const response=await previousFetch(input,init);
    const isPublishedThemeSave=
      response.ok&&
      info?.method==='PUT'&&
      /^\/api\/enterprise\/admin\/themes\/[^/]+$/.test(info.url.pathname)&&
      info.url.searchParams.get('publish')==='true';

    if(!isPublishedThemeSave)return response;

    try{
      const payload=await response.clone().json();
      const themeId=payload?.theme?.id;
      if(!themeId)return response;
      const activation=await previousFetch(`/api/enterprise/admin/themes/${encodeURIComponent(themeId)}/activate`,{
        method:'POST',
        headers:init.headers||{},
      });
      if(!activation.ok){
        const body=await activation.json().catch(()=>({}));
        throw new Error(body.detail||'Theme published, but could not be made the company default.');
      }
      localStorage.setItem(storageKey(),themeId);
      sessionStorage.setItem('glucoplate_theme_studio_selected',themeId);
      window.dispatchEvent(new CustomEvent('glucoplate:theme-published-and-applied',{detail:{themeId}}));
      setTimeout(()=>{
        const status=document.getElementById('themeStatus');
        if(status)status.textContent=`Version ${payload.theme.version} · published · company default`;
      },0);
    }catch(error){
      setTimeout(()=>{
        const status=document.getElementById('themeStatus');
        if(status)status.textContent=error?.message||'Theme published, but could not be applied.';
      },0);
    }
    return response;
  };

  window.addEventListener('DOMContentLoaded',()=>{
    const button=document.getElementById('publishTheme');
    if(button){
      button.textContent='Publish & apply';
      button.setAttribute('aria-label','Publish this theme and make it the company default');
    }
  });
})();
