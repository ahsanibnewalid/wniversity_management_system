from backend.academic import Course, CourseOffering, Enrollment
from backend.core import Department, Institution, InstitutionMembership, db
from test_tenant_authorization import client, register_login, create_institution


def test_direct_communication_controls_reactions_threads_and_tenant_privacy():
    c=client()
    sender_id,sender_headers=register_login(c,"sender@campus.example")
    recipient_id,recipient_headers=register_login(c,"recipient@campus.example")
    outsider_id,outsider_headers=register_login(c,"outsider@elsewhere.example")
    owner_id,owner_headers=register_login(c,"owner@campus.example")
    with c.application.app_context():
        institution=create_institution(owner_id,"chat-campus","Chat Campus")
        db.session.add_all([
            InstitutionMembership(institution_id=institution.id,user_id=sender_id,role="student",status="active"),
            InstitutionMembership(institution_id=institution.id,user_id=recipient_id,role="teacher",status="active"),
        ])
        db.session.commit()
        institution_id=institution.id

    response=c.post("/api/v1/communications/conversations",json={
        "kind":"direct","institution_id":institution_id,"recipient_id":recipient_id,
    },headers=sender_headers)
    assert response.status_code==201
    conversation_id=response.json["data"]["id"]
    response=c.post("/api/v1/communications/conversations",json={
        "kind":"direct","institution_id":institution_id,"recipient_id":recipient_id,
    },headers=sender_headers)
    assert response.status_code==200
    assert response.json["data"]["id"]==conversation_id

    response=c.post(f"/api/v1/communications/conversations/{conversation_id}/messages",json={
        "body":"Can I submit tomorrow?",
    },headers=sender_headers)
    assert response.status_code==201
    message_id=response.json["data"]["id"]
    response=c.post(f"/api/v1/communications/conversations/{conversation_id}/messages",json={
        "body":"Yes, please submit before noon.","parent_id":message_id,
    },headers=recipient_headers)
    assert response.status_code==201
    assert response.json["data"]["parent_id"]==message_id

    response=c.post(f"/api/v1/communications/messages/{message_id}/reactions",
                    json={"reaction":"like"},headers=recipient_headers)
    assert response.status_code==200
    assert response.json["data"]["reactions"][0]["reacted"] is True
    response=c.post(f"/api/v1/communications/messages/{message_id}/reports",
                    json={"reason":"test report"},headers=recipient_headers)
    assert response.status_code==201
    response=c.post(f"/api/v1/communications/messages/{message_id}/reports",
                    json={"reason":"duplicate"},headers=recipient_headers)
    assert response.status_code==409
    response=c.get("/api/v1/communications/reports",headers=owner_headers)
    assert response.status_code==200
    assert len(response.json["items"])==1
    report_id=response.json["items"][0]["id"]
    response=c.patch(f"/api/v1/communications/reports/{report_id}",
                     json={"status":"resolved"},headers=owner_headers)
    assert response.status_code==200

    response=c.get(f"/api/v1/communications/conversations/{conversation_id}/messages?q=tomorrow",
                   headers=recipient_headers)
    assert response.status_code==200
    assert len(response.json["items"])==1
    response=c.patch(f"/api/v1/communications/conversations/{conversation_id}/settings",
                     json={"muted":True,"pinned":True},headers=recipient_headers)
    assert response.status_code==200
    response=c.get("/api/v1/communications/conversations",headers=recipient_headers)
    assert response.json["items"][0]["membership"]["muted"] is True
    assert response.json["items"][0]["membership"]["pinned"] is True
    response=c.patch(f"/api/v1/communications/conversations/{conversation_id}/settings",
                     json={"archived":True},headers=recipient_headers)
    assert response.status_code==200
    response=c.get("/api/v1/communications/conversations",headers=recipient_headers)
    assert response.json["items"]==[]
    response=c.get("/api/v1/communications/conversations?archived=true",headers=recipient_headers)
    assert response.json["items"][0]["membership"]["archived"] is True

    response=c.get(f"/api/v1/communications/conversations/{conversation_id}/messages",
                   headers=outsider_headers)
    assert response.status_code==404
    response=c.post("/api/v1/communications/conversations",json={
        "kind":"direct","institution_id":institution_id,"recipient_id":outsider_id,
    },headers=sender_headers)
    assert response.status_code==404


