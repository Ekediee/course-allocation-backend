import pytest
from flask_jwt_extended import create_access_token
from app import create_app, db
from app.models import (
    School, Department, User, Lecturer, Program, Level, Semester,
    Course, Bulletin, AcademicSession, ProgramCourse, Specialization,
    CourseAllocation, DepartmentAllocationState
)


@pytest.fixture(scope='function')
def test_client():
    flask_app = create_app(config_name='testing')
    flask_app.config['JWT_SECRET_KEY'] = 'super-secret-testing-key'
    flask_app.config['JWT_COOKIE_CSRF_PROTECT'] = False

    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            db.create_all()
            setup_test_data()
            yield testing_client
            db.session.remove()
            db.drop_all()


def setup_test_data():
    school = School(name="School of Public And Allied Health", acronym="SPAH")
    db.session.add(school)
    db.session.flush()

    department = Department(
        name="Nutrition And Dietetics",
        acronym="NUDT",
        school_id=school.id
    )
    db.session.add(department)
    db.session.flush()

    program = Program(
        name="Nutrition And Dietetics",
        department_id=department.id,
        acronym="NUDT"
    )
    db.session.add(program)
    db.session.flush()

    hod_lecturer = Lecturer(staff_id="HOD_NUDT", department_id=department.id)
    lec_a = Lecturer(staff_id="LEC_A", department_id=department.id)
    lec_b = Lecturer(staff_id="LEC_B", department_id=department.id)
    lec_c = Lecturer(staff_id="LEC_C", department_id=department.id)
    db.session.add_all([hod_lecturer, lec_a, lec_b, lec_c])
    db.session.flush()

    hod_user = User(
        name="Dr. HOD NUDT",
        email="hod.nudt@test.com",
        role="hod",
        department_id=department.id,
        lecturer_id=hod_lecturer.id
    )
    hod_user.set_password("password")

    user_a = User(
        name="Dr. Prior Session",
        email="prior@test.com",
        role="lecturer",
        department_id=department.id,
        lecturer_id=lec_a.id
    )
    user_b = User(
        name="Dr. Active Session",
        email="active@test.com",
        role="lecturer",
        department_id=department.id,
        lecturer_id=lec_b.id
    )
    user_c = User(
        name="Dr. Group B",
        email="groupb@test.com",
        role="lecturer",
        department_id=department.id,
        lecturer_id=lec_c.id
    )
    db.session.add_all([hod_user, user_a, user_b, user_c])

    level200 = Level(name="200")
    level300 = Level(name="300")
    first_sem = Semester(name="First Semester", is_active=True)
    second_sem = Semester(name="Second Semester", is_active=True)
    summer_sem = Semester(name="Summer Semester", is_active=True)
    db.session.add_all([level200, level300, first_sem, second_sem, summer_sem])
    db.session.flush()

    bulletin_old = Bulletin(
        name="2019 - 2023",
        start_year=2019,
        end_year=2023,
        is_active=False
    )
    bulletin_active = Bulletin(
        name="2023 - 2027",
        start_year=2023,
        end_year=2027,
        is_active=True
    )
    session_a = AcademicSession(name="2024/2025", is_active=False)
    session_b = AcademicSession(name="2025/2026", is_active=True)
    db.session.add_all([bulletin_old, bulletin_active, session_a, session_b])
    db.session.flush()

    nudt202 = Course(code="NUDT202", title="General and Applied Nutrition", units=2)
    nudt204 = Course(code="NUDT204", title="Human Nutrition", units=3)
    nudt302 = Course(code="NUDT302", title="Clinical Nutrition", units=3)
    db.session.add_all([nudt202, nudt204, nudt302])
    db.session.flush()

    spec = Specialization(name="Clinical Dietetics", program_id=program.id)
    db.session.add(spec)
    db.session.flush()

    pc_nudt202 = ProgramCourse(
        program_id=program.id,
        course_id=nudt202.id,
        level_id=level200.id,
        semester_id=second_sem.id,
        bulletin_id=bulletin_old.id
    )
    pc_nudt204 = ProgramCourse(
        program_id=program.id,
        course_id=nudt204.id,
        level_id=level200.id,
        semester_id=second_sem.id,
        bulletin_id=bulletin_old.id
    )
    pc_nudt302 = ProgramCourse(
        program_id=program.id,
        course_id=nudt302.id,
        level_id=level300.id,
        semester_id=second_sem.id,
        bulletin_id=bulletin_old.id
    )
    db.session.add_all([pc_nudt202, pc_nudt204, pc_nudt302])
    db.session.flush()

    pc_nudt302.specializations.append(spec)

    # Historical allocations in inactive Session A
    hist_allocs = [
        CourseAllocation(
            program_course_id=pc_nudt202.id,
            session_id=session_a.id,
            semester_id=second_sem.id,
            lecturer_id=lec_a.id,
            source_bulletin_id=bulletin_old.id,
            group_name="Group A",
            is_lead=True,
            is_allocated=True,
            class_size=40,
            class_option="Regular"
        ),
        CourseAllocation(
            program_course_id=pc_nudt204.id,
            session_id=session_a.id,
            semester_id=second_sem.id,
            lecturer_id=lec_a.id,
            source_bulletin_id=bulletin_old.id,
            group_name="Group A",
            is_lead=True,
            is_allocated=True,
            class_size=35,
            class_option="Regular"
        ),
        CourseAllocation(
            program_course_id=pc_nudt302.id,
            session_id=session_a.id,
            semester_id=second_sem.id,
            lecturer_id=lec_a.id,
            source_bulletin_id=bulletin_old.id,
            group_name="Group A",
            is_lead=True,
            is_allocated=True,
            class_size=30,
            class_option="Regular"
        ),
    ]
    db.session.add_all(hist_allocs)

    # Historical summer submission state in Session A
    hist_summer_state = DepartmentAllocationState(
        department_id=department.id,
        session_id=session_a.id,
        semester_id=summer_sem.id,
        is_submitted=True,
        submitted_by_id=hod_user.id
    )
    db.session.add(hist_summer_state)
    db.session.commit()


