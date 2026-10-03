from datetime import datetime,timezone
from flask import request,jsonify
from backend.core import db,UserProfile,Institution,Group,User,InstitutionMembership,GroupMembership
from backend.core import Notification,Department,MANAGERS
from backend.api import login_required,institution_manager
from backend.academic import Course,CourseOffering,Enrollment,teacher_can_access_offering
class Message(db.Model):
    id=db.Column(db.Integer,primary_key=True);sender_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False);recipient_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False);body=db.Column(db.Text,nullable=False);read_at=db.Column(db.DateTime(timezone=True));created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class CommunicationConversation(db.Model):
    __tablename__="communication_conversations"
    id=db.Column(db.Integer,primary_key=True)
    institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False,index=True)
    kind=db.Column(db.String(30),nullable=False)
    title=db.Column(db.String(200),nullable=False,default="")
    created_by=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    course_offering_id=db.Column(db.Integer,db.ForeignKey("course_offering.id",ondelete="CASCADE"))
    department_id=db.Column(db.Integer,db.ForeignKey("departments.id",ondelete="CASCADE"))
    official_only=db.Column(db.Boolean,default=False,nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)

class CommunicationMember(db.Model):
    __tablename__="communication_members"
    id=db.Column(db.Integer,primary_key=True)
    conversation_id=db.Column(db.Integer,db.ForeignKey("communication_conversations.id",ondelete="CASCADE"),nullable=False,index=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True)
    last_read_at=db.Column(db.DateTime(timezone=True))
    muted=db.Column(db.Boolean,default=False,nullable=False)
    archived=db.Column(db.Boolean,default=False,nullable=False)
    pinned=db.Column(db.Boolean,default=False,nullable=False)
    joined_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
    __table_args__=(db.UniqueConstraint("conversation_id","user_id",name="uq_communication_member"),)

class CommunicationMessage(db.Model):
    __tablename__="communication_messages"
    id=db.Column(db.Integer,primary_key=True)
    conversation_id=db.Column(db.Integer,db.ForeignKey("communication_conversations.id",ondelete="CASCADE"),nullable=False,index=True)
    sender_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    body=db.Column(db.Text,nullable=False,default="")
    parent_id=db.Column(db.Integer,db.ForeignKey("communication_messages.id",ondelete="CASCADE"))
    attachment_url=db.Column(db.String(1000))
    attachment_name=db.Column(db.String(255))
    attachment_type=db.Column(db.String(100))
    official=db.Column(db.Boolean,default=False,nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False,index=True)

