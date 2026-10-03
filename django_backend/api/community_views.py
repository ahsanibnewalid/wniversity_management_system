from datetime import datetime, timezone
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
    x=member(iid,uid);return bool(x and x.role in {"institution_owner","institution_admin","principal","department_admin"})
def group_access(gid,uid):
    g=m.Group.objects.filter(pk=gid).first()
    return g and member(g.institution_id,uid) and m.GroupMembership.objects.filter(group_id=gid,user_id=uid,status="active").exists()

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def institution_groups(request,iid):
    if not member(iid,request.user.id):return Response({"error":"institution_membership_required"},403)
    return Response({"items":[{"id":g.id,"name":g.name,"type":g.group_type,"department_id":g.department_id,"session_id":g.session_id,"academic_year_id":g.academic_year_id} for g in m.Group.objects.filter(institution_id=iid).order_by("name")]})

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def groups(request):
    if request.method=="GET":
        ids=list(m.InstitutionMembership.objects.filter(user_id=request.user.id,status="active").values_list("institution_id",flat=True));return Response({"items":rows(m.Group.objects.filter(institution_id__in=ids))})
    d=request.data or {};iid=d.get("institution_id")
    if not manager(iid,request.user.id):return Response({"error":"forbidden"},403)
    x=m.Group.objects.create(institution_id=iid,department_id=d.get("department_id"),session_id=d.get("session_id"),academic_year_id=d.get("academic_year_id"),name=d.get("name",""),group_type=d.get("group_type","general"),description=d.get("description"),is_private=bool(d.get("is_private",False)))
    m.GroupMembership.objects.create(group_id=x.id,user_id=request.user.id,role="manager",status="active");return Response(row(x),201)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def join_group(request,gid):
    g=m.Group.objects.filter(pk=gid).first()
    if not g:return Response({"error":"group_not_found"},404)
    if not member(g.institution_id,request.user.id):return Response({"error":"institution_membership_required"},403)
    x=m.GroupMembership.objects.filter(group_id=gid,user_id=request.user.id).first()
    if not x:x=m.GroupMembership.objects.create(group_id=gid,user_id=request.user.id,role="member",status="active")
    return Response({"status":"active"})

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def posts(request,gid):
    if not group_access(gid,request.user.id):return Response({"error":"group_membership_required"},403)
    if request.method=="GET":
        return Response({"items":[{"id":x.id,"author_id":x.author_id,"type":x.post_type,"body":x.body,"created_at":x.created_at.isoformat()} for x in m.Post.objects.filter(group_id=gid).order_by("-created_at")[:50]]})
    body=str((request.data or {}).get("body","")).strip()
    if not body:return Response({"error":"body_required"},400)
    x=m.Post.objects.create(group_id=gid,author_id=request.user.id,post_type=(request.data or {}).get("post_type","post"),body=body,created_at=datetime.now(timezone.utc));return Response({"id":x.id},201)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def comment(request,pid):
    p=m.Post.objects.filter(pk=pid).first()
    if not p or not group_access(p.group_id,request.user.id):return Response({"error":"forbidden"},403)
    body=str((request.data or {}).get("body","")).strip()
    if not body:return Response({"error":"body_required"},400)
    x=m.Comment.objects.create(post_id=pid,author_id=request.user.id,body=body,created_at=datetime.now(timezone.utc));return Response({"status":"created","id":x.id},201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def feed(request,gid):
    return posts(request,gid)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reaction(request,pid):
    p=m.Post.objects.filter(pk=pid).first()
    if not p or not group_access(p.group_id,request.user.id):return Response({"error":"forbidden"},403)
    x=m.Reaction.objects.filter(post_id=pid,user_id=request.user.id).first()
    if not x:x=m.Reaction(post_id=pid,user_id=request.user.id)
    x.reaction=(request.data or {}).get("reaction","like");x.save();return Response({"status":"ok"})

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def attachments(request,pid):
    p=m.Post.objects.filter(pk=pid).first()
    if not p or not group_access(p.group_id,request.user.id):return Response({"error":"forbidden"},403)
    if request.method=="GET":return Response({"items":rows(m.PostAttachment.objects.filter(post_id=pid))})
    d=request.data or {};x=m.PostAttachment.objects.create(post_id=pid,name=d.get("name",""),url=d.get("url",""),mime_type=d.get("mime_type","application/octet-stream"));return Response(row(x),201)

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def polls(request,gid):
    if not group_access(gid,request.user.id):return Response({"error":"group_membership_required"},403)
    if request.method=="GET":
        post_ids=m.Post.objects.filter(group_id=gid).values_list("id",flat=True);ps=m.Poll.objects.filter(post_id__in=post_ids);out=[]
        for p in ps:
            d=row(p);d["options"]=rows(m.PollOption.objects.filter(poll_id=p.id));out.append(d)
        return Response({"items":out})
    d=request.data or {};post_id=d.get("post_id")
    if not post_id:return Response({"error":"post_id_required"},400)
    p=m.Post.objects.filter(pk=post_id,group_id=gid).first()
    if not p:return Response({"error":"post_not_found"},404)
    poll=m.Poll.objects.create(post_id=post_id,question=d.get("question",""))
    for i,label in enumerate(d.get("options",[])):m.PollOption.objects.create(poll_id=poll.id,label=label,position=i)
    return Response(row(poll),201)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def vote(request,pid):
    poll=m.Poll.objects.filter(pk=pid).first();oid=(request.data or {}).get("option_id")
    if not poll or not oid or not m.PollOption.objects.filter(pk=oid,poll_id=pid).exists():return Response({"error":"invalid_option"},400)
    if m.PollVote.objects.filter(option_id=oid,user_id=request.user.id).exists():return Response({"error":"already_voted"},409)
    x=m.PollVote.objects.create(option_id=oid,user_id=request.user.id);return Response(row(x),201)
