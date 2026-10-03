from datetime import datetime, timezone, timedelta
from secrets import token_urlsafe
from django.db import transaction
from django.http import FileResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django_backend.legacy import models as m

def row(obj):
    return {f.name:getattr(obj,f.name) for f in obj._meta.fields}

def rows(qs):
    return [row(x) for x in qs]

def auth_required(view):
    view=permission_classes([IsAuthenticated])(view)
    return api_view(["GET","POST","PUT","PATCH","DELETE"])(view)

def member(iid,uid):
    return m.InstitutionMembership.objects.filter(institution_id=iid,user_id=uid,status="active").first()

def manager(iid,uid):
    x=member(iid,uid)
    return bool(x and x.role in {"institution_owner","institution_admin","principal","department_admin"})

def teacher(oid,uid):
    return m.CourseOffering.objects.filter(pk=oid,teacher_id=uid).exists()

# ---------- Academics ----------

@api_view(["GET","POST"])
@permission_classes([AllowAny])
def faculties(request,iid):
    if request.method=="GET":
        return Response({"items":rows(m.Faculty.objects.filter(institution_id=iid))})
    if not manager(iid,request.user.id): return Response({"error":"forbidden"},403)
    d=request.data or {}
    x=m.Faculty.objects.create(institution_id=iid,name=d.get("name",""),code=d.get("code",""),description=d.get("description",""))
    return Response(row(x),201)

@api_view(["GET","POST"])
@permission_classes([AllowAny])
def programs(request,did):
    dep=m.Department.objects.filter(pk=did).first()
    if not dep:return Response({"error":"department_not_found"},404)
    if request.method=="GET":return Response({"items":rows(m.Program.objects.filter(department_id=did))})
    if not manager(dep.institution_id,request.user.id):return Response({"error":"forbidden"},403)
    d=request.data or {};x=m.Program.objects.create(department_id=did,name=d.get("name",""),code=d.get("code",""),degree=d.get("degree",""),duration_years=d.get("duration_years",4))
    return Response(row(x),201)

@api_view(["GET","POST"])
@permission_classes([AllowAny])
def courses(request,did):
    dep=m.Department.objects.filter(pk=did).first()
    if not dep:return Response({"error":"department_not_found"},404)
    if request.method=="GET":return Response({"items":rows(m.Course.objects.filter(department_id=did))})
    if not manager(dep.institution_id,request.user.id):return Response({"error":"forbidden"},403)
    d=request.data or {};x=m.Course.objects.create(department_id=did,code=d.get("code",""),title=d.get("title",""),credits=float(d.get("credits",3)),description=d.get("description",""))
    return Response(row(x),201)

