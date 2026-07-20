(()=>{
  const ADMIN_ROLES=new Set(['platform_admin','enterprise_owner','enterprise_admin','admin']);
  const PLATFORM_ROLES=new Set(['platform_admin']);
  const ROLE_OPTIONS=['enterprise_owner','enterprise_admin','manager','member','viewer'];
  let session=null,users=[];

  const byId=id=>document.getElementById(id);
  const token=()=>localStorage.getItem('glucoplate_firebase_id_token')||'';
  const readSession=()=>JSON.parse(localStorage.getItem('glucoplate_firebase_session')||'null');
  const escapeHtml=value=>String(value??'').replace(/[&<>'"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
  const titleCase=value=>String(value||'').replaceAll('_',' ').replace(/\b\w/g,ch=>ch.toUpperCase());

  function alert(message,type='error'){
    const node=byId('adminAlert');
    node.textContent=message;node.className=`alert ${type==='success'?'success':''}`;
    window.clearTimeout(alert.timeout);alert.timeout=window.setTimeout(()=>node.classList.add('hidden'),4500);
  }

  async function api(path,options={}){
    const authToken=token();
    if(!authToken)throw new Error('Your session is not ready. Sign in again.');
    const response=await fetch(path,{...options,headers:{'Content-Type':'application/json',Authorization:`Bearer ${authToken}`,...(options.headers||{})}});
    const body=await response.json().catch(()=>({}));
    if(!response.ok){
      if(response.status===401)throw new Error('Your session expired. Sign in again.');
      throw new Error(body.detail||'The request could not be completed.');
    }
    return body;
  }

  function switchView(name){
    document.querySelectorAll('.view').forEach(view=>view.classList.toggle('active',view.id===`${name}View`));
    document.querySelectorAll('.nav-item').forEach(item=>item.classList.toggle('active',item.dataset.view===name));
    byId('pageTitle').textContent=titleCase(name);
    if(name==='users')loadUsers();
    if(name==='enterprises')loadEnterprises();
  }

  function applyRoleVisibility(){
    const role=session?.enterprise?.role||'member';
    document.querySelectorAll('.platform-only').forEach(node=>node.classList.toggle('hidden',!PLATFORM_ROLES.has(role)));
    if(!ADMIN_ROLES.has(role)){
      alert('This account does not have enterprise administration permission.');
      document.querySelectorAll('.nav-item').forEach(item=>item.disabled=true);
      return false;
    }
    return true;
  }

  function setIdentity(){
    const user=session?.user||{},enterprise=session?.enterprise||{};
    byId('adminIdentity').textContent=`${user.name||user.email||'Administrator'} · ${enterprise.company_name||'Platform'} · ${titleCase(enterprise.role)}`;
    byId('metricEnterprise').textContent=enterprise.company_name||'Platform';
    byId('metricRole').textContent=titleCase(enterprise.role);
  }

  function userRow(member){
    const roleOptions=ROLE_OPTIONS.map(role=>`<option value="${role}" ${member.role===role?'selected':''}>${titleCase(role)}</option>`).join('');
    const targetId=escapeHtml(member.user_id||member.id);
    return `<tr data-user-id="${targetId}">
      <td class="user-name"><strong>${escapeHtml(member.display_name||member.name||member.email||'Unnamed user')}</strong><span>${escapeHtml(member.email||'No email')}</span></td>
      <td><select class="role-select" data-role-select>${roleOptions}</select></td>
      <td><span class="badge ${escapeHtml(member.status||'active')}">${titleCase(member.status||'active')}</span></td>
      <td>${escapeHtml(member.last_login_at||'—')}</td>
      <td><div class="row-actions"><button data-save-role>Save role</button><button class="${member.status==='disabled'?'':'danger'}" data-toggle-status>${member.status==='disabled'?'Reactivate':'Disable'}</button></div></td>
    </tr>`;
  }

  function renderUsers(){
    const query=byId('userSearch').value.trim().toLowerCase();
    const status=byId('statusFilter').value;
    const filtered=users.filter(member=>{
      const haystack=`${member.display_name||''} ${member.email||''}`.toLowerCase();
      return (!query||haystack.includes(query))&&(status==='all'||member.status===status);
    });
    byId('userRows').innerHTML=filtered.map(userRow).join('');
    byId('usersEmpty').classList.toggle('hidden',filtered.length>0);
  }

  async function loadUsers(){
    try{
      const result=await api('/api/enterprise/admin/users');
      users=result.users||[];
      renderUsers();
      const active=users.filter(user=>user.status!=='disabled').length;
      const admins=users.filter(user=>ADMIN_ROLES.has(user.role)).length;
      byId('metricActiveUsers').textContent=String(active);
      byId('metricAdmins').textContent=String(admins);
    }catch(error){alert(error.message);}
  }

  async function updateUser(row,changes){
    const userId=row.dataset.userId;
    try{
      await api(`/api/enterprise/admin/users/${encodeURIComponent(userId)}`,{method:'PATCH',body:JSON.stringify(changes)});
      alert('User membership updated.','success');
      await loadUsers();
    }catch(error){alert(error.message);}
  }

  async function loadEnterprises(){
    if(!PLATFORM_ROLES.has(session?.enterprise?.role))return;
    try{
      const result=await api('/api/enterprise/platform/enterprises');
      const enterprises=result.enterprises||[];
      byId('enterpriseCards').innerHTML=enterprises.length?enterprises.map(item=>`<article class="enterprise-card"><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.slug||item.id)}</span><span>Plan: ${escapeHtml(titleCase(item.plan||'standard'))}</span><span>Status: ${escapeHtml(titleCase(item.status||'active'))}</span><button class="button secondary" data-generate-code="${escapeHtml(item.id)}">Generate access code</button></article>`).join(''):'<div class="empty">No enterprises found.</div>';
    }catch(error){alert(error.message);}
  }

  function wireEvents(){
    document.querySelectorAll('.nav-item').forEach(item=>item.addEventListener('click',()=>switchView(item.dataset.view)));
    document.querySelectorAll('[data-open-view]').forEach(item=>item.addEventListener('click',()=>switchView(item.dataset.openView)));
    byId('refreshUsers').addEventListener('click',loadUsers);
    byId('refreshOverview').addEventListener('click',loadUsers);
    byId('refreshEnterprises').addEventListener('click',loadEnterprises);
    byId('enterpriseCreateForm').addEventListener('submit',async event=>{event.preventDefault();try{const name=byId('enterpriseName').value.trim();const slug=byId('enterpriseSlug').value.trim()||undefined;await api('/api/enterprise/platform/enterprises',{method:'POST',body:JSON.stringify({name,slug})});byId('enterpriseCreateForm').reset();alert('Company registered.','success');await loadEnterprises();}catch(error){alert(error.message);}});\n    byId('enterpriseCards').addEventListener('click',async event=>{const button=event.target.closest('[data-generate-code]');if(!button)return;try{const result=await api(`/api/enterprise/platform/enterprises/${encodeURIComponent(button.dataset.generateCode)}/access-codes`,{method:'POST',body:JSON.stringify({})});const code=result.access_code.code;const node=byId('newAccessCode');node.innerHTML=`<strong>New access code</strong><code>${escapeHtml(code)}</code><span>Copy it now. For security, it will not be shown again.</span>`;node.classList.remove('hidden');await navigator.clipboard?.writeText(code);alert('Access code generated and copied.','success');}catch(error){alert(error.message);}});
    byId('userSearch').addEventListener('input',renderUsers);
    byId('statusFilter').addEventListener('change',renderUsers);
    byId('userRows').addEventListener('click',event=>{
      const row=event.target.closest('tr[data-user-id]');if(!row)return;
      if(event.target.closest('[data-save-role]'))updateUser(row,{role:row.querySelector('[data-role-select]').value});
      if(event.target.closest('[data-toggle-status]')){
        const current=row.querySelector('.badge').textContent.trim().toLowerCase();
        updateUser(row,{status:current==='disabled'?'active':'disabled'});
      }
    });
    window.addEventListener('storage',event=>{if(event.key==='glucoplate_firebase_session')initialize();});
  }

  async function initialize(){
    session=readSession();
    if(!session?.enterprise){
      byId('adminIdentity').textContent='Waiting for sign-in…';
      window.setTimeout(initialize,700);return;
    }
    setIdentity();
    if(!applyRoleVisibility())return;
    await loadUsers();
  }

  window.addEventListener('DOMContentLoaded',()=>{wireEvents();initialize();});
})();
