from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_backend.legacy import models as m

ROLES={"institution_owner":{"institution.manage","members.manage","academics.manage","content.manage","finance.manage","requests.manage","groups.manage","analytics.view"},"institution_admin":{"institution.manage","members.manage","academics.manage","content.manage","finance.manage","requests.manage","groups.manage","analytics.view"},"principal":{"institution.manage","members.manage","academics.manage","content.manage","requests.manage","groups.manage","analytics.view"},"department_admin":{"academics.manage","members.manage","content.manage","requests.manage","analytics.view"},"teacher":{"academics.teach","content.manage"},"media_manager":{"content.manage"},"class_representative":{"groups.manage","content.manage"},"student":set()}
def row(x):return {f.name:getattr(x,f.name) for f in x._meta.fields}
def mem(iid,uid):return m.InstitutionMembership.objects.filter(institution_id=iid,user_id=uid,status="active").first()
def perm(iid,uid,p):
    z=mem(iid,uid);inst=m.Institution.objects.filter(pk=iid).first()
    role="institution_owner" if inst and inst.owner_id==uid else (z.role if z else None)
    return p in ROLES.get(role,set())
def require(iid,uid,p):
    return perm(iid,uid,p)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def overview(request,iid):
    if not require(iid,request.user.id,"analytics.view"):return Response({"error":"forbidden"},403)
    return Response({"members":m.InstitutionMembership.objects.filter(institution_id=iid,status="active").count(),"pending_requests":m.JoinRequest.objects.filter(institution_id=iid,status="pending").count(),"departments":m.Department.objects.filter(institution_id=iid).count(),"groups":m.Group.objects.filter(institution_id=iid).count()})

@api_view(["GET","PATCH"])
@permission_classes([IsAuthenticated])
def institution_admin(request,iid):
    if not require(iid,request.user.id,"institution.manage"):return Response({"error":"forbidden"},403)
    x=m.Institution.objects.filter(pk=iid).first()
    if not x:return Response({"error":"institution_not_found"},404)
    if request.method=="PATCH":
        for k in ("name","kind","address","website","description"):
            if k in request.data:setattr(x,k,request.data[k])
        x.save()
    return Response(row(x))

@api_view(["GET","PATCH"])
@permission_classes([IsAuthenticated])
def members(request,iid,uid=None):
    if not require(iid,request.user.id,"members.manage"):return Response({"error":"forbidden"},403)
    if uid is not None:
        x=m.InstitutionMembership.objects.filter(institution_id=iid,user_id=uid).first()
        if not x:return Response({"error":"member_not_found"},404)
        if request.method=="PATCH":
            for k in ("role","status","student_id","program"):
                if k in request.data:setattr(x,k,request.data[k])
            x.save()
        return Response(row(x))
    return Response({"items":rows(m.InstitutionMembership.objects.filter(institution_id=iid))})

