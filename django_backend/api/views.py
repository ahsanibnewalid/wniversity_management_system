from django.http import JsonResponse
from django.db import connection
from django_backend.legacy.models import User,UserProfile,AuthToken,Institution,InstitutionMembership,JoinRequest
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from werkzeug.security import generate_password_hash,check_password_hash
from secrets import token_urlsafe\nfrom django.utils import timezone

def healthz(request):
    try:
        with connection.cursor() as c: c.execute("SELECT 1"); c.fetchone()
        return JsonResponse({"status":"ok","database":"ok"})
    except Exception: return JsonResponse({"status":"error","database":"unavailable"},status=503)

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    d=request.data or {}; email=str(d.get("email","")).strip().lower(); password=str(d.get("password","")); name=str(d.get("full_name","")).strip(); username=str(d.get("username","")).strip().lower()
    if not all((email,password,name,username)): return Response({"error":"email,password,full_name,username_required"},status=400)
    if User.objects.filter(email=email).exists() or UserProfile.objects.filter(username=username).exists(): return Response({"error":"email_or_username_exists"},status=409)
    u=User.objects.create(email=email,password_hash=generate_password_hash(password),created_at=timezone.now())
    UserProfile.objects.create(user_id=u.id,full_name=name,username=username,is_complete=False)
    return Response({"user_id":u.id,"profile_complete":False},status=201)

@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    d=request.data or {}; u=User.objects.filter(email=str(d.get("email","")).strip().lower()).first()
    if not u or not check_password_hash(u.password_hash,str(d.get("password",""))): return Response({"error":"invalid_credentials"},status=401)
    t=AuthToken.objects.create(token=token_urlsafe(48),user_id=u.id,created_at=None,revoked=False)
    p=UserProfile.objects.filter(user_id=u.id).first()
    return Response({"access_token":t.token,"token_type":"Bearer","user_id":u.id,"profile_complete":bool(p and p.is_complete)})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    p=UserProfile.objects.filter(user_id=request.user.id).first()
    return Response({"id":request.user.id,"email":request.user.email,"profile":{"full_name":p.full_name if p else "","username":p.username if p else "","is_complete":bool(p and p.is_complete)}})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    AuthToken.objects.filter(token=request.auth,user_id=request.user.id).update(revoked=True)
    return Response({"status":"logged_out"})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_all(request):
    AuthToken.objects.filter(user_id=request.user.id,revoked=False).update(revoked=True)
    return Response({"status":"logged_out_all"})

@api_view(["GET"])
@permission_classes([AllowAny])
def institutions(request):
    return Response({"items":list(Institution.objects.order_by("name").values("id","name","slug","kind","address"))})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_institutions(request):
    ms=InstitutionMembership.objects.filter(user_id=request.user.id,status="active"); ids=[m.institution_id for m in ms]; by={x.id:x for x in Institution.objects.filter(id__in=ids)}; items=[]
    for m in ms:
        i=by.get(m.institution_id)
        if i: items.append({"id":i.id,"name":i.name,"slug":i.slug,"kind":i.kind,"address":i.address,"role":m.role,"student_id":m.student_id,"program":m.program})
    return Response({"items":items})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_institution(request):
    d=request.data or {}; p=UserProfile.objects.filter(user_id=request.user.id).first()
    if not p or not p.is_complete: return Response({"error":"complete_profile_first"},status=403)
    if not d.get("name") or not d.get("slug"): return Response({"error":"name_and_slug_required"},status=400)
    from django.utils import timezone
    i=Institution.objects.create(name=str(d["name"]).strip(),slug=str(d["slug"]).strip().lower(),kind=d.get("kind","university"),address=d.get("address"),website=d.get("website"),description=d.get("description"),owner_id=request.user.id)
    InstitutionMembership.objects.create(institution_id=i.id,user_id=request.user.id,role="institution_owner",status="active")
    return Response({"id":i.id,"slug":i.slug},status=201)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def join_institution(request,iid):
    p=UserProfile.objects.filter(user_id=request.user.id).first()
    if not p or not p.is_complete: return Response({"error":"complete_profile_first"},status=403)
    d=request.data or {}; required=("department_id","student_id","program","session","academic_year")
    if not all(d.get(k) for k in required): return Response({"error":"academic_details_required"},status=400)
    if not Institution.objects.filter(pk=iid).exists(): return Response({"error":"institution_not_found"},status=404)
    if JoinRequest.objects.filter(institution_id=iid,user_id=request.user.id,status="pending").exists(): return Response({"error":"request_pending"},status=409)
    r=JoinRequest.objects.create(institution_id=iid,user_id=request.user.id,department_id=d["department_id"],student_id=d["student_id"],program=d["program"],session=d["session"],academic_year=d["academic_year"],note=d.get("note"),status="pending",created_at=timezone.now())
    return Response({"request_id":r.id,"status":"pending"},status=201)

@api_view(["GET","PUT"])
@permission_classes([IsAuthenticated])
def profile(request):
    p=UserProfile.objects.filter(user_id=request.user.id).first()
    if not p: return Response({"error":"profile_not_found"},status=404)
    if request.method=="GET": return Response({f.name:getattr(p,f.name) for f in p._meta.fields})
    d=request.data or {}
    for k in ("full_name","phone","address","bio","profile_photo_url","institution_text","department","program","student_id"):
        if k in d: setattr(p,k,d[k])
    if "username" in d:
        name=str(d["username"]).strip().lower()
        if name and name!=p.username and UserProfile.objects.filter(username=name).exists(): return Response({"error":"username_exists"},status=409)
        if name: p.username=name
    p.is_complete=all(bool(getattr(p,k)) for k in ("full_name","username","phone","address","institution_text","department","program","student_id"))
    p.save()
    return Response({"status":"updated","profile_complete":p.is_complete})