@api_view(["GET","POST"])
@permission_classes([AllowAny])
def offerings(request,cid):
    course=m.Course.objects.filter(pk=cid).first()
    if not course:return Response({"error":"course_not_found"},404)
    if request.method=="GET":return Response({"items":rows(m.CourseOffering.objects.filter(course_id=cid))})
    dep=m.Department.objects.filter(pk=course.department_id).first()
    if not dep or not manager(dep.institution_id,request.user.id):return Response({"error":"forbidden"},403)
    d=request.data or {};x=m.CourseOffering.objects.create(course_id=cid,semester_id=d.get("semester_id"),teacher_id=d.get("teacher_id") or request.user.id,section=d.get("section","A"),room=d.get("room",""),capacity=d.get("capacity",50),status=d.get("status","open"))
    return Response(row(x),201)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enroll(request,oid):
    o=m.CourseOffering.objects.filter(pk=oid).first()
    if not o:return Response({"error":"offering_not_found"},404)
    sid=int((request.data or {}).get("student_id",request.user.id))
    if sid!=request.user.id:return Response({"error":"forbidden"},403)
    course=m.Course.objects.filter(pk=o.course_id).first();dep=m.Department.objects.filter(pk=course.department_id).first() if course else None
    if not dep or not member(dep.institution_id,sid):return Response({"error":"institution_membership_required"},403)
    if o.status!="open":return Response({"error":"offering_closed"},409)
    if o.capacity and m.Enrollment.objects.filter(offering_id=oid,status="enrolled").count()>=o.capacity:return Response({"error":"offering_full"},409)
    if m.Enrollment.objects.filter(offering_id=oid,student_id=sid).exists():return Response({"error":"already_enrolled"},409)
    x=m.Enrollment.objects.create(offering_id=oid,student_id=sid,status="enrolled",enrolled_at=datetime.now(timezone.utc))
    return Response(row(x),201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_enrollments(request):
    items=[]
    for x in m.Enrollment.objects.filter(student_id=request.user.id,status="enrolled"):
        d=row(x);o=m.CourseOffering.objects.filter(pk=x.offering_id).first();c=m.Course.objects.filter(pk=o.course_id).first() if o else None
        if o:d.update(section=o.section,room=o.room,teacher_id=o.teacher_id,semester_id=o.semester_id)
        if c:d.update(course_id=c.id,course_code=c.code,course_title=c.title,credits=c.credits)
        items.append(d)
    return Response({"items":items})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def attendance(request,oid):
    if not teacher(oid,request.user.id):return Response({"error":"forbidden"},403)
    d=request.data or {};day=datetime.fromisoformat(d.get("date",datetime.now().date().isoformat())).date()
    allowed={x.student_id for x in m.Enrollment.objects.filter(offering_id=oid,status="enrolled")}
    for r in d.get("records",[]):
        sid=int(r["student_id"])
        if sid not in allowed:return Response({"error":"student_not_enrolled"},400)
        st=str(r.get("status","present"))
        if st not in {"present","absent","late","excused"}:return Response({"error":"invalid_attendance_status"},400)
        x=m.Attendance.objects.filter(offering_id=oid,student_id=sid,date=day).first()
        if not x:x=m.Attendance(offering_id=oid,student_id=sid,date=day)
        x.status=st;x.note=r.get("note","");x.save()
    return Response({"status":"saved"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_attendance(request):
    return Response({"items":rows(m.Attendance.objects.filter(student_id=request.user.id).order_by("-date"))})

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def assignments(request,oid):
    o=m.CourseOffering.objects.filter(pk=oid).first()
    if not o:return Response({"error":"offering_not_found"},404)
    if request.method=="GET":return Response({"items":rows(m.Assignment.objects.filter(offering_id=oid))})
    if o.teacher_id!=request.user.id:return Response({"error":"forbidden"},403)
    d=request.data or {};title=str(d.get("title","")).strip()
    if not title:return Response({"error":"title_required"},400)
    x=m.Assignment.objects.create(offering_id=oid,title=title,description=d.get("description",""),due_at=d.get("due_at"),max_score=float(d.get("max_score",100)),attachment_url=d.get("attachment_url",""))
    return Response(row(x),201)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_assignment(request,aid):
    a=m.Assignment.objects.filter(pk=aid).first()
    if not a:return Response({"error":"assignment_not_found"},404)
    if not m.Enrollment.objects.filter(offering_id=a.offering_id,student_id=request.user.id,status="enrolled").exists():return Response({"error":"enrollment_required"},403)
    x=m.Submission.objects.filter(assignment_id=aid,student_id=request.user.id).first()
    if x and x.score is not None:return Response({"error":"graded_submission_locked"},409)
    d=request.data or {}
    if not x:x=m.Submission(assignment_id=aid,student_id=request.user.id)
    x.body=d.get("body","");x.file_url=d.get("file_url","");x.submitted_at=datetime.now(timezone.utc);x.save()
    return Response(row(x),201)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def grade_submission(request,sid):
    x=m.Submission.objects.filter(pk=sid).first();a=m.Assignment.objects.filter(pk=x.assignment_id).first() if x else None
    if not x or not a or not teacher(a.offering_id,request.user.id):return Response({"error":"forbidden"},403)
    x.score=request.data.get("score");x.feedback=request.data.get("feedback","");x.save();return Response(row(x))

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def exams(request,oid):
    if request.method=="GET":return Response({"items":rows(m.Exam.objects.filter(offering_id=oid))})
    if not teacher(oid,request.user.id):return Response({"error":"forbidden"},403)
    d=request.data or {};x=m.Exam.objects.create(offering_id=oid,title=d.get("title",""),exam_type=d.get("exam_type","final"),exam_at=d.get("exam_at"),room=d.get("room",""));return Response(row(x),201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def results(request):
    return Response({"items":rows(m.Result.objects.filter(student_id=request.user.id,published=True))})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def transcript(request):
    rs=list(m.Result.objects.filter(student_id=request.user.id,published=True));credits=sum(x.credits for x in rs);points=sum(x.credits*x.grade_point for x in rs)
    return Response({"results":[row(x) for x in rs],"credits":credits,"cgpa":round(points/credits,2) if credits else 0})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def student_results(request,sid):
    d=request.data or {};c=m.Course.objects.filter(pk=d.get("course_id")).first();dep=m.Department.objects.filter(pk=c.department_id).first() if c else None
    if not dep or not manager(dep.institution_id,request.user.id):return Response({"error":"forbidden"},403)
    x=m.Result.objects.create(student_id=sid,course_id=c.id,semester_id=d.get("semester_id"),grade=d["grade"],grade_point=d.get("grade_point",0),credits=d.get("credits",0),published=d.get("published",False));return Response(row(x),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def timetable(request,oid):
    if request.method=="GET":return Response({"items":rows(m.TimetableEntry.objects.filter(offering_id=oid))})
    if not teacher(oid,request.user.id):return Response({"error":"forbidden"},403)
    d=request.data or {};x=m.TimetableEntry.objects.create(offering_id=oid,weekday=d.get("weekday",0),start_time=d.get("start_time","09:00"),end_time=d.get("end_time","10:00"),room=d.get("room",""));return Response(row(x),201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_timetable(request):
    ids=list(m.Enrollment.objects.filter(student_id=request.user.id,status="enrolled").values_list("offering_id",flat=True));items=[]
    for x in m.TimetableEntry.objects.filter(offering_id__in=ids).order_by("weekday","start_time"):
        d=row(x);o=m.CourseOffering.objects.filter(pk=x.offering_id).first();c=m.Course.objects.filter(pk=o.course_id).first() if o else None
        d.update(course_code=c.code if c else "",course_title=c.title if c else "",section=o.section if o else "",teacher_id=o.teacher_id if o else None);items.append(d)
    return Response({"items":items})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def semester_results(request,semester_id):
    return Response({"items":rows(m.Result.objects.filter(student_id=request.user.id,semester_id=semester_id,published=True))})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def course_registration(request):
    ids=list(m.InstitutionMembership.objects.filter(user_id=request.user.id,status="active").values_list("institution_id",flat=True))
    depids=list(m.Department.objects.filter(institution_id__in=ids).values_list("id",flat=True))
    items=[]
    for o in m.CourseOffering.objects.filter(course_id__in=m.Course.objects.filter(department_id__in=depids).values("id"),status="open"):
        c=m.Course.objects.filter(pk=o.course_id).first();en=m.Enrollment.objects.filter(offering_id=o.id,student_id=request.user.id,status="enrolled").exists()
        d=row(o);d.update(course_code=c.code if c else "",course_title=c.title if c else "",credits=c.credits if c else 0,enrolled=en);items.append(d)
    return Response({"items":items})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def academic_summary(request):
    uid=request.user.id;en=list(m.Enrollment.objects.filter(student_id=uid,status="enrolled"));oids=[x.offering_id for x in en]
    ass=list(m.Assignment.objects.filter(offering_id__in=oids));submitted=set(m.Submission.objects.filter(student_id=uid).values_list("assignment_id",flat=True))
    rs=list(m.Result.objects.filter(student_id=uid,published=True));credits=sum(x.credits for x in rs);points=sum(x.credits*x.grade_point for x in rs)
    att=list(m.Attendance.objects.filter(student_id=uid));attendance=round(100*sum(x.status=="present" for x in att)/len(att),1) if att else 0
    return Response({"courses":len(en),"assignments":len([x for x in ass if x.id not in submitted]),"attendance":attendance,"credits":credits,"cgpa":round(points/credits,2) if credits else 0})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def assignment_mine(request,aid):
    x=m.Submission.objects.filter(assignment_id=aid,student_id=request.user.id).first();return Response({"submission":row(x) if x else None})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def offering_submissions(request,oid):
    if not teacher(oid,request.user.id):return Response({"error":"forbidden"},403)
    aids=m.Assignment.objects.filter(offering_id=oid).values_list("id",flat=True);return Response({"items":rows(m.Submission.objects.filter(assignment_id__in=aids).order_by("-submitted_at"))})
