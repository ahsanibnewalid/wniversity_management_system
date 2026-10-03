from backend.app import create_app
from backend.academic import Course, Program, Semester
from backend.core import (
    Department, Group, Institution, InstitutionMembership, UserProfile, db,
)


def client(platform_admin_emails=""):
    return create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "PLATFORM_ADMIN_EMAILS": platform_admin_emails,
    }).test_client()


def register_login(c, email):
    response=c.post("/api/v1/auth/register",json={
        "email":email,"password":"password123","full_name":email.split("@")[0],
        "username":email.split("@")[0],
    })
    assert response.status_code==201
    user_id=response.json["user_id"]
    response=c.post("/api/v1/auth/login",json={"email":email,"password":"password123"})
    assert response.status_code==200
    return user_id,{"Authorization":"Bearer "+response.json["access_token"]}


def create_institution(owner_id,slug,name):
    institution=Institution(name=name,slug=slug,kind="university",owner_id=owner_id)
    db.session.add(institution)
    db.session.flush()
    db.session.add(InstitutionMembership(
        institution_id=institution.id,user_id=owner_id,role="institution_owner",status="active"
    ))
    return institution


def test_department_admin_cannot_grant_institution_wide_roles():
    c=client()
    actor_id,headers=register_login(c,"dept-admin@example.com")
    target_id,_=register_login(c,"member@example.com")
    register_login(c,"invite@example.com")
    suspended_id,_=register_login(c,"suspended@example.com")
    owner_id,_=register_login(c,"owner@example.com")
    with c.application.app_context():
        institution=create_institution(owner_id,"role-test","Role Test University")
        actor=InstitutionMembership(institution_id=institution.id,user_id=actor_id,role="department_admin",status="active")
        target=InstitutionMembership(institution_id=institution.id,user_id=target_id,role="student",status="active")
        suspended=InstitutionMembership(institution_id=institution.id,user_id=suspended_id,role="student",status="suspended")
        db.session.add_all([actor,target,suspended])
        db.session.commit()
        institution_id=institution.id
        membership_id=target.id

    response=c.put(
        f"/api/v1/institutions/{institution_id}/admin/members/{membership_id}",
        json={"role":"principal"},headers=headers,
    )
    assert response.status_code==403
    response=c.post(
        f"/api/v1/institutions/{institution_id}/admin/members/invite",
        json={"email":"invite@example.com","role":"institution_owner"},headers=headers,
    )
    assert response.status_code==403
    response=c.post(
        f"/api/v1/institutions/{institution_id}/admin/members/invite",
        json={"email":"invite@example.com","role":"teacher"},headers=headers,
    )
    assert response.status_code==201
    response=c.post(
        f"/api/v1/institutions/{institution_id}/admin/members/invite",
        json={"email":"suspended@example.com","role":"student"},headers=headers,
    )
    assert response.status_code==200
    assert response.json["data"]["status"]=="active"


def test_institution_creation_reports_duplicate_names_and_slugs():
    c=client()
    first_id,first_headers=register_login(c,"first-owner@example.com")
    second_id,second_headers=register_login(c,"second-owner@example.com")
    with c.application.app_context():
        db.session.get(UserProfile,first_id).is_complete=True
        db.session.get(UserProfile,second_id).is_complete=True
        db.session.commit()

    response=c.post("/api/v1/institutions",
                    json={"name":"Example University","slug":"example"},headers=first_headers)
    assert response.status_code==201
    response=c.post("/api/v1/institutions",
                    json={"name":"Another University","slug":"example"},headers=second_headers)
    assert response.status_code==409
    assert response.json["error"]=="institution_name_or_slug_exists"


