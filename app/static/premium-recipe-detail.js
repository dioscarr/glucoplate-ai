(()=>{
  const MIN_SERVINGS=1,MAX_SERVINGS=12;
  const FRACTIONS={'¼':.25,'½':.5,'¾':.75,'⅓':1/3,'⅔':2/3,'⅛':.125,'⅜':.375,'⅝':.625,'⅞':.875};
  function stableHash(value){let hash=2166136261;for(let i=0;i<value.length;i++){hash^=value.charCodeAt(i);hash=Math.imul(hash,16777619)}return(hash>>>0).toString(36)}
  function canonical(value){return String(value||'').trim().toLowerCase().replace(/\s+/g,' ')}
  function parseNumber(token){
    if(!token)return null;if(FRACTIONS[token]!==undefined)return FRACTIONS[token];
    if(/^\d+\s+\d+\/\d+$/.test(token)){const parts=token.split(/\s+/),fraction=parts[1].split('/').map(Number);return Number(parts[0])+fraction[0]/fraction[1]}
    if(/^\d+\/\d+$/.test(token)){const fraction=token.split('/').map(Number);return fraction[1]?fraction[0]/fraction[1]:null}
    const value=Number(token);return Number.isFinite(value)?value:null;
  }
  function parseIngredient(value){
    const text=typeof value==='string'?value:String(value&&value.text||value&&value.name||''),normalized=text.trim();
    const match=normalized.match(/^(\d+\s+\d+\/\d+|\d+\/\d+|\d+(?:\.\d+)?|[¼½¾⅓⅔⅛⅜⅝⅞])(?:\s+|$)(.*)$/);
    if(!match)return{text:normalized,quantity:null,remainder:normalized};
    return{text:normalized,quantity:parseNumber(match[1]),remainder:match[2].trim()};
  }
  function formatQuantity(value){
    if(!Number.isFinite(value))return'';const rounded=Math.round(value*8)/8,whole=Math.floor(rounded),numerator=Math.round((rounded-whole)*8);
    if(!numerator)return String(whole);const divisor=numerator%4===0?4:numerator%2===0?2:1,fraction=(numerator/divisor)+'/'+(8/divisor);return whole?whole+' '+fraction:fraction;
  }
  function normalizeRecipe(recipe){
    if(!recipe||typeof recipe!=='object')return recipe;
    const source=Array.isArray(recipe.ingredients)?recipe.ingredients:[],previous=Array.isArray(recipe.ingredient_details)?recipe.ingredient_details:[],recipeKey=canonical(recipe.id||recipe.recipe_id||recipe.title||'recipe'),seen=new Map();
    const details=source.map((item,index)=>{
      const parsed=parseIngredient(item),name=typeof item==='object'&&item&&item.name?String(item.name):parsed.remainder||parsed.text,key=canonical(parsed.text),occurrence=(seen.get(key)||0)+1,supplied=typeof item==='object'&&item?item:{};
      seen.set(key,occurrence);
      return Object.assign({},previous[index]||{},supplied,{id:supplied.id||previous[index]&&previous[index].id||'ing_'+stableHash(recipeKey+'|'+key+'|'+occurrence),text:parsed.text,name:name,quantity:Number.isFinite(supplied.quantity)?Number(supplied.quantity):parsed.quantity,remainder:parsed.remainder});
    });
    const base=Math.max(MIN_SERVINGS,Math.min(MAX_SERVINGS,Number(recipe.base_servings||recipe.servings)||4));
    recipe.ingredients=details.map(detail=>detail.text);recipe.ingredient_details=details;recipe.base_servings=base;recipe.selected_servings=Math.max(MIN_SERVINGS,Math.min(MAX_SERVINGS,Number(recipe.selected_servings)||base));return recipe;
  }
  function ingredientSection(){return Array.from(document.querySelectorAll('.recipe-section')).find(section=>{const heading=section.querySelector('h2');return heading&&heading.textContent.trim().toLowerCase()==='ingredients'})}
  function renderScaledIngredients(recipe){
    const section=ingredientSection();if(!section)return;const factor=recipe.selected_servings/recipe.base_servings;
    section.querySelectorAll('.ingredient-list li').forEach((item,index)=>{const detail=recipe.ingredient_details[index];if(!detail)return;item.dataset.ingredientId=detail.id;const label=item.querySelector('span:last-child');if(label)label.textContent=Number.isFinite(detail.quantity)?(formatQuantity(detail.quantity*factor)+' '+detail.remainder).trim():detail.text});
    const output=document.getElementById('premiumServingValue');if(output)output.textContent=recipe.selected_servings+' '+(recipe.selected_servings===1?'serving':'servings');
  }
  function changeServings(recipe,delta){
    const next=Math.max(MIN_SERVINGS,Math.min(MAX_SERVINGS,recipe.selected_servings+delta));if(next===recipe.selected_servings)return;recipe.selected_servings=next;renderScaledIngredients(recipe);window.currentRecipe=recipe;
    window.dispatchEvent(new CustomEvent('glucoplate:servings-changed',{detail:{recipeId:recipe.id||recipe.recipe_id||null,baseServings:recipe.base_servings,selectedServings:next}}));if(navigator.vibrate)navigator.vibrate(12);
  }
  function ensureStyles(){
    if(document.getElementById('premiumRecipeDetailStyles'))return;const style=document.createElement('style');style.id='premiumRecipeDetailStyles';
    style.textContent='.premium-serving-control{display:flex;align-items:center;justify-content:space-between;gap:16px;margin:0 0 18px;padding:16px 18px;border:1px solid var(--line,#e7ded4);border-radius:20px;background:linear-gradient(135deg,rgba(255,255,255,.96),rgba(255,248,240,.82));box-shadow:0 10px 28px rgba(59,43,30,.08)}.premium-serving-copy strong{display:block;font-size:1rem}.premium-serving-copy small{display:block;margin-top:3px;color:var(--muted,#756f69);line-height:1.35}.premium-serving-stepper{display:grid;grid-template-columns:48px minmax(92px,auto) 48px;align-items:center;border:1px solid var(--line,#e7ded4);border-radius:999px;background:var(--surface,#fff);overflow:hidden;flex:none}.premium-serving-stepper button{width:48px;height:48px;border:0;background:transparent;color:var(--text,#211f1d);font-size:1.45rem;cursor:pointer;touch-action:manipulation}.premium-serving-stepper button:hover{background:var(--surface2,#f3ede6)}.premium-serving-stepper button:focus-visible{outline:3px solid var(--brand,#f26a2e);outline-offset:-3px}#premiumServingValue{text-align:center;font-weight:800;font-size:.9rem;white-space:nowrap}.ingredient-list li[data-ingredient-id]{transition:transform .18s ease}.ingredient-list li[data-ingredient-id]:active{transform:scale(.985)}@media(max-width:520px){.premium-serving-control{align-items:flex-start;flex-direction:column}.premium-serving-stepper{width:100%;grid-template-columns:48px 1fr 48px}}';document.head.appendChild(style);
  }
  function enhanceRecipeDetail(recipe){
    const section=ingredientSection();if(!section)return;ensureStyles();const old=document.getElementById('premiumServingControl');if(old)old.remove();
    const control=document.createElement('section');control.id='premiumServingControl';control.className='premium-serving-control';control.setAttribute('aria-label','Adjust recipe servings');
    control.innerHTML='<div class="premium-serving-copy"><strong>Make it your size</strong><small>Ingredient amounts scale automatically.</small></div><div class="premium-serving-stepper"><button type="button" aria-label="Decrease servings">−</button><output id="premiumServingValue" aria-live="polite"></output><button type="button" aria-label="Increase servings">+</button></div>';
    const buttons=control.querySelectorAll('button');buttons[0].addEventListener('click',()=>changeServings(recipe,-1));buttons[1].addEventListener('click',()=>changeServings(recipe,1));section.before(control);renderScaledIngredients(recipe);
  }
  function install(){
    const original=window.renderRecipe;if(typeof original!=='function'||original.__premiumRecipeDetail)return;
    const wrapped=function(recipe,...args){const normalized=normalizeRecipe(recipe),result=original.call(this,normalized,...args);queueMicrotask(()=>enhanceRecipeDetail(normalized));return result};wrapped.__premiumRecipeDetail=true;window.renderRecipe=wrapped;
  }
  window.GlucoPlateRecipeDetail={normalizeRecipe:normalizeRecipe,parseIngredient:parseIngredient,formatQuantity:formatQuantity,changeServings:changeServings};window.addEventListener('DOMContentLoaded',install);
})();