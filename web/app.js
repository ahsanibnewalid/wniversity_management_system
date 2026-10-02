const API=window.CAMPUSHUB_API||"/api/v1";
let token=localStorage.getItem("campushub_token"),page="dashboard",me=null,adminInstitutions=[],adminId=null,adminPage="overview";
const $=s=>document.querySelector(s);
const esc=v=>String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[m]));
async function api(path,opt={}){const r=await fetch(API+path,{...opt,headers:{"Content-Type":"application/json",...(token?{Authorization:"Bearer "+token}:{}),...(opt.headers||{})}});const j=await r.json().catch(()=>({}));if(!r.ok)throw Error(j.error||"Request failed");return j}
async function boot(){if(token){try{me=await api("/auth/me");adminInstitutions=(await api("/admin/institutions")).items||[];adminId=adminId||adminInstitutions[0]?.id}catch{token=null;localStorage.removeItem("campushub_token")}}render()}
function nav(){const base=["dashboard","courses","assignments","attendance","results","timetable","events","clubs","documents","services","fees","messages"];return base.map(p=>'<button class="'+(page===p?"active":"")+'" onclick="go(\''+p+'\')">'+p[0].toUpperCase()+p.slice(1)+'</button>').join("")+(adminInstitutions.length?'<button class="'+(page==="admin"?"active":"")+'" onclick="go(\'admin\')">University Admin</button>':"")}
function render(){if(!token){login();return}document.querySelector("#app").innerHTML='<div class="shell"><aside class="side"><div class="brand">CampusHub</div><div class="nav">'+nav()+'<button onclick="logout()">Sign out</button></div></aside><main class="main"><div class="top"><div><h1>'+esc(page==="admin"?"University Admin":page[0].toUpperCase()+page.slice(1))+'</h1><div class="muted">'+esc(me?.profile?.full_name||"Campus member")+'</div></div><button class="btn" onclick="load()">Refresh</button></div><section id="content"></section></main></div>';load()}
function login(){document.querySelector("#app").innerHTML='<div class="form card"><h1>CampusHub</h1><p class="muted">University management + community.</p><input id="email" placeholder="Email"><input id="password" type="password" placeholder="Password"><button class="btn" onclick="doLogin()">Sign in</button></div>'}
async function doLogin(){try{const j=await api("/auth/login",{method:"POST",body:JSON.stringify({email:$("#email").value,password:$("#password").value})});token=j.access_token;localStorage.setItem("campushub_token",token);await boot()}catch(e){alert(e.message)}}
function logout(){token=null;localStorage.removeItem("campushub_token");render()}function go(p){page=p;render()}
const card=(a,b)=>'<div class="card"><div class="muted">'+esc(a)+'</div><div class="stat">'+esc(b)+'</div></div>';
const list=items=>'<div class="list">'+items.map(x=>'<div class="row"><b>'+esc(x.title||x.name||x.full_name||x.email||("Item #"+x.id))+'</b><span>'+esc(x.status||x.role||x.code||"")+'</span></div>').join("")+'</div>';
async function load(){const c=$("#content");try{
if(page==="admin"){await loadAdmin(c);return}
if(page==="dashboard"){const j=await api("/dashboard").catch(()=>({stats:{courses:0,upcoming_assignments:0,attendance_percent:0}}));c.innerHTML='<div class="grid">'+card("Courses",j.stats.courses)+card("Upcoming assignments",j.stats.upcoming_assignments)+card("Attendance",j.stats.attendance_percent+"%")+card("Notifications",j.stats.unread_notifications||0)+'</div>';return}
if(page==="courses"){c.innerHTML=list((await api("/me/enrollments")).items);return}
if(page==="assignments"){const e=await api("/me/enrollments"),a=[];for(const x of e.items)a.push(...(await api("/offerings/"+x.offering_id+"/assignments")).items);c.innerHTML=list(a);return}
if(page==="attendance"){c.innerHTML=list((await api("/me/attendance")).items);return}
if(page==="results"){const j=await api("/me/transcript");c.innerHTML='<div class="grid">'+card("CGPA",j.cgpa)+card("Credits",j.credits)+'</div>'+list(j.results);return}
if(page==="timetable"){c.innerHTML=list((await api("/me/timetable")).items);return}
const paths={events:"/events",clubs:"/clubs",documents:"/documents",services:"/service-requests",fees:"/fees",messages:"/messages"};c.innerHTML=list((await api(paths[page]||"/events")).items||[]);
}catch(e){c.innerHTML='<div class="card"><h2>Unable to load</h2><p>'+esc(e.message)+'</p></div>'}}
async function loadAdmin(c){
if(!adminId){c.innerHTML='<div class="card"><h2>No managed university</h2><p>Create a university or ask an owner to grant you an admin role.</p></div>';return}
const tabs=["overview","institution","members","departments","sessions","faculties","programs","courses","groups","requests","events","clubs","services","fees"];
c.innerHTML='<div class="admin-head"><select id="adminUni" onchange="adminId=Number(this.value);adminPage=\'overview\';loadAdmin(document.querySelector(\'#content\'))">'+adminInstitutions.map(i=>'<option value="'+i.id+'" '+(i.id===adminId?"selected":"")+'>'+esc(i.name)+' · '+esc(i.role)+'</option>').join("")+'</select><div class="tabs">'+tabs.map(t=>'<button class="'+(adminPage===t?"active":"")+'" onclick="adminPage=\''+t+'\';loadAdmin(document.querySelector(\'#content\'))">'+t+'</button>').join("")+'</div></div><div id="adminBody"></div>';
const b=$("#adminBody");const q="/institutions/"+adminId+"/admin/";
if(adminPage==="overview"){const j=await api(q+"overview");b.innerHTML='<div class="grid">'+Object.entries(j.counts).map(([k,v])=>card(k,v)).join("")+'</div><div class="card"><h2>Role: '+esc(j.role)+'</h2><p class="muted">Your role controls exactly which university records you can edit.</p></div>';return}
if(adminPage==="institution"){const j=await api(q+"");const i=j.institution;b.innerHTML='<div class="form card"><h2>Edit university</h2>'+["name","slug","kind","address","website","description"].map(k=>'<input id="i_'+k+'" placeholder="'+k+'" value="'+esc(i[k])+'">').join("")+'<button class="btn" onclick="saveInstitution()">Save changes</button></div>';return}
if(adminPage==="members"){const j=await api(q+"members");b.innerHTML='<div class="form card"><h2>Add existing user</h2><input id="inviteEmail" placeholder="User email"><select id="inviteRole">'+["student","teacher","department_admin","media_manager","class_representative","principal","institution_admin"].map(x=>'<option>'+x+'</option>').join("")+'</select><input id="inviteStudent" placeholder="Student ID (optional)"><button class="btn" onclick="inviteUser()">Add member</button></div>'+j.items.map(x=>'<div class="row card"><div><b>'+esc(x.full_name||x.email)+'</b><div class="muted">'+esc(x.email)+' · '+esc(x.student_id||"")+'</div></div><select onchange="changeRole('+x.id+',this.value)">'+["student","teacher","department_admin","media_manager","class_representative","principal","institution_admin","institution_owner"].map(r=>'<option '+(x.role===r?"selected":"")+'>'+r+'</option>').join("")+'</select><button onclick="suspendMember('+x.id+')">Suspend</button></div>').join("");return}
const loaders={departments:"departments",sessions:"sessions",faculties:"faculties",programs:"programs",courses:"courses",groups:"groups",requests:"requests",events:"events",clubs:"clubs",services:"service-requests",fees:"fees"};
if(loaders[adminPage]){const j=await api(q+loaders[adminPage]);b.innerHTML=adminEditor(adminPage,j.items||[]);return}
}
function adminEditor(type,items){
let form="";
if(type==="departments")form='<input id="aName" placeholder="Department name"><input id="aCode" placeholder="Code"><button class="btn" onclick="addDepartment()">Add department</button>';
if(type==="sessions")form='<input id="aDep" placeholder="Department ID"><input id="aName" placeholder="Session name"><button class="btn" onclick="addSession()">Add session</button><input id="aSession" placeholder="Session ID"><input id="aYear" placeholder="Academic year name"><button class="btn" onclick="addYear()">Add year</button>';
if(type==="faculties")form='<input id="aName" placeholder="Faculty name"><input id="aCode" placeholder="Code"><button class="btn" onclick="addFaculty()">Add faculty</button>';
if(type==="programs")form='<input id="aDep" placeholder="Department ID"><input id="aName" placeholder="Program name"><input id="aCode" placeholder="Code"><input id="aDegree" placeholder="Degree"><button class="btn" onclick="addProgram()">Add program</button>';
if(type==="courses")form='<input id="aDep" placeholder="Department ID"><input id="aCode" placeholder="Course code"><input id="aName" placeholder="Course title"><input id="aCredits" placeholder="Credits" value="3"><button class="btn" onclick="addCourse()">Add course</button>';
if(type==="groups")form='<input id="aName" placeholder="Group name"><input id="aType" placeholder="Type" value="community"><input id="aDesc" placeholder="Description"><button class="btn" onclick="addGroup()">Create group</button>';
if(type==="events")form='<input id="aName" placeholder="Event title"><input id="aDesc" placeholder="Description"><input id="aLocation" placeholder="Location"><button class="btn" onclick="addEvent()">Create event</button>';
if(type==="fees")form='<input id="aStudent" placeholder="Student user ID"><input id="aName" placeholder="Fee title"><input id="aAmount" placeholder="Amount"><button class="btn" onclick="addFee()">Create fee</button>';
if(type==="requests")return items.map(x=>'<div class="row card"><span>Request #'+x.id+' · user '+x.user_id+' · '+esc(x.program)+'</span><span><button onclick="reviewRequest('+x.id+',\'approve\')">Approve</button> <button onclick="reviewRequest('+x.id+',\'reject\')">Reject</button></span></div>').join("");
if(type==="services")return items.map(x=>'<div class="row card"><span>#'+x.id+' · '+esc(x.request_type)+' · '+esc(x.details)+'</span><button onclick="serviceUpdate('+x.id+')">'+esc(x.status)+'</button></div>').join("");
return '<div class="form card">'+form+'</div>'+list(items);
}
async function postAdmin(path,body){await api("/institutions/"+adminId+"/admin/"+path,{method:"POST",body:JSON.stringify(body)});await loadAdmin($("#content"))}
async function saveInstitution(){const d={};["name","slug","kind","address","website","description"].forEach(k=>d[k]=$("#i_"+k).value);await api("/institutions/"+adminId+"/admin/institution",{method:"PUT",body:JSON.stringify(d)});alert("Saved");await boot()}
async function inviteUser(){await postAdmin("members/invite",{email:$("#inviteEmail").value,role:$("#inviteRole").value,student_id:$("#inviteStudent").value})}
async function changeRole(id,role){await api("/institutions/"+adminId+"/admin/members/"+id,{method:"PUT",body:JSON.stringify({role})});}
async function suspendMember(id){await api("/institutions/"+adminId+"/admin/members/"+id,{method:"DELETE"});await loadAdmin($("#content"))}
async function addDepartment(){await postAdmin("departments",{name:$("#aName").value,code:$("#aCode").value})}
async function addSession(){await postAdmin("sessions",{department_id:Number($("#aDep").value),name:$("#aName").value})}
async function addYear(){await postAdmin("years",{session_id:Number($("#aSession").value),name:$("#aYear").value})}
async function addFaculty(){await postAdmin("faculties",{name:$("#aName").value,code:$("#aCode").value})}
async function addProgram(){await postAdmin("programs",{department_id:Number($("#aDep").value),name:$("#aName").value,code:$("#aCode").value,degree:$("#aDegree").value})}
async function addCourse(){await postAdmin("courses",{department_id:Number($("#aDep").value),code:$("#aCode").value,title:$("#aName").value,credits:Number($("#aCredits").value)})}
async function addGroup(){await postAdmin("groups",{name:$("#aName").value,group_type:$("#aType").value,description:$("#aDesc").value})}
async function addEvent(){await postAdmin("events",{title:$("#aName").value,description:$("#aDesc").value,location:$("#aLocation").value})}
async function addFee(){await postAdmin("fees",{student_id:Number($("#aStudent").value),title:$("#aName").value,amount:Number($("#aAmount").value)})}
async function reviewRequest(id,decision){await api("/institutions/"+adminId+"/admin/requests/"+id+"/review",{method:"POST",body:JSON.stringify({decision})});await loadAdmin($("#content"))}
async function serviceUpdate(id){const status=prompt("New status: submitted, processing, completed, rejected");if(!status)return;const response=prompt("Response (optional)")||"";await api("/institutions/"+adminId+"/admin/service-requests/"+id,{method:"PUT",body:JSON.stringify({status,response})});await loadAdmin($("#content"))}
boot();