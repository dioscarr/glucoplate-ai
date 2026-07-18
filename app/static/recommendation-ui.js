(()=>{
  if(window.GlucoPlateRecommendationUi)return;

  const originalGenerate=window.generateRecipe;
  if(typeof originalGenerate!=='function')return;

  let pending=null;
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const activeProfileId=()=>window.GlucoPlateUserData?.activeProfileId?.()||localStorage.getItem('glucoplate_active_profile_id')||'default';
  async function authToken(forceRefresh=false){
    const provider=window.GlucoPlateFirebaseAuth?.getIdToken;
    if(typeof provider==='function')return provider(Boolean(forceRefresh));
    const token=localStorage.getItem('glucoplate_firebase_id_token');
    if(!token)throw new Error('Sign in is required for personalized suggestions.');
    return token;
  }
  async function authenticatedFetch(path,options={}){
    const request=async forceRefresh=>fetch(path,{...options,headers:{'Content-Type':'application/json',...(options.headers||{}),Authorization:`Bearer ${await authToken(forceRefresh)}`}});
    let response=await request(false);
    if(response.status===401&&typeof window.GlucoPlateFirebaseAuth?.getIdToken==='function')response=await request(true);
    return response;
  }

  async function recordFeedback(sessionId,eventType,conceptId=null,metadata={},profileId=activeProfileId()){
    if(!sessionId||!localStorage.getItem('glucoplate_firebase_id_token'))return;
    try{
      const response=await authenticatedFetch('/api/recommendations/events',{
        method:'POST',
        body:JSON.stringify({
          session_id:sessionId,
          event_type:eventType,
          concept_id:conceptId,
          profile_id:profileId,
          metadata
        })
      });
      if(!response.ok)throw new Error(`Recommendation feedback failed with ${response.status}`);
    }catch(error){
      console.debug('Recommendation feedback was not recorded.',error);
    }
  }

  function ensureStyles(){
    if(document.getElementById('recommendationUiStyles'))return;
    const style=document.createElement('style');
    style.id='recommendationUiStyles';
    style.textContent=`
      .concept-overlay{position:fixed;inset:0;z-index:88;display:grid;place-items:center;padding:18px;background:rgba(33,31,29,.58);backdrop-filter:blur(16px)}
      .concept-dialog{width:min(760px,100%);max-height:min(760px,92dvh);overflow:auto;padding:22px;background:var(--bg,#f7f4ef)}
      .concept-dialog-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}.concept-dialog h2{margin:5px 0 4px;font-size:1.7rem;letter-spacing:-.04em}.concept-dialog-head p{margin:0;color:var(--muted,#756f69);line-height:1.45}.concept-close{border:1px solid var(--line,#e7ded4);background:#fff;width:40px;height:40px;border-radius:14px;font-weight:900}
      .concept-list{display:grid;gap:11px;margin-top:18px}.concept-card{width:100%;display:grid;grid-template-columns:44px 1fr auto;gap:12px;align-items:start;text-align:left;padding:16px;border:1px solid var(--line,#e7ded4);border-radius:20px;background:#fff;color:var(--text,#211f1d);box-shadow:var(--soft,0 10px 28px rgba(59,43,30,.08));transition:.16s}.concept-card:hover{transform:translateY(-2px);border-color:#efa076}.concept-rank{width:44px;height:44px;border-radius:15px;display:grid;place-items:center;background:#fff0e5;color:#a54520;font-weight:950}.concept-card strong{display:block;font-size:1.02rem}.concept-direction{display:block;margin-top:5px;color:var(--muted,#756f69);font-size:.82rem;line-height:1.45}.concept-reason{display:block;margin-top:9px;color:#245d46;font-size:.76rem;font-weight:800}.concept-score{font-size:.7rem;font-weight:900;color:#a54520;background:#fff0e5;border-radius:999px;padding:6px 8px}.concept-actions{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-top:16px}.concept-note{color:var(--muted,#756f69);font-size:.75rem}
      @media(max-width:560px){.concept-dialog{padding:18px}.concept-card{grid-template-columns:38px 1fr}.concept-rank{width:38px;height:38px}.concept-score{grid-column:2;justify-self:start}.concept-actions{align-items:stretch;flex-direction:column}.concept-actions .btn{width:100%}}
    `;
    document.head.appendChild(style);
  }

  function closeDialog(){
    document.getElementById('recipeConceptOverlay')?.remove();
    pending=null;
  }
  function dismissConcepts(reason='closed'){
    const value=pending;
    closeDialog();
    if(value?.sessionId)void recordFeedback(value.sessionId,'skipped',null,{reason},value.profileId);
  }

  function renderConcepts(result,context){
    ensureStyles();
    closeDialog();
    pending={...context,sessionId:result?.session_id||null,profileId:result?.profile_id||activeProfileId()};
    const concepts=Array.isArray(result?.concepts)?result.concepts:[];
    if(!concepts.length)throw new Error('No recipe directions were returned.');
    const overlay=document.createElement('div');
    overlay.id='recipeConceptOverlay';
    overlay.className='concept-overlay';
    overlay.setAttribute('role','dialog');
    overlay.setAttribute('aria-modal','true');
    overlay.setAttribute('aria-labelledby','recipeConceptTitle');
    const reasonList=concept=>Array.isArray(concept.why_this_fits)?concept.why_this_fits:[concept.why_this_fits||'A practical match for your request.'];
    overlay.innerHTML=`<div class="card concept-dialog"><div class="concept-dialog-head"><div><span class="eyebrow">Chosen for this profile</span><h2 id="recipeConceptTitle">Pick tonight’s direction</h2><p>These are ranked suggestions—not guarantees. GlucoPlate uses this profile’s cooking choices and available pantry context, then generates the full recipe after you choose.</p><div class="concept-context"><span>${Number(result.interaction_count||0)} Flavor Memory signals</span><span>${Number(result.pantry_count||0)} pantry items considered</span>${Number(result.use_soon_count||0)?`<span>${Number(result.use_soon_count)} use-soon matches</span>`:''}</div></div><button class="concept-close" type="button" aria-label="Close suggestions">×</button></div><div class="concept-list">${concepts.map((concept,index)=>`<button type="button" class="concept-card" data-concept-index="${index}"><span class="concept-rank">${index+1}</span><span><strong>${esc(concept.title)}</strong><span class="concept-direction">${esc(concept.direction)}</span><span class="concept-reasons">${reasonList(concept).slice(0,2).map(reason=>`<span class="concept-reason">${esc(reason)}</span>`).join('')}</span></span><span class="concept-score" aria-label="Personalization score ${esc(concept.score||0)}">${Number(concept.score||0)>0?'+':''}${esc(concept.score||0)}</span></button>`).join('')}</div><div class="concept-actions"><span class="concept-note">You can skip these and generate directly. Ranking: ${esc(result.ranking_version||'flavor-memory-v1')}</span><button id="skipConceptsBtn" type="button" class="btn ghost">Skip suggestions</button></div></div>`;
    document.body.appendChild(overlay);
    overlay.querySelector('.concept-close').onclick=()=>dismissConcepts('close_button');
    overlay.addEventListener('click',event=>{if(event.target===overlay)dismissConcepts('backdrop')});
    overlay.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();dismissConcepts('escape_key')}});
    overlay.querySelector('#skipConceptsBtn').onclick=()=>{
      const value=pending;
      closeDialog();
      void recordFeedback(value.sessionId,'skipped',null,{reason:'user_requested_direct_generation'},value.profileId);
      originalGenerate(value.goal,value.culture,value.emoji);
      void recordFeedback(value.sessionId,'generated',null,{source:'skip_suggestions'},value.profileId);
    };
    overlay.querySelectorAll('[data-concept-index]').forEach(button=>button.onclick=()=>{
      const index=Number(button.dataset.conceptIndex);
      const concept=concepts[index];
      const value=pending;
      closeDialog();
      void recordFeedback(value.sessionId,'selected',concept.id||null,{rank:index+1,score:concept.score||0},value.profileId);
      const selectedGoal=`${concept.direction}\n\nOriginal request: ${value.goal}`;
      originalGenerate(selectedGoal,concept.cuisine||value.culture,value.emoji);
      void recordFeedback(value.sessionId,'generated',concept.id||null,{rank:index+1},value.profileId);
    });
    overlay.querySelector('[data-concept-index]')?.focus();
  }

  async function requestConcepts(goal,culture){
    const token=localStorage.getItem('glucoplate_firebase_id_token');
    if(!token)throw new Error('Sign in is required for personalized suggestions.');
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),12000);
    let response;
    try{
      response=await authenticatedFetch('/api/recommendations/recipe-concepts',{
        method:'POST',
        signal:controller.signal,
        body:JSON.stringify({goal,culture,profile_id:activeProfileId(),limit:3,candidates:[]})
      });
    }finally{clearTimeout(timeout)}
    if(!response.ok){
      let detail='Could not rank recipe directions.';
      try{detail=(await response.json()).detail||detail}catch(_error){}
      throw new Error(detail);
    }
    return response.json();
  }

  async function recommendBeforeGenerate(goalOverride=null,cultureOverride=null,emoji=null){
    const goal=String(goalOverride||document.getElementById('goal')?.value||'').trim();
    if(!goal)return originalGenerate(goalOverride,cultureOverride,emoji);
    const token=localStorage.getItem('glucoplate_firebase_id_token');
    if(!token)return originalGenerate(goal,cultureOverride,emoji);
    const generateButton=document.getElementById('generateBtn');
    if(generateButton)generateButton.disabled=true;
    window.setThinking?.(true,'Finding your best options…','Ranking three directions using this profile’s Flavor Memory.');
    try{
      const result=await requestConcepts(goal,cultureOverride);
      renderConcepts(result,{goal,culture:cultureOverride,emoji});
    }catch(error){
      console.debug('Personalized concept ranking unavailable; using direct generation.',error);
      window.toast?.('Personalized suggestions were unavailable. Generating directly.');
      return originalGenerate(goal,cultureOverride,emoji);
    }finally{
      if(generateButton)generateButton.disabled=false;
      window.setThinking?.(false);
    }
  }

  window.generateRecipe=recommendBeforeGenerate;
  window.GlucoPlateRecommendationUi={requestConcepts,renderConcepts,recommendBeforeGenerate,recordFeedback,closeDialog,dismissConcepts};
})();
