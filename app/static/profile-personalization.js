(()=>{
  const nativeFetch=window.fetch.bind(window);
  const ACTIVE_PROFILE_KEY='glucoplate_active_profile_id';
  let lastContext=null;

  const activeProfileId=()=>localStorage.getItem(ACTIVE_PROFILE_KEY)||null;
  const cleanList=value=>Array.isArray(value)?value.map(item=>String(item||'').trim()).filter(Boolean):[];

  async function loadContext(){
    const api=window.GlucoPlateUserData;
    const profileId=activeProfileId();
    if(!api||!profileId)return null;
    try{
      const [profiles,preferences]=await Promise.all([api.listProfiles(),api.getPreferences(profileId)]);
      const profile=(profiles||[]).find(item=>item.profile_id===profileId||item.id===profileId);
      if(!profile)return null;
      return {profile,preferences:preferences||{}};
    }catch(error){
      console.warn('Profile personalization unavailable',error);
      return null;
    }
  }

  function personalizePayload(payload,context){
    if(!context)return payload;
    const profile=context.profile||{},preferences=context.preferences||{};
    const allergies=[...new Set([...cleanList(profile.allergies),...cleanList(preferences.allergies)])];
    const dislikes=cleanList(preferences.dislikes||preferences.avoid_ingredients);
    const dietary=[...new Set([...cleanList(profile.dietary_preferences),...cleanList(preferences.dietary_preferences)])];
    const cuisines=cleanList(preferences.favorite_cuisines||preferences.cuisines);
    const avoid=[...new Set([...(payload.avoid_ingredients||[]),...allergies,...dislikes])];
    const servingValue=Number(preferences.servings||preferences.default_servings||payload.servings||4);
    const preferencesList=[...(payload.preferences||[]),...dietary];
    if(cuisines.length)preferencesList.push(`Prefer ${cuisines.join(', ')} cuisine styles when appropriate`);
    preferencesList.push(`Personalize for ${profile.name||'the active household profile'}`);
    if(allergies.length)preferencesList.push(`Strictly exclude allergy ingredients: ${allergies.join(', ')}`);
    if(dislikes.length)preferencesList.push(`Avoid disliked ingredients: ${dislikes.join(', ')}`);
    return {
      ...payload,
      servings:Number.isFinite(servingValue)&&servingValue>0?Math.min(100,Math.round(servingValue)):4,
      preferences:[...new Set(preferencesList.filter(Boolean))],
      avoid_ingredients:avoid,
      profile_id:profile.profile_id||profile.id,
      profile_name:profile.name,
    };
  }

  window.fetch=async(input,init={})=>{
    const rawUrl=typeof input==='string'?input:input.url;
    const url=new URL(rawUrl,window.location.origin);
    if(url.pathname!=='/api/recipes/generate'||String(init.method||'GET').toUpperCase()!=='POST'||!init.body){
      return nativeFetch(input,init);
    }
    try{
      const payload=JSON.parse(init.body);
      lastContext=await loadContext();
      const personalized=personalizePayload(payload,lastContext);
      const headers=new Headers(init.headers||{});headers.set('Content-Type','application/json');
      return nativeFetch(input,{...init,headers,body:JSON.stringify(personalized)});
    }catch(error){
      console.warn('Recipe personalization skipped',error);
      return nativeFetch(input,init);
    }
  };

  function installRecipeLabel(){
    const original=window.renderRecipe;
    if(typeof original!=='function'||original.__profilePersonalized)return;
    const wrapped=function(recipe,...args){
      const result=original.call(this,recipe,...args);
      const profile=lastContext?.profile;
      if(profile){
        const kicker=document.querySelector('#result .recipe-kicker');
        if(kicker&&!kicker.querySelector('[data-profile-label]')){
          const badge=document.createElement('span');
          badge.className='pill';badge.dataset.profileLabel='true';
          badge.textContent=`For ${profile.avatar||'👤'} ${profile.name||'profile'}`;
          kicker.appendChild(badge);
        }
      }
      return result;
    };
    wrapped.__profilePersonalized=true;window.renderRecipe=wrapped;
  }

  window.addEventListener('DOMContentLoaded',()=>setTimeout(installRecipeLabel,0));
  window.addEventListener('glucoplate:profilechange',()=>{lastContext=null});
  window.GlucoPlatePersonalization={activeProfileId,loadContext,personalizePayload};
})();
