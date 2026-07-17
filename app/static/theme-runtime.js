(()=>{
  const map={background:'--bg',surface:'--surface',surfaceAlt:'--surface2',text:'--text',muted:'--muted',border:'--line',primary:'--brand',secondary:'--brand2',accent:'--green',dark:'--dark'};
  const selectors={'recipes.hero':'.hero,.recipe-hero','navigation.top':'.app-header,.bottom-nav','recipes.gallery':'.dish-grid,.saved-list','cook.mode':'.cook-step','button.primary':'.btn.primary,.primary','button.secondary':'.btn.secondary,.secondary','input.default':'input,select,textarea','card.recipe':'.dish-card,.recipe-card,.saved-item','card.panel':'.card,.section','text.heroTitle':'.hero h1,.recipe-hero h1','text.eyebrow':'.eyebrow','content.brandName':'.brand strong'};
  const enterprise=()=>{try{return JSON.parse(localStorage.getItem('glucoplate_firebase_session')||'null')?.enterprise?.company_id||'glucoplate'}catch{return'glucoplate'}};
  const storageKey=id=>`glucoplate_theme_${id}`;
  let bundle=null;

  function clearPreviousOverrides(){
    document.querySelectorAll('[data-company-theme-style]').forEach(node=>{
      node.removeAttribute('style');
      node.removeAttribute('data-company-theme-style');
    });
  }

  function styleNode(node,p={}){
    node.dataset.companyThemeStyle='1';
    if(p.background)node.style.background=p.background;
    if(p.textColor)node.style.color=p.textColor;
    if(p.color)node.style.color=p.color;
    if(p.borderColor)node.style.borderColor=p.borderColor;
    if(p.borderRadius!==undefined)node.style.borderRadius=`${p.borderRadius}px`;
    if(p.padding!==undefined)node.style.padding=`${p.padding}px`;
    if(p.paddingTop!==undefined)node.style.paddingTop=`${p.paddingTop}px`;
    if(p.paddingBottom!==undefined)node.style.paddingBottom=`${p.paddingBottom}px`;
    if(p.paddingX!==undefined){node.style.paddingLeft=`${p.paddingX}px`;node.style.paddingRight=`${p.paddingX}px`}
    if(p.paddingY!==undefined){node.style.paddingTop=`${p.paddingY}px`;node.style.paddingBottom=`${p.paddingY}px`}
    if(p.fontSize!==undefined)node.style.fontSize=`${p.fontSize}px`;
    if(p.fontWeight!==undefined)node.style.fontWeight=p.fontWeight;
    if(p.text!==undefined)node.textContent=p.text;
  }

  function applyOverrides(theme){
    clearPreviousOverrides();
    ['sections','components','elements'].forEach(group=>Object.entries(theme?.[group]||{}).forEach(([key,props])=>document.querySelectorAll(selectors[key]||'').forEach(node=>styleNode(node,props))));
  }

  function apply(theme){
    if(!theme)return;
    const root=document.documentElement,t=theme.tokens||{};
    Object.entries(t.colors||{}).forEach(([k,v])=>map[k]&&root.style.setProperty(map[k],v));
    if(t.typography){
      root.style.setProperty('--theme-font',t.typography.fontFamily||'inherit');
      root.style.setProperty('--theme-base-size',`${t.typography.baseSize||16}px`);
      document.body.style.fontFamily='var(--theme-font)';
      document.body.style.fontSize='var(--theme-base-size)';
    }
    if(t.shape){root.style.setProperty('--radius',`${t.shape.radius||26}px`);root.style.setProperty('--theme-control-radius',`${t.shape.controlRadius||17}px`)}
    if(t.effects){root.style.setProperty('--shadow',t.effects.shadow||'none');root.style.setProperty('--soft',t.effects.softShadow||'none')}
    applyOverrides(theme);
    document.documentElement.dataset.companyTheme=theme.id||'default';
  }

  function selectedTheme(){
    const company=enterprise();
    const stored=localStorage.getItem(storageKey(company));
    return bundle?.themes?.find(theme=>theme.id===stored)||bundle?.themes?.find(theme=>theme.id===bundle.activeThemeId)||bundle?.themes?.[0];
  }

  function switchTheme(themeId){
    const theme=bundle?.themes?.find(item=>item.id===themeId);
    if(!theme)return;
    localStorage.setItem(storageKey(enterprise()),themeId);
    apply(theme);
    const select=document.getElementById('companyThemeSwitcher');
    if(select&&select.value!==themeId)select.value=themeId;
    window.dispatchEvent(new CustomEvent('glucoplate:theme-changed',{detail:{theme}}));
  }

  function mountSwitcher(){
    document.getElementById('companyThemeSwitcherWrap')?.remove();
    if(!bundle?.themes||bundle.themes.length<2)return;
    const target=document.querySelector('.app-header .header-actions,.app-header nav,.app-header,.bottom-nav');
    if(!target)return;
    const wrap=document.createElement('label');
    wrap.id='companyThemeSwitcherWrap';
    wrap.style.cssText='display:flex;align-items:center;gap:6px;font-size:.72rem;font-weight:800;white-space:nowrap';
    wrap.innerHTML=`<span>Theme</span><select id="companyThemeSwitcher" aria-label="Company theme" style="width:auto;min-width:110px;padding:7px 9px;border:1px solid var(--line,#ddd);border-radius:10px;background:var(--surface,#fff);color:var(--text,#222)">${bundle.themes.map(theme=>`<option value="${theme.id}">${theme.name||theme.id}</option>`).join('')}</select>`;
    target.appendChild(wrap);
    const select=wrap.querySelector('select');
    select.value=selectedTheme()?.id||bundle.activeThemeId;
    select.addEventListener('change',()=>switchTheme(select.value));
  }

  async function load(){
    try{
      const company=enterprise();
      const response=await fetch(`/api/enterprise/themes/${encodeURIComponent(company)}`);
      if(!response.ok)return;
      bundle=await response.json();
      const theme=selectedTheme();
      if(theme)apply(theme);
      mountSwitcher();
    }catch(error){console.info('Company theme unavailable:',error?.message||error)}
  }

  window.GlucoPlateTheme={apply,load,switchTheme,get themes(){return bundle?.themes||[]}};
  document.addEventListener('DOMContentLoaded',load);
  window.addEventListener('glucoplate:auth-session-changed',load);
})();
