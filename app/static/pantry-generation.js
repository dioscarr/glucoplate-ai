(()=>{
  if(window.GlucoPlatePantryGeneration)return;

  const originalFetch=window.fetch.bind(window);
  const profileId=()=>window.GlucoPlateUserData?.activeProfileId?.()||localStorage.getItem('glucoplate_active_profile_id')||'default';
  const token=()=>localStorage.getItem('glucoplate_firebase_id_token');
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  let pantryCache=null;
  let pantryCacheProfile=null;

  async function loadPantry(){
    if(!token())return {items:[]};
    const currentProfile=profileId();
    if(pantryCache&&pantryCacheProfile===currentProfile)return pantryCache;
    const response=await originalFetch(`/api/pantry/items?profile_id=${encodeURIComponent(currentProfile)}`,{
      headers:{'Authorization':`Bearer ${token()}`}
    });
    if(!response.ok)throw new Error('Pantry unavailable');
    pantryCache=await response.json();
    pantryCacheProfile=currentProfile;
    return pantryCache;
  }

  function pantryContext(result){
    const items=Array.isArray(result?.items)?result.items:[];
    const usable=items.filter(item=>item.expiration_status!=='expired');
    return {
      pantry_items:usable.map(item=>item.name).filter(Boolean),
      use_soon_ingredients:usable.filter(item=>item.expiration_status==='use_soon').map(item=>item.name).filter(Boolean)
    };
  }

  function renderCoverage(recipe){
    const coverage=recipe?.pantry_coverage;
    if(!coverage)return;
    document.getElementById('pantryCoverageCard')?.remove();
    const card=document.createElement('section');
    card.id='pantryCoverageCard';
    card.className='card';
    card.style.margin='16px 0';
    const have=Array.isArray(recipe.already_have)?recipe.already_have:[];
    const buy=Array.isArray(recipe.need_to_buy)?recipe.need_to_buy:[];
    const soon=Array.isArray(recipe.use_soon_matches)?recipe.use_soon_matches:[];
    const chips=items=>items.map(item=>`<span class="chip">${esc(item)}</span>`).join(' ');
    card.innerHTML=`<div style="padding:16px"><span class="eyebrow">Pantry coverage</span><h3 style="margin:6px 0">You already have ${Number(coverage.available_count||0)} of ${Number(coverage.required_count||0)} ingredients</h3><p style="margin:0 0 12px;color:var(--muted,#756f69)">${Number(coverage.coverage_percent||0)}% covered${soon.length?` · Uses ${soon.length} item${soon.length===1?'':'s'} soon`:''}</p><div style="display:grid;gap:10px"><div><strong>Already have</strong><div>${have.length?chips(have):'None matched'}</div></div><div><strong>Need to buy</strong><div id="pantryShoppingGap">${buy.length?chips(buy):'Nothing — your pantry covers this recipe.'}</div></div></div></div>`;
    const target=document.getElementById('result')||document.getElementById('recipeResult')||document.querySelector('main');
    target?.prepend(card);
  }

  window.fetch=async(input,init={})=>{
    const url=typeof input==='string'?input:input?.url||'';
    if(!url.includes('/api/recipes/generate'))return originalFetch(input,init);
    let nextInit={...init};
    try{
      const pantry=pantryContext(await loadPantry());
      const body=typeof init.body==='string'?JSON.parse(init.body):{};
      nextInit={...init,body:JSON.stringify({...body,...pantry})};
    }catch(error){
      console.debug('Pantry context unavailable; generating normally.',error);
    }
    const response=await originalFetch(input,nextInit);
    try{renderCoverage(await response.clone().json())}catch(error){console.debug('Pantry coverage unavailable.',error)}
    return response;
  };

  window.addEventListener('glucoplate:pantry-changed',()=>{pantryCache=null;pantryCacheProfile=null});
  window.GlucoPlatePantryGeneration={loadPantry,pantryContext,renderCoverage};
})();
