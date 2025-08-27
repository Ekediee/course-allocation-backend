```python
@allocation_bp.route('/list', methods=['GET'])
@jwt_required()
def get_hod_course_allocations():
    # ic(current_user)
    department = current_user.lecturer.department
    
    programs = Program.query.filter_by(department_id=department.id).all()
    semesters = Semester.query.all()  # Or filtered by active session

    output = []
    for semester in semesters:
        semester_data = {"id": semester.id, "name": semester.name, "programs": []}
        
        for program in programs:
            program_data = {"id": program.id, "name": program.name, "levels": []}
            
            # levels = db.session.query(ProgramCourse.level).filter_by(program_id=program.id).distinct().all()
            
            # Get distinct level IDs used in this program
            level_ids = (
                db.session.query(ProgramCourse.level_id)
                .filter_by(program_id=program.id)
                .distinct()
                .all()
            )
            # ic(level_ids, semester.id, program.id)
            for level_row in level_ids:
                # level = level_row.level
                level_id = level_row.level_id
                level = Level.query.get(level_id)

                level_data = {"id": str(level.id), "name": f"{level.name} Level", "courses": []}
                
                program_courses = ProgramCourse.query.filter_by(
                    program_id=program.id, level_id=level.id
                ).distinct()

                for pc in program_courses:
                    course = pc.course
                    allocation = CourseAllocation.query.filter_by(
                        program_course_id=pc.id,
                        semester_id=semester.id
                    ).first()

                    level_data["courses"].append({
                        "id": str(course.id),
                        "code": course.code,
                        "title": course.title,
                        "unit": course.units,
                        "isAllocated": bool(allocation),
                        "allocatedTo": allocation.lecturer_profile.user_account[0].name if allocation else None
                    })
                program_data["levels"].append(level_data)
            semester_data["programs"].append(program_data)
        output.append(semester_data)
    return output
```