def test_course_communication_channel_is_scoped_and_official_mode_is_read_only():
    c=client()
    teacher_id,teacher_headers=register_login(c,"teacher@course.example")
    student_id,student_headers=register_login(c,"student@course.example")
    outsider_id,outsider_headers=register_login(c,"outsider@course.example")
    owner_id,_=register_login(c,"owner@course.example")
    with c.application.app_context():
        institution=create_institution(owner_id,"course-campus","Course Campus")
        teacher_membership=InstitutionMembership(
            institution_id=institution.id,user_id=teacher_id,role="teacher",status="active",
        )
        student_membership=InstitutionMembership(
            institution_id=institution.id,user_id=student_id,role="student",status="active",
        )
        department=Department(institution_id=institution.id,name="Computing",code="COMP")
        db.session.add_all([teacher_membership,student_membership,department])
        db.session.flush()
        course=Course(department_id=department.id,code="COMP101",title="Computing")
        db.session.add(course)
        db.session.flush()
        offering=CourseOffering(course_id=course.id,teacher_id=teacher_id,section="A")
        db.session.add(offering)
        db.session.flush()
        db.session.add(Enrollment(offering_id=offering.id,student_id=student_id,status="enrolled"))
        db.session.commit()
        institution_id=institution.id
        offering_id=offering.id

    response=c.post("/api/v1/communications/conversations",json={
        "kind":"course","institution_id":institution_id,
        "course_offering_id":offering_id,"official_only":True,
    },headers=teacher_headers)
    assert response.status_code==201
    conversation_id=response.json["data"]["id"]
    response=c.post(f"/api/v1/communications/conversations/{conversation_id}/messages",
                    json={"body":"Assignment deadline extended.","official":True},headers=teacher_headers)
    assert response.status_code==201
    response=c.post(f"/api/v1/communications/conversations/{conversation_id}/messages",
                    json={"body":"Thanks!"},headers=student_headers)
    assert response.status_code==403
    response=c.get(f"/api/v1/communications/conversations/{conversation_id}/messages",
                   headers=student_headers)
    assert response.status_code==200
    assert len(response.json["items"])==1
    response=c.get(f"/api/v1/communications/conversations/{conversation_id}/messages",
                   headers=outsider_headers)
    assert response.status_code==404
    with c.application.app_context():
        membership=InstitutionMembership.query.filter_by(
            institution_id=institution_id,user_id=student_id
        ).first()
        membership.status="suspended"
        db.session.commit()
    response=c.get(f"/api/v1/communications/conversations/{conversation_id}/messages",
                   headers=student_headers)
    assert response.status_code==404


def test_blocked_member_cannot_start_or_continue_direct_messages():
    c=client()
    blocker_id,blocker_headers=register_login(c,"blocker@campus.example")
    blocked_id,blocked_headers=register_login(c,"blocked@campus.example")
    owner_id,_=register_login(c,"block-owner@campus.example")
    with c.application.app_context():
        institution=create_institution(owner_id,"block-campus","Block Campus")
        db.session.add_all([
            InstitutionMembership(institution_id=institution.id,user_id=blocker_id,role="student",status="active"),
            InstitutionMembership(institution_id=institution.id,user_id=blocked_id,role="student",status="active"),
        ])
        db.session.commit()
        institution_id=institution.id

    response=c.post("/api/v1/communications/blocks",json={
        "institution_id":institution_id,"user_id":blocked_id,
    },headers=blocker_headers)
    assert response.status_code==201
    response=c.post("/api/v1/communications/conversations",json={
        "kind":"direct","institution_id":institution_id,"recipient_id":blocker_id,
    },headers=blocked_headers)
    assert response.status_code==403
    response=c.get(f"/api/v1/communications/blocks?institution_id={institution_id}",
                   headers=blocker_headers)
    assert response.status_code==200
    assert response.json["items"][0]["blocked_id"]==blocked_id


def test_announcements_are_tenant_scoped_and_audience_filtered():
    c=client()
    owner_id,owner_headers=register_login(c,"announcement-owner@campus.example")
    student_id,student_headers=register_login(c,"announcement-student@campus.example")
    teacher_id,teacher_headers=register_login(c,"announcement-teacher@campus.example")
    outsider_id,outsider_headers=register_login(c,"announcement-outsider@elsewhere.example")
    with c.application.app_context():
        institution=create_institution(owner_id,"announcement-campus","Announcement Campus")
        db.session.add_all([
            InstitutionMembership(institution_id=institution.id,user_id=student_id,role="student",status="active"),
            InstitutionMembership(institution_id=institution.id,user_id=teacher_id,role="teacher",status="active"),
        ])
        db.session.commit()
        institution_id=institution.id

    response=c.post(f"/api/v1/institutions/{institution_id}/announcements",json={
        "title":"Faculty notice","body":"Teacher-only update","audience":"teachers",
    },headers=owner_headers)
    assert response.status_code==201
    announcement_id=response.json["id"]
    response=c.get(f"/api/v1/institutions/{institution_id}/announcements",
                   headers=student_headers)
    assert response.status_code==200
    assert response.json["items"]==[]
    response=c.get(f"/api/v1/institutions/{institution_id}/announcements",
                   headers=teacher_headers)
    assert len(response.json["items"])==1
    response=c.get(f"/api/v1/institutions/{institution_id}/announcements",
                   headers=outsider_headers)
    assert response.status_code==403
    response=c.post(f"/api/v1/announcements/{announcement_id}/read",headers=student_headers)
    assert response.status_code==404
    response=c.post(f"/api/v1/institutions/{institution_id}/announcements",json={
        "title":"","body":"Missing title",
    },headers=owner_headers)
    assert response.status_code==400
