(function(){
  const API=window.CAMPUSHUB_API||"/api/v1";
  const token=localStorage.getItem("campushub_token");
  if(!token)return;
  const esc=v=>String(v??"").replace(/[&<>"]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[m]));
  const get=async p=>{const r=await fetch(API+p,{headers:{Authorization:"Bearer "+token}});return r.json().catch(()=>({}))};
  const navItems=[
    ["dashboard","Home"],["courses","Courses"],["assignments","Assignments"],["attendance","Attendance"],
    ["results","Results & CGPA"],["timetable","Timetable"],["calendar","Academic Calendar"],
    ["community","Community"],["events","Events"],["clubs","Clubs"],["documents","Documents"],
    ["services","Student Services"],["campus","Campus Services"],["library","Library"],["hostel","Hostel"],
    ["lost-found","Lost & Found"],["fees","Fees"],["messages","Messages"],["notifications","Notifications"],
    ["search","Global Search"],["profile","My Profile"],["university","My University"]
  ];
  function refreshShell(){
    const shell=document.querySelector(".shell"); if(!shell)return;
    const side=shell.querySelector(".side"), nav=side?.querySelector(".nav"); if(!nav)return;
    const admin=Array.from(nav.querySelectorAll("button")).find(b=>/University Admin/i.test(b.textContent));
    nav.innerHTML=navItems.map(x=>'<button onclick="go(\''+x[0]+'\')">'+x[1]+"</button>").join("");
    if(admin)nav.insertAdjacentHTML("beforeend",'<button onclick="go(\'admin\')">University Admin</button>');
    nav.insertAdjacentHTML("beforeend",'<button data-key="campushub_token" onclick="localStorage.removeItem(this.dataset.key);location.reload()">Sign out</button>');
  }
  async function restoreDashboard(){
    const content=document.querySelector("#content"); if(!content)return;
    const [dash,insts]=await Promise.all([get("/dashboard"),get("/my/institutions")]);
    const s=dash.stats||{}, institutions=insts.items||[];
    const card=(title,value,desc)=>'<div class="card"><div class="muted">'+esc(title)+'</div><div class="stat">'+esc(value)+'</div><p class="muted">'+esc(desc)+'</p></div>';
    const tile=(id,title,desc)=>'<button class="module-card" onclick="go(\''+id+'\')"><strong>'+esc(title)+'</strong><span>'+esc(desc)+'</span><em>Open →</em></button>';
    content.innerHTML=
      '<div class="welcome card"><span class="eyebrow">CAMPUSHUB HOME</span><h2>Welcome back 👋</h2><p class="muted">'+esc(institutions[0]?.name||"No university selected yet. Join or create one from My University.")+'</p><div class="hero-actions"><button class="btn" onclick="go(\'university\')">My University</button><button class="ghost" onclick="go(\'profile\')">My Profile</button></div></div>'+
      '<div class="grid">'+card("Courses",s.courses||0,"Current enrolments")+card("Upcoming assignments",s.upcoming_assignments||0,"Deadlines to watch")+card("Attendance",(s.attendance_percent||0)+"%","Current attendance")+card("Notifications",s.unread_notifications||0,"Unread updates")+'</div>'+
      '<div class="section-title"><h2>Academic</h2><span class="muted">Everything for your studies</span></div><div class="module-grid">'+
      [["courses","Courses","Current courses and enrolments"],["assignments","Assignments","Submit work and view feedback"],["attendance","Attendance","Track attendance records"],["results","Results & CGPA","Results, GPA and transcript"],["timetable","Timetable","Today and weekly classes"],["calendar","Academic Calendar","Classes, exams and deadlines"]].map(x=>tile(...x)).join("")+
      '</div><div class="section-title"><h2>Campus & Community</h2><span class="muted">Stay connected beyond the classroom</span></div><div class="module-grid">'+
      [["community","Community","Groups, posts, comments and reactions"],["events","Events","Campus events and registrations"],["clubs","Clubs","Clubs and memberships"],["documents","Documents","Course and university files"],["services","Student Services","Requests and tracking"],["campus","Campus Services","Campus resources"],["library","Library","Library resources"],["hostel","Hostel","Hostel rooms and services"],["lost-found","Lost & Found","Find or report items"],["fees","Fees","Balances and payment history"],["messages","Messages","Campus communication"],["notifications","Notifications","Announcements and alerts"]].map(x=>tile(...x)).join("")+
      '</div><div class="section-title"><h2>Account & University</h2></div><div class="module-grid">'+
      [["profile","My Profile","Personal information and account details"],["university","My University","Join, create or select your university"],["search","Global Search","Search your permitted campus data"]].map(x=>tile(...x)).join("")+'</div>';
  }
  function install(){
    refreshShell();
    const originalGo=window.go;
    window.go=function(p){originalGo(p);setTimeout(()=>{if(p==="dashboard")restoreDashboard();refreshShell()},80)};
    const content=document.querySelector("#content");
    if(content && location.pathname==="/")restoreDashboard();
  }
  const timer=setInterval(()=>{if(document.querySelector(".shell")){clearInterval(timer);install()}},50);
})();