def rows(q):return [row(x) for x in q]
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def invite(request,iid):
    if not require(iid,request.user.id,"members.manage"):return Response({"error":"forbidden"},403)
    d=request.data or {};uid=d.get("user_id")
    if not uid or not m.User.objects.filter(pk=uid).exists():return Response({"error":"user_not_found"},404)
    x=m.InstitutionMembership.objects.filter(institution_id=iid,user_id=uid).first() or m.InstitutionMembership(institution_id=iid,user_id=uid)
    x.role=d.get("role","student");x.status="active";x.student_id=d.get("student_id");x.program=d.get("program");x.save();return Response(row(x),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def departments(request,iid):
    if request.method=="GET":return Response({"items":rows(m.Department.objects.filter(institution_id=iid).order_by("name"))})
    if not require(iid,request.user.id,"academics.manage"):return Response({"error":"forbidden"},403)
    d=request.data or {};x=m.Department.objects.create(institution_id=iid,name=d.get("name",""),code=d.get("code","").upper());return Response(row(x),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def sessions(request,iid):
    if not require(iid,request.user.id,"academics.manage"):return Response({"error":"forbidden"},403)
    did=(request.data or {}).get("department_id") if request.method=="POST" else None
    if request.method=="GET":
        deps=m.Department.objects.filter(institution_id=iid).values_list("id",flat=True);return Response({"items":rows(m.AcademicSession.objects.filter(department_id__in=deps))})
    x=m.AcademicSession.objects.create(department_id=did,name=(request.data or {}).get("name",""));return Response(row(x),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def years(request,iid):
    if not require(iid,request.user.id,"academics.manage"):return Response({"error":"forbidden"},403)
    if request.method=="GET":
        deps=m.Department.objects.filter(institution_id=iid).values_list("id",flat=True);sids=m.AcademicSession.objects.filter(department_id__in=deps).values_list("id",flat=True);return Response({"items":rows(m.AcademicYear.objects.filter(session_id__in=sids))})
    x=m.AcademicYear.objects.create(session_id=(request.data or {}).get("session_id"),name=(request.data or {}).get("name",""));return Response(row(x),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def admin_groups(request,iid):
    if request.method=="GET":return Response({"items":rows(m.Group.objects.filter(institution_id=iid))})
    if not require(iid,request.user.id,"groups.manage"):return Response({"error":"forbidden"},403)
    d=request.data or {};x=m.Group.objects.create(institution_id=iid,department_id=d.get("department_id"),session_id=d.get("session_id"),academic_year_id=d.get("academic_year_id"),name=d.get("name",""),group_type=d.get("group_type","general"),description=d.get("description"),is_private=bool(d.get("is_private",False)));return Response(row(x),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def requests(request,iid):
    if not require(iid,request.user.id,"requests.manage"):return Response({"error":"forbidden"},403)
    if request.method=="GET":return Response({"items":rows(m.JoinRequest.objects.filter(institution_id=iid).order_by("-created_at"))})
    return Response({"error":"use join-requests review"},405)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def permissions(request,iid):
    z=mem(iid,request.user.id)
    if not z:return Response({"error":"forbidden"},403)
    return Response({"role":z.role,"permissions":sorted(ROLES.get(z.role,set()))})

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def faculties(request,iid):
    if request.method=="GET":return Response({"items":rows(m.Faculty.objects.filter(institution_id=iid))})
    if not require(iid,request.user.id,"academics.manage"):return Response({"error":"forbidden"},403)
    d=request.data or {};return Response(row(m.Faculty.objects.create(institution_id=iid,name=d.get("name",""),code=d.get("code",""),description=d.get("description",""))),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def admin_programs(request,iid):
    if request.method=="GET":
        dids=m.Department.objects.filter(institution_id=iid).values_list("id",flat=True);return Response({"items":rows(m.Program.objects.filter(department_id__in=dids))})
    if not require(iid,request.user.id,"academics.manage"):return Response({"error":"forbidden"},403)
    d=request.data or {};return Response(row(m.Program.objects.create(department_id=d["department_id"],name=d.get("name",""),code=d.get("code",""),degree=d.get("degree",""),duration_years=d.get("duration_years",4))),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def admin_courses(request,iid):
    dids=m.Department.objects.filter(institution_id=iid).values_list("id",flat=True)
    if request.method=="GET":return Response({"items":rows(m.Course.objects.filter(department_id__in=dids))})
    if not require(iid,request.user.id,"academics.manage"):return Response({"error":"forbidden"},403)
    d=request.data or {};return Response(row(m.Course.objects.create(department_id=d["department_id"],code=d.get("code",""),title=d.get("title",""),credits=d.get("credits",3),description=d.get("description",""))),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def admin_events(request,iid):
    if request.method=="GET":return Response({"items":rows(m.Event.objects.filter(institution_id=iid))})
    if not require(iid,request.user.id,"content.manage"):return Response({"error":"forbidden"},403)
    d=request.data or {};return Response(row(m.Event.objects.create(institution_id=iid,organizer_id=request.user.id,title=d.get("title",""),description=d.get("description",""),starts_at=d.get("starts_at"),ends_at=d.get("ends_at"),location=d.get("location",""),event_type=d.get("event_type","event"),capacity=d.get("capacity"))),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def admin_clubs(request,iid):
    if request.method=="GET":return Response({"items":rows(m.Club.objects.filter(institution_id=iid))})
    if not require(iid,request.user.id,"content.manage"):return Response({"error":"forbidden"},403)
    d=request.data or {};return Response(row(m.Club.objects.create(institution_id=iid,name=d.get("name",""),description=d.get("description",""),logo_url=d.get("logo_url",""))),201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_service_requests(request,iid):
    if not require(iid,request.user.id,"requests.manage"):return Response({"error":"forbidden"},403)
    return Response({"items":rows(m.ServiceRequest.objects.filter(institution_id=iid).order_by("-created_at"))})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_fees(request,iid):
    if not require(iid,request.user.id,"finance.manage"):return Response({"error":"forbidden"},403)
    return Response({"items":rows(m.Fee.objects.filter(institution_id=iid))})