def _hod_headers():
    hod_user = User.query.filter_by(email="hod.nudt@test.com").first()
    token = create_access_token(identity=str(hod_user.id))
    return {"Authorization": f"Bearer {token}"}


def _post_courses_by_bulletin(client):
    return client.post(
        "/api/v1/allocation/courses-by-bulletin",
        headers=_hod_headers(),
        json={
            "bulletin": "2019 - 2023",
            "program": "Nutrition And Dietetics",
            "semester": "Second Semester",
        },
    )


def test_fresh_session_returns_all_courses_unallocated(test_client):
    """Prior-session allocations must not appear in a fresh active session."""
    response = _post_courses_by_bulletin(test_client)
    assert response.status_code == 200

    data = response.get_json()
    assert data["is_submitted"] is False
    assert [lvl["name"] for lvl in data["levels"]] == ["200 Level", "300 Level"]

    all_courses = {
        c["code"]: c
        for lvl in data["levels"]
        for c in lvl["courses"]
    }
    assert set(all_courses.keys()) == {"NUDT202", "NUDT204", "NUDT302"}

    for code, course in all_courses.items():
        assert course["isAllocated"] is False, f"{code} leaked allocation from inactive session"
        assert course["allocatedTo"] is None, f"{code} leaked lecturer from inactive session"
        assert "programCourseId" in course
        assert "specialization" in course

    assert all_courses["NUDT202"]["specialization"] == "General"
    assert all_courses["NUDT302"]["specialization"] == "Clinical Dietetics"


def test_active_session_allocation_reflected_without_touching_history(test_client):
    """Allocating one course in active Session B only marks that course allocated and preserves Session A history."""
    session_a = AcademicSession.query.filter_by(name="2024/2025").first()
    session_b = AcademicSession.query.filter_by(name="2025/2026").first()
    second_sem = Semester.query.filter_by(name="Second Semester").first()
    nudt202 = Course.query.filter_by(code="NUDT202").first()
    pc_nudt202 = ProgramCourse.query.filter_by(course_id=nudt202.id).first()
    lec_b = Lecturer.query.filter_by(staff_id="LEC_B").first()
    lec_a = Lecturer.query.filter_by(staff_id="LEC_A").first()

    active_alloc = CourseAllocation(
        program_course_id=pc_nudt202.id,
        session_id=session_b.id,
        semester_id=second_sem.id,
        lecturer_id=lec_b.id,
        source_bulletin_id=pc_nudt202.bulletin_id,
        group_name="Group A",
        is_lead=True,
        is_allocated=True,
        class_size=50,
        class_option="Regular"
    )
    db.session.add(active_alloc)
    db.session.commit()

    response = _post_courses_by_bulletin(test_client)
    assert response.status_code == 200
    data = response.get_json()

    all_courses = {
        c["code"]: c
        for lvl in data["levels"]
        for c in lvl["courses"]
    }
    assert all_courses["NUDT202"]["isAllocated"] is True
    assert all_courses["NUDT202"]["allocatedTo"] == "Dr. Active Session"

    assert all_courses["NUDT204"]["isAllocated"] is False
    assert all_courses["NUDT204"]["allocatedTo"] is None
    assert all_courses["NUDT302"]["isAllocated"] is False
    assert all_courses["NUDT302"]["allocatedTo"] is None

    # Verify historical Session A allocations remain intact
    hist_allocs = CourseAllocation.query.filter_by(session_id=session_a.id).all()
    assert len(hist_allocs) == 3
    assert all(a.lecturer_id == lec_a.id for a in hist_allocs)


