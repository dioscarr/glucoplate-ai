(()=>{
  const DB_NAME='glucoplate-native';
  const DB_VERSION=1;
  const STORE='recipes';
  const openDb=()=>new Promise((resolve,reject)=>{
    if(!('indexedDB'in window)){reject(new Error('IndexedDB unavailable'));return}
    const request=indexedDB.open(DB_NAME,DB_VERSION);
    request.onupgradeneeded=()=>{const db=request.result;if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE,{keyPath:'id'})};
    request.onsuccess=()=>resolve(request.result);
    request.onerror=()=>reject(request.error);
  });
  async function cacheRecipe(recipe){
    if(!recipe)return;
    const db=await openDb();
    const id=recipe.id||`${recipe.title||'recipe'}:${Date.now()}`;
    await new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).put({id,recipe,cachedAt:new Date().toISOString()});tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)});
  }
  async function cachedRecipes(){
    const db=await openDb();
    return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly');const request=tx.objectStore(STORE).getAll();request.onsuccess=()=>resolve(request.result.sort((a,b)=>String(b.cachedAt).localeCompare(String(a.cachedAt))).map(x=>x.recipe));request.onerror=()=>reject(request.error)});
  }
  const notify=message=>typeof window.toast==='function'?window.toast(message):console.info(message);
  function parseIngredients(text){
    return [...new Set(String(text||'').split(/\n|,|;/).map(x=>x.replace(/^[-*•\d.)\s]+/,'').trim().toLowerCase()).filter(x=>x.length>1))].slice(0,30);
  }
  function applyIngredients(items){
    if(!items.length){notify('No ingredients found in the clipboard.');return}
    if(Array.isArray(window.selectedFoods))window.selectedFoods=[...new Set([...window.selectedFoods,...items])];
    const goal=document.getElementById('goal');
    if(goal)goal.value=`Create a practical recipe using ${items.join(', ')}. Include substitutions and estimated nutrition.`;
    if(typeof window.renderFoods==='function')window.renderFoods();
    notify(`Imported ${items.length} ingredients`);
    window.DeviceManager?.haptic?.('success');
  }
  async function importClipboard(){
    if(!navigator.clipboard?.readText){notify('Clipboard import is not available in this browser.');return}
    try{applyIngredients(parseIngredients(await navigator.clipboard.readText()))}catch{notify('Clipboard permission was not granted.')}
  }
  function choosePhoto(){document.getElementById('ingredientPhotoInput')?.click()}
  function handlePhoto(event){
    const file=event.target.files?.[0];
    if(!file)return;
    const preview=document.getElementById('ingredientPhotoPreview');
    const image=document.getElementById('ingredientPhotoImage');
    const label=document.getElementById('ingredientPhotoLabel');
    if(image)image.src=URL.createObjectURL(file);
    if(label)label.textContent=`${file.name||'Ingredient photo'} selected. Add the visible ingredients to the prompt, then generate.`;
    preview?.classList.remove('hidden');
    const goal=document.getElementById('goal');
    if(goal&&!goal.value.trim())goal.value='Create a recipe from the ingredients visible in my selected kitchen photo: ';
    notify('Photo attached as a visual reference');
    window.DeviceManager?.haptic?.('light');
  }
  function installImportPanel(){
    const selected=document.getElementById('selectedFoods');
    const section=selected?.closest('.card')||document.getElementById('discoverView')?.querySelector('.card:last-of-type');
    if(!section||document.getElementById('ingredientImportPanel'))return;
    section.insertAdjacentHTML('beforeend',`<div id="ingredientImportPanel" class="native-import-panel"><strong>Bring in ingredients</strong><span>Paste a grocery list or use your camera/photo library as a visual reference.</span><div class="native-import-actions"><button id="clipboardIngredientBtn" class="btn secondary" type="button">Paste ingredients</button><button id="photoIngredientBtn" class="btn ghost" type="button">Camera or photo</button></div><input id="ingredientPhotoInput" class="hidden" type="file" accept="image/*" capture="environment"><div id="ingredientPhotoPreview" class="native-photo-preview hidden"><img id="ingredientPhotoImage" alt="Selected ingredients"><span id="ingredientPhotoLabel"></span></div></div>`);
    document.getElementById('clipboardIngredientBtn').onclick=importClipboard;
    document.getElementById('photoIngredientBtn').onclick=choosePhoto;
    document.getElementById('ingredientPhotoInput').onchange=handlePhoto;
  }
  function wrapRecipeFunctions(){
    const originalRender=window.renderRecipe;
    if(typeof originalRender==='function'&&!originalRender.__offlineWrapped){
      const wrapped=function(recipe,...args){cacheRecipe(recipe).catch(()=>{});return originalRender.call(this,recipe,...args)};
      wrapped.__offlineWrapped=true;window.renderRecipe=wrapped;
    }
    const originalLoad=window.loadSaved;
    if(typeof originalLoad==='function'&&!originalLoad.__offlineWrapped){
      const wrapped=async function(){
        try{await originalLoad.call(this);const current=window.savedRecipes||[];for(const recipe of current)cacheRecipe(recipe).catch(()=>{})}
        catch{}
        if(!navigator.onLine){
          try{const recipes=await cachedRecipes();window.savedRecipes=recipes;const list=document.getElementById('savedList');if(list&&recipes.length){list.innerHTML=recipes.map((x,i)=>`<button class="saved-item" data-index="${i}"><span style="font-size:1.6rem">🍽️</span><span><strong>${String(x.title||'Cached recipe').replace(/[&<>"']/g,'')}</strong><span>Available offline</span></span><span>›</span></button>`).join('');list.querySelectorAll('.saved-item').forEach(button=>button.onclick=()=>window.renderRecipe(recipes[Number(button.dataset.index)]))}}
          catch{}
        }
      };
      wrapped.__offlineWrapped=true;window.loadSaved=wrapped;
    }
  }
  window.addEventListener('offline',()=>{notify('Offline mode: cached recipes remain available.');window.loadSaved?.()});
  window.addEventListener('online',()=>notify('Back online'));
  window.addEventListener('DOMContentLoaded',()=>{installImportPanel();wrapRecipeFunctions();setTimeout(()=>window.loadSaved?.(),0)});
  window.GlucoPlateIngredients={importClipboard,choosePhoto,parseIngredients,cacheRecipe,cachedRecipes};
})();