def test_platform_admin_can_manage_central_tenant_memberships():
    c=client("platform@example.com")
    platform_id,platform_headers=register_login(c,"platform@example.com")
    owner_id,_=register_login(c,"tenant-owner@example.com")
    teacher_id,_=register_login(c,"tenant-teacher@example.com")
    with c.application.app_context():
        db.session.get(UserProfile,platform_id).is_complete=True
        institution=create_institution(owner_id,"central-tenant","Central Tenant")
        db.session.add(InstitutionMembership(
            institution_id=institution.id,user_id=platform_id,
            role="student",status="active",
        ))
        db.session.commit()
        institution_id=institution.id

    response=c.get("/api/v1/platform/admin/overview",headers=platform_headers)
    assert response.status_code==200
    assert response.json["counts"]["universities"]==1
    response=c.get("/api/v1/platform/admin/institutions",headers=platform_headers)
    assert response.status_code==200
    assert response.json["items"][0]["owner_email"]=="tenant-owner@example.com"
    response=c.post(
        f"/api/v1/platform/admin/institutions/{institution_id}/members",
        json={"email":"tenant-teacher@example.com","role":"institution_owner"},
        headers=platform_headers,
    )
    assert response.status_code==201
    assert response.json["data"]["is_institution_owner"] is True
    with c.application.app_context():
        institution=db.session.get(Institution,institution_id)
        assert institution.owner_id==teacher_id
        previous_owner=InstitutionMembership.query.filter_by(
            institution_id=institution_id,user_id=owner_id
        ).first()
        assert previous_owner.role=="institution_admin"
    membership_id=response.json["data"]["id"]
    response=c.patch(
        f"/api/v1/platform/admin/members/{membership_id}",
        json={"role":"teacher","status":"suspended"},
        headers=platform_headers,
    )
    assert response.status_code==409
    response=c.get("/api/v1/platform/admin/users?q=tenant-teacher",headers=platform_headers)
    assert response.status_code==200
    assert response.json["items"][0]["email"]=="tenant-teacher@example.com"

    _,regular_headers=register_login(c,"regular@example.com")
    response=c.get("/api/v1/platform/admin/overview",headers=regular_headers)
    assert response.status_code==403


def test_private_group_requires_invitation_and_search_is_tenant_scoped():
    c=client()
    member_id,member_headers=register_login(c,"campus-member@example.com")
    owner_id,owner_headers=register_login(c,"campus-owner@example.com")
    outsider_id,_=register_login(c,"outside@example.com")
    with c.application.app_context():
        campus=create_institution(owner_id,"campus-a","Campus A")
        other=create_institution(outsider_id,"campus-b","Campus B")
        db.session.add(InstitutionMembership(
            institution_id=campus.id,user_id=member_id,role="student",status="active"
        ))
        private_group=Group(institution_id=campus.id,name="Secret Research Group",group_type="department",is_private=True)
        public_group=Group(institution_id=other.id,name="External Research Group",group_type="community",is_private=False)
        db.session.add_all([private_group,public_group])
        db.session.commit()
        campus_id=campus.id
        private_id=private_group.id

    response=c.post(f"/api/v1/groups/{private_id}/join",headers=member_headers)
    assert response.status_code==403
    response=c.get(f"/api/v1/institutions/{campus_id}/groups",headers=member_headers)
    assert "Secret Research Group" not in str(response.json)
    response=c.post(f"/api/v1/institutions/{campus_id}/admin/groups/{private_id}/members",
                    json={"user_id":member_id},headers=owner_headers)
    assert response.status_code==201
    response=c.post(f"/api/v1/groups/{private_id}/join",headers=member_headers)
    assert response.status_code==200
    response=c.get("/api/v1/search?q=Research",headers=member_headers)
    assert "External Research Group" not in str(response.json)
    assert "Secret Research Group" in str(response.json)