def test_multi_group_allocations_in_active_session(test_client):
    """Multiple groups allocated in the active session combine lecturer names like /detailed-list."""
    session_b = AcademicSession.query.filter_by(name="2025/2026").first()
    second_sem = Semester.query.filter_by(name="Second Semester").first()
    nudt202 = Course.query.filter_by(code="NUDT202").first()
    pc_nudt202 = ProgramCourse.query.filter_by(course_id=nudt202.id).first()
    lec_b = Lecturer.query.filter_by(staff_id="LEC_B").first()
    lec_c = Lecturer.query.filter_by(staff_id="LEC_C").first()

    db.session.add_all([
        CourseAllocation(
            program_course_id=pc_nudt202.id,
            session_id=session_b.id,
            semester_id=second_sem.id,
            lecturer_id=lec_b.id,
            source_bulletin_id=pc_nudt202.bulletin_id,
            group_name="Group A",
            is_lead=True,
            is_allocated=True,
            class_size=40,
            class_option="Regular"
        ),
        CourseAllocation(
            program_course_id=pc_nudt202.id,
            session_id=session_b.id,
            semester_id=second_sem.id,
            lecturer_id=lec_c.id,
            source_bulletin_id=pc_nudt202.bulletin_id,
            group_name="Group B",
            is_lead=False,
            is_allocated=True,
            class_size=40,
            class_option="Regular"
        ),
    ])
    db.session.commit()

    response = _post_courses_by_bulletin(test_client)
    assert response.status_code == 200

    all_courses = {
        c["code"]: c
        for lvl in response.get_json()["levels"]
        for c in lvl["courses"]
    }
    assert all_courses["NUDT202"]["isAllocated"] is True
    assert all_courses["NUDT202"]["allocatedTo"] == "Dr. Active Session, Dr. Group B"


def test_allocate_endpoint_duplicate_check_scoped_to_active_session(test_client):
    """Allocating a course in Session B previously allocated in Session A succeeds; duplicate in Session B fails."""
    program = Program.query.filter_by(name="Nutrition And Dietetics").first()
    level200 = Level.query.filter_by(name="200").first()
    second_sem = Semester.query.filter_by(name="Second Semester").first()
    nudt202 = Course.query.filter_by(code="NUDT202").first()
    session_b = AcademicSession.query.filter_by(name="2025/2026").first()

    payload = [
        {
            "programId": program.id,
            "levelId": level200.id,
            "courseId": nudt202.id,
            "semesterId": second_sem.id,
            "allocatedTo": "Dr. Active Session",
            "groupName": "Group A",
            "isAllocated": True,
            "classSize": 45,
            "class_option": "Regular",
        }
    ]

    resp1 = test_client.post("/api/v1/allocation/allocate", headers=_hod_headers(), json=payload)
    assert resp1.status_code == 201

    pc_nudt202 = ProgramCourse.query.filter_by(course_id=nudt202.id).first()
    saved_active = CourseAllocation.query.filter_by(
        program_course_id=pc_nudt202.id,
        session_id=session_b.id,
        semester_id=second_sem.id,
        group_name="Group A"
    ).first()
    assert saved_active is not None

    # Re-posting the exact same allocation in active Session B must be rejected as duplicate
    resp2 = test_client.post("/api/v1/allocation/allocate", headers=_hod_headers(), json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.get_json()["message"].lower()


def test_no_active_session_returns_error(test_client):
    """When no session is active, courses-by-bulletin returns 404 with a descriptive error."""
    AcademicSession.query.update({AcademicSession.is_active: False})
    db.session.commit()

    response = _post_courses_by_bulletin(test_client)
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert "no active session" in data["error"].lower()


def test_companion_details_and_summer_status_scoped_to_active_session(test_client):
    """Companion endpoints /details and /status/summer/<name> must be strictly scoped to active session."""
    session_b = AcademicSession.query.filter_by(name="2025/2026").first()
    second_sem = Semester.query.filter_by(name="Second Semester").first()
    nudt202 = Course.query.filter_by(code="NUDT202").first()
    pc_nudt202 = ProgramCourse.query.filter_by(course_id=nudt202.id).first()
    lec_b = Lecturer.query.filter_by(staff_id="LEC_B").first()

    # /details in fresh Session B must not return Session A's allocation
    details_resp_empty = test_client.get(
        f"/api/v1/allocation/details?program_course_id={pc_nudt202.id}&semester_id={second_sem.id}",
        headers=_hod_headers()
    )
    assert details_resp_empty.status_code == 200
    assert details_resp_empty.get_json()["data"] == []

    # After allocating in Session B, /details returns only Session B's record
    db.session.add(
        CourseAllocation(
            program_course_id=pc_nudt202.id,
            session_id=session_b.id,
            semester_id=second_sem.id,
            lecturer_id=lec_b.id,
            source_bulletin_id=pc_nudt202.bulletin_id,
            group_name="Group A",
            is_lead=True,
            is_allocated=True,
            class_size=55,
            class_option="Regular"
        )
    )
    db.session.commit()

    details_resp_active = test_client.get(
        f"/api/v1/allocation/details?program_course_id={pc_nudt202.id}&semester_id={second_sem.id}",
        headers=_hod_headers()
    )
    assert details_resp_active.status_code == 200
    details_data = details_resp_active.get_json()["data"]
    assert len(details_data) == 1
    assert details_data[0]["lecturer"] == "Dr. Active Session"

    # /status/summer/<name> in Session B must not reflect Session A's submitted state
    summer_resp = test_client.get(
        "/api/v1/allocation/status/summer/Summer Semester",
        headers=_hod_headers()
    )
    assert summer_resp.status_code == 200
    assert summer_resp.get_json()["is_submitted"] is False
