(()=>{
  const token=()=>localStorage.getItem('glucoplate_firebase_id_token')||'';
  const key='glucoplate_theme_studio_selected';
  const originalFetch=window.fetch.bind(window);
  let selectedId=sessionStorage.getItem(key)||'';
  let bundle=null;

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

  function ensureStyles(){
    if(document.getElementById('themeLibraryStyles'))return;
    const style=document.createElement('style');
    style.id='themeLibraryStyles';
    style.textContent=`
      .theme-library{width:min(1180px,calc(100% - 28px));margin:16px auto 0;padding:18px;background:#fff;border:1px solid var(--line);border-radius:22px;box-shadow:var(--shadow)}.theme-library-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}.theme-library h2{margin:0;font-size:1.15rem}.theme-library p{margin:4px 0 0;color:var(--muted);font-size:.8rem}.theme-create{display:grid;grid-template-columns:minmax(180px,1fr) auto;gap:8px}.theme-create input{margin:0}.theme-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:15px}.theme-card{position:relative;text-align:left;border:1px solid var(--line);border-radius:18px;padding:14px;background:#fff;color:var(--text);min-height:132px;cursor:pointer}.theme-card:hover{box-shadow:var(--soft);transform:translateY(-1px)}.theme-card.selected{border-color:var(--brand);box-shadow:0 0 0 3px rgba(242,106,46,.10);background:linear-gradient(145deg,#fff,#fff5ec)}.theme-card strong,.theme-card small{display:block}.theme-card small{color:var(--muted);margin-top:4px;line-height:1.4}.theme-swatches{display:flex;gap:6px;margin-top:14px}.theme-swatch{width:26px;height:26px;border-radius:9px;border:1px solid rgba(0,0,0,.08)}.theme-tags{display:flex;flex-wrap:wrap;gap:5px;margin-top:10px}.theme-tag{padding:5px 7px;border-radius:999px;background:#f4efe9;color:#6f6259;font-size:.65rem;font-weight:850}.theme-tag.active{background:#e8f4ee;color:#245d46}.theme-tag.enabled{background:#fff0e5;color:#a54520}.theme-library-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}.theme-library-actions button{padding:9px 12px}.theme-empty{padding:22px;text-align:center;color:var(--muted);border:1px dashed var(--line);border-radius:16px}.theme-help{margin-top:12px;padding:11px 13px;border-radius:14px;background:#eef5ff;color:#315b8b;font-size:.76rem;line-height:1.45}@media(max-width:850px){.theme-cards{grid-template-columns:1fr 1fr}.theme-library-head{flex-direction:column}.theme-create{width:100%}}@media(max-width:560px){.theme-cards{grid-template-columns:1fr}.theme-create{grid-template-columns:1fr}.theme-library-actions{display:grid;grid-template-columns:1fr 1fr}.theme-library-actions button:last-child{grid-column:1/-1}}
    `;
    document.head.appendChild(style);
  }

  function color(theme,key,fallback){return theme?.tokens?.colors?.[key]||fallback}
  function renderLibrary(){
    const host=document.getElementById('themeManager');
    if(!host||!bundle)return;
    ensureStyles();
    if(!selectedId||!bundle.themes.some(theme=>theme.id===selectedId))selectedId=bundle.activeThemeId||bundle.themes[0]?.id||'default';
    sessionStorage.setItem(key,selectedId);
    const selected=bundle.themes.find(theme=>theme.id===selectedId);
    host.className='theme-library';
    host.innerHTML=`<div class="theme-library-head"><div><h2>Theme library</h2><p>Create several looks for this company, keep multiple themes enabled, and choose one default.</p></div><form id="createThemeForm" class="theme-create"><input id="newThemeName" placeholder="New theme name" maxlength="80" required><button class="primary" type="submit">Create theme</button></form></div><div class="theme-cards">${bundle.themes.length?bundle.themes.map(theme=>`<button type="button" class="theme-card ${theme.id===selectedId?'selected':''}" data-theme-id="${theme.id}"><strong>${theme.name}</strong><small>Version ${theme.version||1} · ${theme.status||'draft'}</small><div class="theme-swatches"><span class="theme-swatch" style="background:${color(theme,'primary','#f26a2e')}"></span><span class="theme-swatch" style="background:${color(theme,'secondary','#ff9e3d')}"></span><span class="theme-swatch" style="background:${color(theme,'background','#f7f4ef')}"></span><span class="theme-swatch" style="background:${color(theme,'dark','#171412')}"></span></div><div class="theme-tags">${theme.id===bundle.activeThemeId?'<span class="theme-tag active">Company default</span>':''}${theme.enabled?'<span class="theme-tag enabled">Available in app</span>':'<span class="theme-tag">Disabled</span>'}</div></button>`).join(''):'<div class="theme-empty">No themes have been created yet.</div>'}</div><div class="theme-library-actions"><button id="editSelectedTheme" class="primary" type="button">Edit selected</button><button id="duplicateTheme" type="button">Duplicate</button><button id="activateTheme" type="button">Make company default</button></div><div class="theme-help"><strong>${selected?.name||'Selected theme'}</strong> is loaded in the editor below. Publishing makes it available to users; “Make company default” controls the fallback theme.</div>`;
    host.querySelectorAll('[data-theme-id]').forEach(card=>card.onclick=()=>{selectedId=card.dataset.themeId;sessionStorage.setItem(key,selectedId);location.reload()});
    host.querySelector('#createThemeForm').onsubmit=async event=>{
      event.preventDefault();
      const input=host.querySelector('#newThemeName');
      const name=input.value.trim();
      if(!name)return;
      const button=event.currentTarget.querySelector('button');button.disabled=true;button.textContent='Creating…';
      try{const result=await api('/api/enterprise/admin/themes',{method:'POST',body:JSON.stringify({name,source_theme_id:selectedId||null})});selectedId=result.theme.id;sessionStorage.setItem(key,selectedId);location.reload()}
      catch(error){button.disabled=false;button.textContent='Create theme';document.getElementById('themeStatus').textContent=error.message}
    };
    host.querySelector('#editSelectedTheme').onclick=()=>document.querySelector('.steps')?.scrollIntoView({behavior:'smooth',block:'start'});
    host.querySelector('#duplicateTheme').onclick=async()=>{
      const source=bundle.themes.find(theme=>theme.id===selectedId);
      const name=prompt('Name the duplicated theme',`${source?.name||'Theme'} copy`);
      if(!name?.trim())return;
      try{const result=await api('/api/enterprise/admin/themes',{method:'POST',body:JSON.stringify({name:name.trim(),source_theme_id:selectedId})});selectedId=result.theme.id;sessionStorage.setItem(key,selectedId);location.reload()}
      catch(error){document.getElementById('themeStatus').textContent=error.message}
    };
    host.querySelector('#activateTheme').onclick=async()=>{
      try{await api(`/api/enterprise/admin/themes/${encodeURIComponent(selectedId)}/activate`,{method:'POST'});localStorage.setItem(`glucoplate_theme_${JSON.parse(localStorage.getItem('glucoplate_firebase_session')||'null')?.enterprise?.company_id||'glucoplate'}`,selectedId);location.reload()}
      catch(error){document.getElementById('themeStatus').textContent=error.message}
    };
  }

  window.addEventListener('DOMContentLoaded',async()=>{
    try{bundle=await api('/api/enterprise/admin/themes');renderLibrary()}
    catch(error){const status=document.getElementById('themeStatus');if(status)status.textContent=error.message}
  });
})();