class CommunicationReaction(db.Model):
    __tablename__="communication_reactions"
    id=db.Column(db.Integer,primary_key=True)
    message_id=db.Column(db.Integer,db.ForeignKey("communication_messages.id",ondelete="CASCADE"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    reaction=db.Column(db.String(24),nullable=False)
    __table_args__=(db.UniqueConstraint("message_id","user_id","reaction",name="uq_communication_reaction"),)

class CommunicationReport(db.Model):
    __tablename__="communication_reports"
    id=db.Column(db.Integer,primary_key=True)
    message_id=db.Column(db.Integer,db.ForeignKey("communication_messages.id",ondelete="CASCADE"),nullable=False)
    reporter_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    reason=db.Column(db.String(80),nullable=False)
    details=db.Column(db.Text)
    status=db.Column(db.String(20),default="open",nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)

class CommunicationBlock(db.Model):
    __tablename__="communication_blocks"
    id=db.Column(db.Integer,primary_key=True)
    institution_id=db.Column(db.Integer,db.ForeignKey("institutions.id",ondelete="CASCADE"),nullable=False)
    blocker_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    blocked_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
    __table_args__=(db.UniqueConstraint("institution_id","blocker_id","blocked_id",name="uq_communication_block"),)

def data(x):return {c.name:getattr(x,c.name) for c in x.__table__.columns}

def active_membership(institution_id,user_id):
    return InstitutionMembership.query.filter_by(
        institution_id=institution_id,user_id=user_id,status="active"
    ).first()

def conversation_member(conversation_id,user_id):
    membership=CommunicationMember.query.filter_by(
        conversation_id=conversation_id,user_id=user_id
    ).first()
    conversation=db.session.get(CommunicationConversation,conversation_id)
    if not membership or not conversation or not active_membership(conversation.institution_id,user_id):
        return None
    return membership

def can_moderate(conversation,user):
    if institution_manager(conversation.institution_id):
        return True
    if conversation.kind=="course" and conversation.course_offering_id:
        return teacher_can_access_offering(
            db.session.get(CourseOffering,conversation.course_offering_id),user.id
        )
    return False

def can_post(conversation,user):
    if conversation.official_only:
        return can_moderate(conversation,user)
    return True

def message_data(message,user_id):
    author=db.session.get(UserProfile,message.sender_id)
    reactions=CommunicationReaction.query.filter_by(message_id=message.id).all()
    reaction_types={reaction.reaction for reaction in reactions}
    return {
        **data(message),
        "author_name":author.full_name if author else "Campus member",
        "reactions":[{"reaction":reaction,"count":sum(x.reaction==reaction for x in reactions),"reacted":any(x.user_id==user_id and x.reaction==reaction for x in reactions)} for reaction in sorted(reaction_types)],
        "reply_count":CommunicationMessage.query.filter_by(parent_id=message.id).count(),
    }

def register(app):
    @app.get("/api/v1/communications/catalog")
    @login_required
    def communication_catalog():
        institution_id=request.args.get("institution_id",type=int)
        if not institution_id or not active_membership(institution_id,request.current_user.id):
            return jsonify(error="institution_membership_required"),403
        offerings=(db.session.query(CourseOffering,Course)
            .join(Course,Course.id==CourseOffering.course_id)
            .join(Department,Department.id==Course.department_id)
            .filter(Department.institution_id==institution_id,CourseOffering.status=="open")
            .all())
        return jsonify(
            departments=[{"id":item.id,"name":item.name,"code":item.code}
                for item in Department.query.filter_by(institution_id=institution_id).order_by(Department.name).all()],
            courses=[{"id":offering.id,"course_code":course.code,"course_title":course.title,
                      "section":offering.section}
                for offering,course in offerings],
        )

    @app.patch("/api/v1/profile")
    @login_required
    def profile():
        p=request.current_user.profile;d=request.get_json() or {}
        for k in ("full_name","phone","address","bio","profile_photo_url","institution_text","department","program","student_id"):
            if k in d:setattr(p,k,d[k])
        db.session.commit();return jsonify(profile={c.name:getattr(p,c.name) for c in p.__table__.columns if c.name not in ("id","user_id")})
    @app.get("/api/v1/messages")
    @login_required
    def messages():return jsonify(items=[data(x) for x in Message.query.filter((Message.sender_id==request.current_user.id)|(Message.recipient_id==request.current_user.id)).order_by(Message.created_at.desc()).limit(100).all()])
    @app.post("/api/v1/messages")
    @login_required
    def send():
        d=request.get_json(silent=True) or {};body=str(d.get("body","")).strip()
        try:recipient_id=int(d.get("recipient_id"))
        except (TypeError,ValueError):return jsonify(error="recipient_and_body_required"),400
        if not body:return jsonify(error="recipient_and_body_required"),400
        if len(body)>10000:return jsonify(error="message_too_long"),400
        if recipient_id==request.current_user.id:return jsonify(error="cannot_message_self"),400
        from backend.core import User,Notification
        recipient=db.session.get(User,recipient_id)
        if not recipient:return jsonify(error="recipient_not_found"),404
        viewer_ids=[m.institution_id for m in InstitutionMembership.query.filter_by(user_id=request.current_user.id,status="active").all()]
        if not InstitutionMembership.query.filter(InstitutionMembership.user_id==recipient.id,InstitutionMembership.institution_id.in_(viewer_ids),InstitutionMembership.status=="active").first():return jsonify(error="recipient_not_found"),404
        if viewer_ids and CommunicationBlock.query.filter(
            CommunicationBlock.institution_id.in_(viewer_ids),
            ((CommunicationBlock.blocker_id==request.current_user.id)&(CommunicationBlock.blocked_id==recipient.id))|
            ((CommunicationBlock.blocker_id==recipient.id)&(CommunicationBlock.blocked_id==request.current_user.id)),
        ).first():return jsonify(error="direct_messages_unavailable"),403
        x=Message(sender_id=request.current_user.id,recipient_id=recipient.id,body=body);db.session.add(x)
        db.session.add(Notification(user_id=recipient.id,kind="message",title="New message",body=f"You have a new message from user #{request.current_user.id}."))
        db.session.commit();return jsonify(data(x)),201

    @app.post("/api/v1/messages/<int:mid>/read")
    @login_required
    def read_message(mid):
        x=db.session.get(Message,mid)
        if not x or x.recipient_id!=request.current_user.id:return jsonify(error="message_not_found"),404
        x.read_at=datetime.now(timezone.utc);db.session.commit();return jsonify(data(x))

    @app.get("/api/v1/profile")
    @login_required
    def get_profile():
        p=request.current_user.profile
        return jsonify(profile={c.name:getattr(p,c.name) for c in p.__table__.columns if c.name not in ("id","user_id")})
    @app.get("/api/v1/users/<int:user_id>/profile")
    @login_required
    def user_profile(user_id):
        if user_id == request.current_user.id:
            return jsonify(profile={c.name:getattr(request.current_user.profile,c.name) for c in request.current_user.profile.__table__.columns if c.name not in ("id","user_id")})
        viewer_ids=[m.institution_id for m in InstitutionMembership.query.filter_by(user_id=request.current_user.id,status="active").all()]
        shared=InstitutionMembership.query.filter(InstitutionMembership.user_id==user_id,InstitutionMembership.institution_id.in_(viewer_ids),InstitutionMembership.status=="active").first()
        if not shared:return jsonify(error="user_not_found"),404
        user=db.session.get(User,user_id)
        if not user:return jsonify(error="user_not_found"),404
        p=user.profile
        return jsonify(profile={c.name:getattr(p,c.name) for c in p.__table__.columns if c.name not in ("id","user_id")},user_id=user.id)

    @app.get("/api/v1/search")
    @login_required
    def search():
        q=request.args.get("q","").strip();like=f"%{q}%";out=[]
        institution_ids=[m.institution_id for m in InstitutionMembership.query.filter_by(user_id=request.current_user.id,status="active").all()]
        shared_user_ids=db.session.query(InstitutionMembership.user_id).filter(
            InstitutionMembership.institution_id.in_(institution_ids),
            InstitutionMembership.status=="active"
        ).distinct() if institution_ids else []
        visible_group_ids=db.session.query(GroupMembership.group_id).filter(
            GroupMembership.user_id==request.current_user.id,
            GroupMembership.status.in_(("active","invited"))
        )
        out += [{"type":"institution","id":x.id,"title":x.name} for x in Institution.query.filter(Institution.name.ilike(like)).limit(10)]
        if institution_ids:
            out += [{"type":"user","id":x.user_id,"title":x.full_name} for x in UserProfile.query.filter(
                UserProfile.user_id.in_(shared_user_ids),UserProfile.full_name.ilike(like)
            ).limit(20)]
            out += [{"type":"group","id":x.id,"title":x.name} for x in Group.query.filter(
                Group.institution_id.in_(institution_ids),Group.name.ilike(like),
                (Group.is_private.is_(False)) | Group.id.in_(visible_group_ids)
            ).limit(20)]
        return jsonify(items=out)

    @app.get("/api/v1/communications/conversations")
    @login_required
    def communication_conversations():
        uid=request.current_user.id
        membership_query=CommunicationMember.query.filter_by(user_id=uid)
        if request.args.get("archived","false").lower() not in {"1","true","yes"}:
            membership_query=membership_query.filter_by(archived=False)
        memberships=membership_query.all()
        result=[]
        for membership in memberships:
            conversation=db.session.get(CommunicationConversation,membership.conversation_id)
            if not conversation or not active_membership(conversation.institution_id,uid):
                continue
            latest=CommunicationMessage.query.filter_by(conversation_id=conversation.id).order_by(CommunicationMessage.created_at.desc()).first()
            unread=CommunicationMessage.query.filter(
                CommunicationMessage.conversation_id==conversation.id,
                CommunicationMessage.sender_id!=uid,
                CommunicationMessage.created_at>=(membership.last_read_at or membership.joined_at),
            ).count()
            others=CommunicationMember.query.filter(
                CommunicationMember.conversation_id==conversation.id,
                CommunicationMember.user_id!=uid,
            ).all()
            names=[]
            for other in others[:10]:
                profile=db.session.get(UserProfile,other.user_id)
                if profile:names.append(profile.full_name)
            result.append({
                **data(conversation),
                "membership":data(membership),
                "unread_count":unread,
                "participant_names":names,
                "last_message":message_data(latest,uid) if latest else None,
            })
        result.sort(key=lambda item:(not item["membership"]["pinned"],-(item["last_message"]["created_at"].timestamp() if item["last_message"] else 0)))
        return jsonify(items=result)

    @app.post("/api/v1/communications/conversations")
    @login_required
    def create_communication_conversation():
        payload=request.get_json(silent=True) or {}
        uid=request.current_user.id
        kind=str(payload.get("kind","")).strip().lower()
        title=str(payload.get("title","")).strip()[:200]
        try:
            institution_id=int(payload.get("institution_id"))
        except (TypeError,ValueError):
            return jsonify(error="institution_id_required"),400
        if kind not in {"direct","group","course","department","institution","support"}:
            return jsonify(error="invalid_conversation_type"),400
        if "official_only" in payload and not isinstance(payload["official_only"],bool):
            return jsonify(error="official_only_must_be_boolean"),400
        if not active_membership(institution_id,uid):
            return jsonify(error="institution_membership_required"),403

        participant_ids={uid}
        offering=None
        department_id=None
        official_only=bool(payload.get("official_only",False))
        if kind=="direct":
            try:
                target=int(payload.get("recipient_id"))
            except (TypeError,ValueError):
                return jsonify(error="recipient_id_required"),400
            if target==uid or not active_membership(institution_id,target):
                return jsonify(error="recipient_not_found"),404
            if CommunicationBlock.query.filter(
                CommunicationBlock.institution_id==institution_id,
                ((CommunicationBlock.blocker_id==uid)&(CommunicationBlock.blocked_id==target))|
                ((CommunicationBlock.blocker_id==target)&(CommunicationBlock.blocked_id==uid)),
            ).first():
                return jsonify(error="direct_messages_unavailable"),403
            participant_ids.add(target)
            existing=CommunicationConversation.query.filter_by(
                institution_id=institution_id,kind="direct"
            ).all()
            for prior in existing:
                ids={m.user_id for m in CommunicationMember.query.filter_by(conversation_id=prior.id).all()}
                if ids==participant_ids:
                    return jsonify(data=data(prior)),200
        elif kind=="group":
            raw_ids=payload.get("participant_ids",[])
            if not isinstance(raw_ids,list) or len(raw_ids)>99:
                return jsonify(error="invalid_participants"),400
            try:
                participant_ids.update(int(value) for value in raw_ids)
            except (TypeError,ValueError):
                return jsonify(error="invalid_participants"),400
            if any(not active_membership(institution_id,member_id) for member_id in participant_ids):
                return jsonify(error="all_participants_must_be_active_tenant_members"),400
            if not title:
                return jsonify(error="title_required"),400
        elif kind=="course":
            try:
                offering_id=int(payload.get("course_offering_id"))
            except (TypeError,ValueError):
                return jsonify(error="course_offering_id_required"),400
            offering=db.session.get(CourseOffering,offering_id)
            course=db.session.get(Course,offering.course_id) if offering else None
            from backend.core import Department as CoreDepartment
            department=db.session.get(CoreDepartment,course.department_id) if course else None
            if not department or department.institution_id!=institution_id:
                return jsonify(error="course_not_found"),404
            can_manage_course=bool(
                teacher_can_access_offering(offering,uid) or institution_manager(institution_id)
            )
            enrollment=Enrollment.query.filter_by(
                offering_id=offering.id,student_id=uid,status="enrolled"
            ).first()
            if not can_manage_course and not enrollment:
                return jsonify(error="forbidden"),403
            if not can_manage_course and official_only:
                return jsonify(error="official_channel_permission_required"),403
            if offering.teacher_id:
                participant_ids.add(offering.teacher_id)
            participant_ids.update(
                x.student_id for x in Enrollment.query.filter_by(
                    offering_id=offering.id,status="enrolled"
                ).all() if active_membership(institution_id,x.student_id)
            )
            existing=CommunicationConversation.query.filter_by(
                institution_id=institution_id,kind="course",course_offering_id=offering.id
            ).first()
            if existing:
                member_ids={
                    m.user_id for m in CommunicationMember.query.filter_by(conversation_id=existing.id).all()
                }
                for participant_id in participant_ids-member_ids:
                    db.session.add(CommunicationMember(
                        conversation_id=existing.id,user_id=participant_id,
                    ))
                if participant_ids-member_ids:
                    db.session.commit()
                return jsonify(data=data(existing)),200
            if not title:
                title=f"{course.code} · {offering.section}"
            official_only=bool(payload.get("official_only",False))
        elif kind=="department":
            try:
                department_id=int(payload.get("department_id"))
            except (TypeError,ValueError):
                return jsonify(error="department_id_required"),400
            department=db.session.get(Department,department_id)
            if not department or department.institution_id!=institution_id:
                return jsonify(error="department_not_found"),404
            if not institution_manager(institution_id):
                return jsonify(error="forbidden"),403
            participant_ids.update(
                m.user_id for m in InstitutionMembership.query.filter_by(institution_id=institution_id,status="active").all()
                if (db.session.get(UserProfile,m.user_id) and db.session.get(UserProfile,m.user_id).department==department.name)
            )
            if not title:title=department.name
        elif kind=="institution":
            if not institution_manager(institution_id):
                return jsonify(error="forbidden"),403
            official_only=True
            participant_ids.update(m.user_id for m in InstitutionMembership.query.filter_by(institution_id=institution_id,status="active").all())
            inst=db.session.get(Institution,institution_id)
            if not title:title=f"{inst.name} announcements"
        elif kind=="support":
            participant_ids.update(
                m.user_id for m in InstitutionMembership.query.filter_by(institution_id=institution_id,status="active").all()
                if m.role in MANAGERS
            )
            if not title:title="Student support request"
            if not str(payload.get("body","")).strip():
                return jsonify(error="support_request_details_required"),400

        conversation=CommunicationConversation(
            institution_id=institution_id,kind=kind,title=title,created_by=uid,
            course_offering_id=offering.id if offering else None,
            department_id=department_id,official_only=official_only,
        )
        db.session.add(conversation)
        db.session.flush()
        for participant_id in participant_ids:
            db.session.add(CommunicationMember(
                conversation_id=conversation.id,user_id=participant_id,
                last_read_at=datetime.now(timezone.utc) if participant_id==uid else None,
            ))
        if kind=="support":
            first=CommunicationMessage(conversation_id=conversation.id,sender_id=uid,body=str(payload["body"]).strip())
            db.session.add(first)
            for staff_id in participant_ids-{uid}:
                db.session.add(Notification(user_id=staff_id,kind="support_message",title="New student support request",body=title))
        db.session.commit()
        return jsonify(data=data(conversation)),201

    @app.get("/api/v1/communications/conversations/<int:conversation_id>/messages")
    @login_required
    def communication_messages(conversation_id):
        membership=conversation_member(conversation_id,request.current_user.id)
        if not membership:return jsonify(error="conversation_not_found"),404
        query=CommunicationMessage.query.filter_by(conversation_id=conversation_id)
        term=request.args.get("q","").strip()
        if term:query=query.filter(CommunicationMessage.body.ilike(f"%{term[:100]}%"))
        try:before=int(request.args.get("before","0"))
        except ValueError:return jsonify(error="invalid_cursor"),400
        if before:query=query.filter(CommunicationMessage.id<before)
        messages=query.order_by(CommunicationMessage.id.desc()).limit(100).all()
        messages.reverse()
        return jsonify(items=[message_data(message,request.current_user.id) for message in messages])

    @app.post("/api/v1/communications/conversations/<int:conversation_id>/messages")
    @login_required
    def send_communication_message(conversation_id):
        conversation=db.session.get(CommunicationConversation,conversation_id)
        membership=conversation_member(conversation_id,request.current_user.id)
        if not conversation or not membership:return jsonify(error="conversation_not_found"),404
        if not can_post(conversation,request.current_user):return jsonify(error="official_channel_read_only"),403
        payload=request.get_json(silent=True) or {}
        if "official" in payload and not isinstance(payload["official"],bool):
            return jsonify(error="official_must_be_boolean"),400
        body=str(payload.get("body","")).strip()
        attachment_url=str(payload.get("attachment_url","")).strip()
        if len(body)>10000:return jsonify(error="message_too_long"),400
        if not body and not attachment_url:return jsonify(error="message_or_attachment_required"),400
        if attachment_url and (len(attachment_url)>1000 or not attachment_url.startswith(("https://","http://"))):
            return jsonify(error="invalid_attachment_url"),400
        parent_id=payload.get("parent_id")
        if parent_id is not None:
            try:parent_id=int(parent_id)
            except (TypeError,ValueError):return jsonify(error="invalid_parent_message"),400
            parent=db.session.get(CommunicationMessage,parent_id)
            if not parent or parent.conversation_id!=conversation_id:return jsonify(error="parent_message_not_found"),404
        message=CommunicationMessage(
            conversation_id=conversation_id,sender_id=request.current_user.id,body=body,
            parent_id=parent_id,attachment_url=attachment_url or None,
            attachment_name=str(payload.get("attachment_name",""))[:255] or None,
            attachment_type=str(payload.get("attachment_type",""))[:100] or None,
            official=bool(payload.get("official",False)),
        )
        if message.official and not can_moderate(conversation,request.current_user):
            return jsonify(error="official_message_permission_required"),403
        db.session.add(message)
        recipients=CommunicationMember.query.filter(
            CommunicationMember.conversation_id==conversation_id,
            CommunicationMember.user_id!=request.current_user.id,
        ).all()
        if conversation.kind=="direct" and any(
            CommunicationBlock.query.filter(
                CommunicationBlock.institution_id==conversation.institution_id,
                ((CommunicationBlock.blocker_id==recipient.user_id)&(CommunicationBlock.blocked_id==request.current_user.id))|
                ((CommunicationBlock.blocker_id==request.current_user.id)&(CommunicationBlock.blocked_id==recipient.user_id)),
            ).first()
            for recipient in recipients
        ):
            db.session.rollback()
            return jsonify(error="direct_messages_unavailable"),403
        for recipient in recipients:
            if not recipient.muted:
                db.session.add(Notification(
                    user_id=recipient.user_id,kind="communication_message",
                    title=conversation.title or "New message",
                    body="New official communication" if message.official else "You have a new message.",
                ))
        db.session.commit()
        return jsonify(data=message_data(message,request.current_user.id)),201

    @app.post("/api/v1/communications/conversations/<int:conversation_id>/read")
    @login_required
    def mark_communication_read(conversation_id):
        membership=conversation_member(conversation_id,request.current_user.id)
        if not membership:return jsonify(error="conversation_not_found"),404
        membership.last_read_at=datetime.now(timezone.utc)
        db.session.commit()
        return jsonify(status="read")

    @app.patch("/api/v1/communications/conversations/<int:conversation_id>/settings")
    @login_required
    def update_communication_settings(conversation_id):
        membership=conversation_member(conversation_id,request.current_user.id)
        if not membership:return jsonify(error="conversation_not_found"),404
        payload=request.get_json(silent=True) or {}
        for key in ("muted","archived","pinned"):
            if key in payload:
                if not isinstance(payload[key],bool):return jsonify(error=f"{key}_must_be_boolean"),400
                setattr(membership,key,payload[key])
        db.session.commit()
        return jsonify(data=data(membership))

    @app.post("/api/v1/communications/messages/<int:message_id>/reactions")
    @login_required
    def toggle_communication_reaction(message_id):
        message=db.session.get(CommunicationMessage,message_id)
        if not message or not conversation_member(message.conversation_id,request.current_user.id):
            return jsonify(error="message_not_found"),404
        reaction=str((request.get_json(silent=True) or {}).get("reaction","")).strip()
        if reaction not in {"like","love","laugh","celebrate","sad","support"}:
            return jsonify(error="invalid_reaction"),400
        existing=CommunicationReaction.query.filter_by(
            message_id=message_id,user_id=request.current_user.id,reaction=reaction
        ).first()
        if existing:db.session.delete(existing)
        else:db.session.add(CommunicationReaction(message_id=message_id,user_id=request.current_user.id,reaction=reaction))
        db.session.commit()
        return jsonify(data=message_data(message,request.current_user.id))

    @app.post("/api/v1/communications/messages/<int:message_id>/reports")
    @login_required
    def report_communication_message(message_id):
        message=db.session.get(CommunicationMessage,message_id)
        if not message or not conversation_member(message.conversation_id,request.current_user.id):
            return jsonify(error="message_not_found"),404
        payload=request.get_json(silent=True) or {}
        reason=str(payload.get("reason","")).strip()[:80]
        if not reason:return jsonify(error="reason_required"),400
        if CommunicationReport.query.filter_by(message_id=message_id,reporter_id=request.current_user.id).first():
            return jsonify(error="already_reported"),409
        db.session.add(CommunicationReport(
            message_id=message_id,reporter_id=request.current_user.id,reason=reason,
            details=str(payload.get("details","")).strip()[:2000] or None,
        ))
        db.session.commit()
        return jsonify(status="reported"),201

    @app.get("/api/v1/communications/reports")
    @login_required
    def communication_reports():
        reports=CommunicationReport.query.filter_by(status="open").order_by(CommunicationReport.created_at.asc()).all()
        visible=[]
        for report in reports:
            message=db.session.get(CommunicationMessage,report.message_id)
            conversation=db.session.get(CommunicationConversation,message.conversation_id) if message else None
            if conversation and can_moderate(conversation,request.current_user):
                visible.append({**data(report),"message":message_data(message,request.current_user.id),"conversation_title":conversation.title})
        return jsonify(items=visible)

    @app.patch("/api/v1/communications/reports/<int:report_id>")
    @login_required
    def resolve_communication_report(report_id):
        report=db.session.get(CommunicationReport,report_id)
        message=db.session.get(CommunicationMessage,report.message_id) if report else None
        conversation=db.session.get(CommunicationConversation,message.conversation_id) if message else None
        if not report or not conversation or not can_moderate(conversation,request.current_user):
            return jsonify(error="report_not_found"),404
        status=(request.get_json(silent=True) or {}).get("status")
        if status not in {"reviewed","resolved","dismissed"}:
            return jsonify(error="invalid_report_status"),400
        report.status=status
        db.session.commit()
        return jsonify(data=data(report))

    @app.get("/api/v1/communications/blocks")
    @login_required
    def list_communication_blocks():
        institution_id=request.args.get("institution_id",type=int)
        if not institution_id or not active_membership(institution_id,request.current_user.id):
            return jsonify(error="institution_membership_required"),403
        items=[]
        for block in CommunicationBlock.query.filter_by(
            institution_id=institution_id,blocker_id=request.current_user.id
        ).all():
            profile=db.session.get(UserProfile,block.blocked_id)
            items.append({**data(block),"full_name":profile.full_name if profile else None})
        return jsonify(items=items)

    @app.post("/api/v1/communications/blocks")
    @login_required
    def create_communication_block():
        payload=request.get_json(silent=True) or {}
        try:
            institution_id=int(payload.get("institution_id"))
            blocked_id=int(payload.get("user_id"))
        except (TypeError,ValueError):
            return jsonify(error="institution_id_and_user_id_required"),400
        uid=request.current_user.id
        if blocked_id==uid or not active_membership(institution_id,uid) or not active_membership(institution_id,blocked_id):
            return jsonify(error="user_not_found"),404
        existing=CommunicationBlock.query.filter_by(
            institution_id=institution_id,blocker_id=uid,blocked_id=blocked_id
        ).first()
        if existing:return jsonify(data=data(existing)),200
        block=CommunicationBlock(institution_id=institution_id,blocker_id=uid,blocked_id=blocked_id)
        db.session.add(block)
        db.session.commit()
        return jsonify(data=data(block)),201

    @app.delete("/api/v1/communications/blocks/<int:block_id>")
    @login_required
    def remove_communication_block(block_id):
        block=db.session.get(CommunicationBlock,block_id)
        if not block or block.blocker_id!=request.current_user.id:
            return jsonify(error="block_not_found"),404
        db.session.delete(block)
        db.session.commit()
        return jsonify(status="unblocked")

from backend.academic import Enrollment, Assignment, Attendance
def register_dashboard(app):
    @app.get("/api/v1/dashboard")
    @login_required
    def dashboard():
        uid=request.current_user.id
        enrollments=Enrollment.query.filter_by(student_id=uid,status="enrolled").all()
        ids=[x.offering_id for x in enrollments]
        assignments=Assignment.query.filter(Assignment.offering_id.in_(ids)).limit(10).all() if ids else []
        att=Attendance.query.filter_by(student_id=uid).all()
        present=sum(x.status=="present" for x in att)
        from backend.core import Notification
        unread=Notification.query.filter_by(user_id=uid,is_read=False).count()
        return jsonify(stats={"courses":len(enrollments),"upcoming_assignments":len(assignments),"attendance_percent":round(present/len(att)*100,1) if att else 0,"unread_notifications":unread},assignments=[{k:getattr(x,k) for k in ("id","title","description","due_at","max_score")} for x in assignments])
