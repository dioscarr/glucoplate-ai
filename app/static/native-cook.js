(()=>{
  let touchStartX=0,touchStartY=0,wakeLockActive=false;
  const device=()=>window.DeviceManager;
  const current=()=>window.currentRecipe||null;
  const notify=(message)=>typeof window.toast==='function'?window.toast(message):console.info(message);

  function recipeShareText(recipe){
    const ingredients=(recipe.ingredients||[]).map(item=>`• ${item}`).join('\n');
    const steps=(recipe.steps||[]).map((step,index)=>`${index+1}. ${step}`).join('\n');
    return `${recipe.summary||''}\n\nIngredients\n${ingredients}\n\nDirections\n${steps}`.trim();
  }

  async function shareCurrentRecipe(){
    const recipe=current();
    if(!recipe){notify('Generate or open a recipe first.');return}
    try{
      const usedNative=await device()?.share({title:recipe.title||'GlucoPlate recipe',text:recipeShareText(recipe),url:location.href});
      device()?.haptic('success');
      notify(usedNative?'Recipe shared.':'Recipe copied to your clipboard.');
    }catch(error){
      if(error?.name!=='AbortError')notify('Could not share this recipe.');
    }
  }

  function installShareButton(){
    const actions=document.querySelector('.recipe-actions');
    if(!actions||actions.querySelector('#shareRecipeBtn'))return;
    const button=document.createElement('button');
    button.id='shareRecipeBtn';button.type='button';button.className='btn ghost';button.textContent='Share';button.onclick=shareCurrentRecipe;
    const newButton=actions.querySelector('#newBtn');actions.insertBefore(button,newButton||null);
  }

  async function enterCookMode(){
    const recipe=current();
    if(!recipe)return;
    wakeLockActive=await device()?.requestWakeLock()===true;
    document.documentElement.classList.toggle('cook-wake-lock',wakeLockActive);
    device()?.haptic('light');
    attachSwipeSurface();
  }

  async function leaveCookMode(){
    wakeLockActive=false;document.documentElement.classList.remove('cook-wake-lock');
    await device()?.releaseWakeLock();
  }

  function goNext(){if(typeof window.nextStep==='function'){device()?.haptic('light');window.nextStep()}}
  function goPrevious(){if(typeof window.prevStep==='function'){device()?.haptic('light');window.prevStep()}}

  function attachSwipeSurface(){
    const surface=document.getElementById('cookMode');
    if(!surface||surface.dataset.swipeReady==='true')return;
    surface.dataset.swipeReady='true';
    surface.addEventListener('touchstart',event=>{const touch=event.changedTouches[0];touchStartX=touch.clientX;touchStartY=touch.clientY},{passive:true});
    surface.addEventListener('touchend',event=>{const touch=event.changedTouches[0],dx=touch.clientX-touchStartX,dy=touch.clientY-touchStartY;if(Math.abs(dx)<65||Math.abs(dx)<Math.abs(dy)*1.3)return;dx<0?goNext():goPrevious()},{passive:true});
  }

  function enhanceCookControls(){
    const cook=document.getElementById('cookMode');if(!cook)return;
    attachSwipeSurface();
    const controls=cook.querySelector('.cook-controls');if(!controls)return;
    controls.querySelectorAll('button').forEach(button=>{button.classList.add('cook-native-control');button.setAttribute('aria-label',button.textContent.trim())});
    if(current()&&!cook.querySelector('.cook-swipe-hint')){const hint=document.createElement('span');hint.className='cook-swipe-hint';hint.textContent='Swipe left or right to change steps';controls.insertAdjacentElement('afterend',hint)}
  }

  function wrapGlobals(){
    const originalStart=window.startCookMode;
    if(typeof originalStart==='function'&&!originalStart.__nativeWrapped){
      const wrapped=function(...args){const result=originalStart.apply(this,args);queueMicrotask(()=>{enhanceCookControls();enterCookMode()});return result};
      wrapped.__nativeWrapped=true;window.startCookMode=wrapped;
    }
    const originalShow=window.showView;
    if(typeof originalShow==='function'&&!originalShow.__nativeWrapped){
      const wrapped=function(id,...args){if(id!=='cookView')leaveCookMode();const result=originalShow.call(this,id,...args);if(id==='recipeView')queueMicrotask(installShareButton);return result};
      wrapped.__nativeWrapped=true;window.showView=wrapped;
    }
    const originalNext=window.nextStep;
    if(typeof originalNext==='function'&&!originalNext.__nativeWrapped){const wrapped=function(...args){const before=window.cookIndex;const result=originalNext.apply(this,args);device()?.haptic(window.cookIndex===before?'success':'light');queueMicrotask(enhanceCookControls);return result};wrapped.__nativeWrapped=true;window.nextStep=wrapped}
    const originalPrev=window.prevStep;
    if(typeof originalPrev==='function'&&!originalPrev.__nativeWrapped){const wrapped=function(...args){device()?.haptic('light');const result=originalPrev.apply(this,args);queueMicrotask(enhanceCookControls);return result};wrapped.__nativeWrapped=true;window.prevStep=wrapped}
  }

  const observer=new MutationObserver(()=>{installShareButton();enhanceCookControls()});
  window.addEventListener('pagehide',leaveCookMode);
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible'&&document.getElementById('cookView')?.classList.contains('active'))enterCookMode()});
  window.addEventListener('DOMContentLoaded',()=>{wrapGlobals();observer.observe(document.body,{subtree:true,childList:true});installShareButton();enhanceCookControls()});
  window.GlucoPlateNativeCook={shareCurrentRecipe,enterCookMode,leaveCookMode};
})();