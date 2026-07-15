(()=>{
  const DB='glucoplate-native-v1',STORE='pending-actions';
  const notify=message=>typeof window.toast==='function'?window.toast(message):console.info(message);
  function openDb(){return new Promise((resolve,reject)=>{const request=indexedDB.open(DB,2);request.onupgradeneeded=()=>{const db=request.result;if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE,{keyPath:'id',autoIncrement:true})};request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error)})}
  async function enqueue(action){const db=await openDb();await new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).add({...action,createdAt:Date.now()});tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)});db.close()}
  async function all(){const db=await openDb();const values=await new Promise((resolve,reject)=>{const request=db.transaction(STORE).objectStore(STORE).getAll();request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error)});db.close();return values}
  async function remove(id){const db=await openDb();await new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).delete(id);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)});db.close()}
  async function flush(){if(!navigator.onLine)return;const actions=await all();let completed=0;for(const action of actions){try{const response=await fetch(action.url,{method:action.method||'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(action.body)});if(response.ok){await remove(action.id);completed++}}catch{break}}if(completed)notify(`${completed} offline action${completed===1?'':'s'} synced.`)}
  function wrapSave(){const original=window.saveRecipe;if(typeof original!=='function'||original.__offlineWrapped)return;const wrapped=async function(...args){if(navigator.onLine){try{return await original.apply(this,args)}catch{}}if(!window.currentRecipe){notify('No recipe available to save.');return}await enqueue({url:'/api/recipes/save',method:'POST',body:window.currentRecipe});window.DeviceManager?.haptic?.('success');notify('Recipe queued and will save when you are back online.');};wrapped.__offlineWrapped=true;window.saveRecipe=wrapped}
  window.addEventListener('online',flush);
  window.addEventListener('DOMContentLoaded',()=>{wrapSave();flush()});
  const observer=new MutationObserver(wrapSave);window.addEventListener('DOMContentLoaded',()=>observer.observe(document.body,{subtree:true,childList:true}));
  window.GlucoPlateOfflineActions={enqueue,flush,all};
})();
