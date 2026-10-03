from datetime import datetime, timezone, timedelta
from secrets import token_urlsafe
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Q
from django_backend.legacy import models as m

def row(x): return {f.name:getattr(x,f.name) for f in x._meta.fields}
def rows(q): return [row(x) for x in q]
def member(iid,uid): return m.InstitutionMembership.objects.filter(institution_id=iid,user_id=uid,status="active").first()
def manager(iid,uid): 
    z=member(iid,uid); return bool(z and z.role in {"institution_owner","institution_admin","principal","department_admin"})
def can_manage(iid,uid): return manager(iid,uid)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def events(request):
    if request.method=="GET":
        ids=list(m.InstitutionMembership.objects.filter(user_id=request.user.id,status="active").values_list("institution_id",flat=True))
        return Response({"items":rows(m.Event.objects.filter(institution_id__in=ids).order_by("starts_at")[:100])})
    d=request.data or {};iid=d.get("institution_id")
    if not iid or not member(iid,request.user.id):return Response({"error":"membership_required"},403)
    title=str(d.get("title","")).strip()
    if not title:return Response({"error":"title_required"},400)
    x=m.Event.objects.create(institution_id=iid,organizer_id=request.user.id,title=title,description=d.get("description",""),starts_at=d.get("starts_at"),ends_at=d.get("ends_at"),location=d.get("location",""),event_type=d.get("event_type","event"),capacity=d.get("capacity"))
    return Response(row(x),201)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_event(request,eid):
    e=m.Event.objects.filter(pk=eid).first()
    if not e or not member(e.institution_id,request.user.id):return Response({"error":"membership_required"},403)
    if e.capacity and m.EventRegistration.objects.filter(event_id=eid).count()>=e.capacity:return Response({"error":"event_full"},409)
    if m.EventRegistration.objects.filter(event_id=eid,user_id=request.user.id).exists():return Response({"error":"already_registered"},409)
    x=m.EventRegistration.objects.create(event_id=eid,user_id=request.user.id,registered_at=datetime.now(timezone.utc));return Response(row(x),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def clubs(request):
    ids=list(m.InstitutionMembership.objects.filter(user_id=request.user.id,status="active").values_list("institution_id",flat=True))
    if request.method=="GET":return Response({"items":rows(m.Club.objects.filter(institution_id__in=ids).order_by("name"))})
    d=request.data or {};iid=d.get("institution_id")
    if not iid or not member(iid,request.user.id):return Response({"error":"membership_required"},403)
    title=str(d.get("name","")).strip()
    if not title:return Response({"error":"name_required"},400)
    x=m.Club.objects.create(institution_id=iid,name=title,description=d.get("description",""),logo_url=d.get("logo_url",""));m.ClubMembership.objects.create(club_id=x.id,user_id=request.user.id,role="admin");return Response(row(x),201)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def join_club(request,cid):
    x=m.Club.objects.filter(pk=cid).first()
    if not x or not member(x.institution_id,request.user.id):return Response({"error":"membership_required"},403)
    if m.ClubMembership.objects.filter(club_id=cid,user_id=request.user.id).exists():return Response({"error":"already_member"},409)
    return Response(row(m.ClubMembership.objects.create(club_id=cid,user_id=request.user.id,role="member")),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def documents(request):
    ids=list(m.InstitutionMembership.objects.filter(user_id=request.user.id,status="active").values_list("institution_id",flat=True))
    if request.method=="GET":return Response({"items":rows(m.Document.objects.filter(institution_id__in=ids).order_by("-created_at"))})
    d=request.data or {};iid=d.get("institution_id")
    if not iid or not member(iid,request.user.id):return Response({"error":"membership_required"},403)
    if not str(d.get("title","")).strip() or not str(d.get("url","")).strip():return Response({"error":"title_and_url_required"},400)
    x=m.Document.objects.create(institution_id=iid,owner_id=request.user.id,title=d["title"],category=d.get("category","general"),url=d["url"]);return Response(row(x),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def service_requests(request):
    if request.method=="GET":return Response({"items":rows(m.ServiceRequest.objects.filter(user_id=request.user.id))})
    d=request.data or {};iid=d.get("institution_id")
    if iid and not member(iid,request.user.id):return Response({"error":"membership_required"},403)
    typ=str(d.get("request_type","general")).strip()
    if not typ:return Response({"error":"request_type_required"},400)
    x=m.ServiceRequest.objects.create(user_id=request.user.id,institution_id=iid,request_type=typ,details=d.get("details",""));return Response(row(x),201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def fees(request):
    return Response({"items":rows(m.Fee.objects.filter(student_id=request.user.id))})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def fee_detail(request,fid):
    x=m.Fee.objects.filter(pk=fid).first()
    if not x or x.student_id!=request.user.id:return Response({"error":"forbidden"},403)
    return Response(row(x))

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def messages(request):
    if request.method=="GET":
        return Response({"items":rows(m.Message.objects.filter(Q(sender_id=request.user.id)|Q(recipient_id=request.user.id)).order_by("-created_at")[:100])})
    d=request.data or {};rid=d.get("recipient_id");body=str(d.get("body","")).strip()
    if not rid or not body:return Response({"error":"recipient_and_body_required"},400)
    if int(rid)==request.user.id:return Response({"error":"cannot_message_self"},400)
    if not m.User.objects.filter(pk=rid).exists():return Response({"error":"recipient_not_found"},404)
    viewer=list(m.InstitutionMembership.objects.filter(user_id=request.user.id,status="active").values_list("institution_id",flat=True))
    if not m.InstitutionMembership.objects.filter(user_id=rid,institution_id__in=viewer,status="active").exists():return Response({"error":"recipient_not_found"},404)
    x=m.Message.objects.create(sender_id=request.user.id,recipient_id=rid,body=body);m.Notification.objects.create(user_id=rid,kind="message",title="New message",body=f"You have a new message from user #{request.user.id}.");return Response(row(x),201)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def read_message(request,mid):
    x=m.Message.objects.filter(pk=mid,recipient_id=request.user.id).first()
    if not x:return Response({"error":"message_not_found"},404)
    x.read_at=datetime.now(timezone.utc);x.save();return Response(row(x))

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request,uid):
    if uid==request.user.id:
        p=m.UserProfile.objects.filter(user_id=uid).first();return Response({"profile":{f.name:getattr(p,f.name) for f in p._meta.fields if f.name not in {"id","user_id"}}})
    ids=list(m.InstitutionMembership.objects.filter(user_id=request.user.id,status="active").values_list("institution_id",flat=True))
    if not m.InstitutionMembership.objects.filter(user_id=uid,institution_id__in=ids,status="active").exists():return Response({"error":"user_not_found"},404)
    p=m.UserProfile.objects.filter(user_id=uid).first()
    if not p:return Response({"error":"user_not_found"},404)
    return Response({"profile":{f.name:getattr(p,f.name) for f in p._meta.fields if f.name not in {"id","user_id"}},"user_id":uid})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search(request):
    q=str(request.query_params.get("q","")).strip();like=q
    out=[]
    out += [{"type":"institution","id":x.id,"title":x.name} for x in m.Institution.objects.filter(name__icontains=like)[:10]]
    out += [{"type":"user","id":x.user_id,"title":x.full_name} for x in m.UserProfile.objects.filter(full_name__icontains=like)[:20]]
    out += [{"type":"group","id":x.id,"title":x.name} for x in m.Group.objects.filter(name__icontains=like)[:20]]
    return Response({"items":out})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    uid=request.user.id;en=list(m.Enrollment.objects.filter(student_id=uid,status="enrolled"));oids=[x.offering_id for x in en];ass=list(m.Assignment.objects.filter(offering_id__in=oids)[:10]);att=list(m.Attendance.objects.filter(student_id=uid));present=sum(x.status=="present" for x in att);unread=m.Notification.objects.filter(user_id=uid,is_read=False).count()
    return Response({"stats":{"courses":len(en),"upcoming_assignments":len(ass),"attendance_percent":round(present/len(att)*100,1) if att else 0,"unread_notifications":unread},"assignments":[{k:getattr(x,k) for k in ("id","title","description","due_at","max_score")} for x in ass]})

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def notifications(request):
    if request.method=="GET":return Response({"items":rows(m.Notification.objects.filter(user_id=request.user.id).order_by("-created_at")[:100])})
    return Response({"error":"method_not_supported"},405)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def notification_read(request,nid):
    x=m.Notification.objects.filter(pk=nid,user_id=request.user.id).first()
    if not x:return Response({"error":"forbidden"},403)
    x.is_read=True;x.save();return Response({"status":"read"})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    from werkzeug.security import check_password_hash,generate_password_hash
    d=request.data or {}
    if not check_password_hash(request.user.password_hash,d.get("current_password","")):return Response({"error":"invalid_current_password"},400)
    if len(d.get("new_password",""))<8:return Response({"error":"password_too_short"},400)
    u=m.User.objects.get(pk=request.user.id);u.password_hash=generate_password_hash(d["new_password"]);u.save();return Response({"status":"changed"})

@api_view(["GET","POST"])
@permission_classes([AllowAny])
def announcements(request,iid):
    if request.method=="GET":return Response({"items":rows(m.Announcement.objects.filter(institution_id=iid).order_by("-created_at"))})
    if not manager(iid,request.user.id):return Response({"error":"forbidden"},403)
    d=request.data or {};x=m.Announcement.objects.create(institution_id=iid,author_id=request.user.id,title=d.get("title",""),body=d.get("body",""),audience=d.get("audience","all"))
    for mm in m.InstitutionMembership.objects.filter(institution_id=iid,status="active"):m.Notification.objects.create(user_id=mm.user_id,kind="announcement",title=x.title,body=x.body)
    return Response(row(x),201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def event_ticket(request,eid):
    from django.db import transaction
    e=m.Event.objects.filter(pk=eid).first()
    if not e:return Response({"error":"event_not_found"},404)
    x=m.EventTicket.objects.filter(event_id=eid,user_id=request.user.id).first()
    if not x:x=m.EventTicket.objects.create(event_id=eid,user_id=request.user.id,code=token_urlsafe(24),checked_in=False,issued_at=datetime.now(timezone.utc))
    return Response(row(x))

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def checkin(request,code):
    x=m.EventTicket.objects.filter(code=code).first();e=m.Event.objects.filter(pk=x.event_id).first() if x else None
    if not x:return Response({"error":"ticket_not_found"},404)
    if not e or not can_manage(e.institution_id,request.user.id):return Response({"error":"forbidden"},403)
    x.checked_in=True;x.save();return Response({"status":"checked_in","ticket":row(x)})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def certificate(request,eid):
    e=m.Event.objects.filter(pk=eid).first()
    if not e or not can_manage(e.institution_id,request.user.id):return Response({"error":"forbidden"},403)
    uid=(request.data or {}).get("user_id")
    if not uid:return Response({"error":"user_id_required"},400)
    x=m.Certificate.objects.filter(event_id=eid,user_id=uid).first()
    if not x:x=m.Certificate.objects.create(event_id=eid,user_id=uid,certificate_no="CERT-"+token_urlsafe(10),title=e.title,issued_at=datetime.now(timezone.utc))
    return Response(row(x))

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def certificates(request):
    return Response({"items":rows(m.Certificate.objects.filter(user_id=request.user.id).order_by("-issued_at"))})

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def campus_services(request,iid=None):
    if request.method=="GET":
        ids=list(m.InstitutionMembership.objects.filter(user_id=request.user.id,status="active").values_list("institution_id",flat=True)) if iid is None else [iid]
        return Response({"items":rows(m.CampusService.objects.filter(institution_id__in=ids))})
    if not can_manage(iid,request.user.id):return Response({"error":"forbidden"},403)
    d=request.data or {};x=m.CampusService.objects.create(institution_id=iid,kind=d.get("kind","general"),name=d.get("name",""),description=d.get("description",""),location=d.get("location",""),contact=d.get("contact",""),hours=d.get("hours",""),status=d.get("status","active"));return Response(row(x),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def lost_found(request,iid=None):
    if request.method=="GET":
        ids=list(m.InstitutionMembership.objects.filter(user_id=request.user.id,status="active").values_list("institution_id",flat=True)) if iid is None else [iid]
        return Response({"items":rows(m.LostFoundItem.objects.filter(institution_id__in=ids).order_by("-created_at"))})
    if not member(iid,request.user.id):return Response({"error":"membership_required"},403)
    d=request.data or {};x=m.LostFoundItem.objects.create(institution_id=iid,reporter_id=request.user.id,item_type=d.get("item_type","lost"),title=d.get("title",""),description=d.get("description",""),location=d.get("location",""),contact=d.get("contact",""),status=d.get("status","open"));return Response(row(x),201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def emergency_contacts(request,iid):
    if not member(iid,request.user.id):return Response({"error":"forbidden"},403)
    return Response({"items":rows(m.EmergencyContact.objects.filter(institution_id=iid))})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def bus_routes(request,iid):
    if not member(iid,request.user.id):return Response({"error":"forbidden"},403)
    return Response({"items":rows(m.BusRoute.objects.filter(institution_id=iid,active=True))})

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def hostel(request,iid):
    if not member(iid,request.user.id):return Response({"error":"forbidden"},403)
    if request.method=="GET":return Response({"items":rows(m.HostelRoom.objects.filter(institution_id=iid))})
    d=request.data or {};x=m.StudentRequest.objects.create(user_id=request.user.id,institution_id=iid,request_type="hostel",details=str(d.get("details","")),tracking_no="HOSTEL-"+token_urlsafe(8),status="submitted",created_at=datetime.now(timezone.utc));return Response(row(x),201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def library_items(request,iid):
    if not member(iid,request.user.id):return Response({"error":"forbidden"},403)
    return Response({"items":rows(m.LibraryItem.objects.filter(institution_id=iid))})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_loans(request):return Response({"items":rows(m.LibraryLoan.objects.filter(user_id=request.user.id).order_by("-borrowed_at"))})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def borrow(request,item_id):
    x=m.LibraryItem.objects.filter(pk=item_id).first()
    if not x or x.available_copies<1:return Response({"error":"not_available"},409)
    if m.LibraryLoan.objects.filter(item_id=item_id,user_id=request.user.id,returned_at__isnull=True).exists():return Response({"error":"already_borrowed"},409)
    loan=m.LibraryLoan.objects.create(item_id=item_id,user_id=request.user.id,borrowed_at=datetime.now(timezone.utc),due_at=datetime.now(timezone.utc)+timedelta(days=14));x.available_copies-=1;x.save();return Response(row(loan),201)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def return_loan(request,lid):
    x=m.LibraryLoan.objects.filter(pk=lid,user_id=request.user.id,returned_at__isnull=True).first()
    if not x:return Response({"error":"loan_not_found"},404)
    x.returned_at=datetime.now(timezone.utc);x.save();item=m.LibraryItem.objects.filter(pk=x.item_id).first()
    if item:item.available_copies+=1;item.save()
    return Response({"status":"returned"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cafeteria(request,iid):
    if not member(iid,request.user.id):return Response({"error":"forbidden"},403)
    return Response({"items":rows(m.CafeteriaItem.objects.filter(institution_id=iid,available=True))})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def materials(request,oid):
    o=m.CourseOffering.objects.filter(pk=oid).first()
    if not o:return Response({"error":"offering_not_found"},404)
    if o.teacher_id!=request.user.id and not m.Enrollment.objects.filter(offering_id=oid,student_id=request.user.id,status="enrolled").exists():return Response({"error":"forbidden"},403)
    return Response({"items":rows(m.CourseMaterial.objects.filter(offering_id=oid).order_by("-created_at"))})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_material(request,oid):
    if not m.CourseOffering.objects.filter(pk=oid,teacher_id=request.user.id).exists():return Response({"error":"forbidden"},403)
    d=request.data or {}
    if not d.get("title") or not d.get("url"):return Response({"error":"title_and_url_required"},400)
    x=m.CourseMaterial.objects.create(offering_id=oid,teacher_id=request.user.id,title=d["title"],description=d.get("description",""),url=d["url"],mime_type=d.get("mime_type","application/octet-stream"),created_at=datetime.now(timezone.utc));return Response(row(x),201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def academic_calendar(request,iid):
    if not member(iid,request.user.id):return Response({"error":"forbidden"},403)
    return Response({"items":rows(m.AcademicCalendarItem.objects.filter(institution_id=iid).order_by("starts_at"))})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def advanced_request(request):
    d=request.data or {};iid=d.get("institution_id");x=m.StudentRequest.objects.create(user_id=request.user.id,institution_id=iid,request_type=d.get("request_type","general"),details=d.get("details",""),tracking_no="REQ-"+token_urlsafe(8),status="submitted",created_at=datetime.now(timezone.utc));return Response(row(x),201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def advanced_requests(request):return Response({"items":rows(m.StudentRequest.objects.filter(user_id=request.user.id).order_by("-created_at"))})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_push(request):
    d=request.data or {};token=str(d.get("token","")).strip()
    if not token:return Response({"error":"token_required"},400)
    x=m.PushDevice.objects.filter(token=token).first()
    if not x:x=m.PushDevice(token=token,user_id=request.user.id,platform=d.get("platform","expo"),active=True,created_at=datetime.now(timezone.utc))
    x.user_id=request.user.id;x.active=True;x.save();return Response(row(x))

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def unregister_push(request):
    token=str((request.data or {}).get("token","")).strip();m.PushDevice.objects.filter(user_id=request.user.id,token=token).update(active=False);return Response({"status":"disabled"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verification(request):
    x=m.UserVerification.objects.filter(user_id=request.user.id).first();return Response({"verified":bool(x and x.verified),"verified_at":x.verified_at.isoformat() if x and x.verified_at else None})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirm_verification(request):
    if not (request.data or {}).get("code"):return Response({"error":"code_required"},400)
    x=m.UserVerification.objects.filter(user_id=request.user.id).first()
    if not x:x=m.UserVerification(user_id=request.user.id,verified=True)
    x.verified=True;x.verified_at=datetime.now(timezone.utc);x.save();return Response({"verified":True,"verified_at":x.verified_at.isoformat()})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def announcement_read(request,aid):
    x=m.AnnouncementRead.objects.filter(announcement_id=aid,user_id=request.user.id).first()
    if not x:m.AnnouncementRead.objects.create(announcement_id=aid,user_id=request.user.id,read_at=datetime.now(timezone.utc))
    return Response({"status":"read"})