def test_teacher_assignment_results_and_join_requests_stay_in_institution():
    c=client()
    manager_id,manager_headers=register_login(c,"academic-admin@example.com")
    teacher_id,teacher_headers=register_login(c,"teacher@example.com")
    student_id,student_headers=register_login(c,"student@example.com")
    outsider_id,_=register_login(c,"outsider-student@example.com")
    applicant_id,applicant_headers=register_login(c,"applicant@example.com")
    alternate_id,alternate_headers=register_login(c,"alternate-applicant@example.com")
    with c.application.app_context():
        campus=create_institution(manager_id,"academic-a","Academic A")
        other=create_institution(manager_id,"academic-b","Academic B")
        department=Department(institution_id=campus.id,name="Computing",code="CS")
        other_department=Department(institution_id=other.id,name="Arts",code="AR")
        db.session.add_all([department,other_department])
        db.session.flush()
        course=Course(department_id=department.id,code="CS101",title="Computing")
        db.session.add(course)
        db.session.add_all([
            InstitutionMembership(institution_id=other.id,user_id=outsider_id,role="student",status="active"),
            InstitutionMembership(institution_id=campus.id,user_id=student_id,role="student",status="active"),
        ])
        student_profile=db.session.get(UserProfile,student_id)
        student_profile.is_complete=True
        db.session.get(UserProfile,applicant_id).is_complete=True
        db.session.get(UserProfile,alternate_id).is_complete=True
        db.session.flush()
        department_id=department.id
        source_department_id=other_department.id
        course_id=course.id
        campus_id=campus.id
        db.session.commit()

    response=c.post(f"/api/v1/courses/{course_id}/offerings",
                    json={"teacher_id":teacher_id},headers=manager_headers)
    assert response.status_code==400
    response=c.post(f"/api/v1/students/{outsider_id}/results",
                    json={"course_id":course_id,"grade":"A"},headers=manager_headers)
    assert response.status_code==400
    with c.application.app_context():
        db.session.add(InstitutionMembership(
            institution_id=campus_id,user_id=teacher_id,role="teacher",status="active"
        ))
        program=Program(department_id=source_department_id,name="Arts program")
        db.session.add(program)
        db.session.flush()
        semester=Semester(program_id=program.id,name="Semester 1")
        db.session.add(semester)
        db.session.commit()
        mismatched_semester_id=semester.id

    response=c.post(f"/api/v1/courses/{course_id}/offerings",
                    json={"teacher_id":teacher_id},headers=manager_headers)
    assert response.status_code==201
    offering_id=response.json["id"]
    response=c.get("/api/v1/teacher/dashboard",headers=teacher_headers)
    assert response.status_code==200
    assert response.json["courses"][0]["course_title"]=="Computing"
    response=c.post(f"/api/v1/offerings/{offering_id}/enroll",headers=student_headers)
    assert response.status_code==201
    response=c.post(
        f"/api/v1/offerings/{offering_id}/assignments",
        json={"title":"Lab report","max_score":10},headers=teacher_headers,
    )
    assert response.status_code==201
    assignment_id=response.json["id"]
    response=c.post(
        f"/api/v1/assignments/{assignment_id}/submit",
        json={"body":"Completed lab"},headers=student_headers,
    )
    assert response.status_code==201
    submission_id=response.json["id"]
    response=c.post(
        f"/api/v1/submissions/{submission_id}/grade",
        json={"score":11,"feedback":"Over maximum"},headers=teacher_headers,
    )
    assert response.status_code==400
    response=c.post(
        f"/api/v1/submissions/{submission_id}/grade",
        json={"score":8,"feedback":"Good work"},headers=teacher_headers,
    )
    assert response.status_code==200
    response=c.post(f"/api/v1/students/{student_id}/results",
                    json={"course_id":course_id,"semester_id":mismatched_semester_id,"grade":"A"},
                    headers=manager_headers)
    assert response.status_code==400
    response=c.post(f"/api/v1/institutions/{campus_id}/join",
                    json={"department_id":source_department_id,"student_id":"S-1","program":"CS",
                          "session":"2025","academic_year":"1"},headers=applicant_headers)
    assert response.status_code==400
    application={
        "department_id":department_id,
        "student_id":"S-1",
        "program":"CS",
        "session":"2025",
        "academic_year":"1",
    }
    response=c.post(f"/api/v1/institutions/{campus_id}/join",
                    json=application,headers=applicant_headers)
    assert response.status_code==201
    request_id=response.json["request_id"]
    response=c.post(f"/api/v1/institutions/{campus_id}/admin/requests/{request_id}/review",
                    json={"decision":"approve"},headers=manager_headers)
    assert response.status_code==200
    response=c.post(f"/api/v1/institutions/{campus_id}/join",
                    json={**application,"student_id":"S-2"},headers=alternate_headers)
    assert response.status_code==201
    response=c.post(f"/api/v1/join-requests/{response.json['request_id']}/review",
                    json={"decision":"approve"},headers=manager_headers)
    assert response.status_code==200
    for headers in (applicant_headers,alternate_headers):
        memberships=c.get("/api/v1/my/institutions",headers=headers).json["items"]
        assert any(item["id"]==campus_id and item["role"]=="student" for item in memberships)
    with c.application.app_context():
        membership=InstitutionMembership.query.filter_by(
            institution_id=campus_id,user_id=teacher_id
        ).first()
        membership.role="student"
        db.session.commit()
    response=c.get(f"/api/v1/teacher/courses/{offering_id}/students",headers=teacher_headers)
    assert response.status_code==403
