📘 Course Allocation System – Model Documentation & Design Rationale
This system supports dynamic allocation of courses to lecturers based on academic sessions, departmental structure, curriculum bulletins, and grouping requirements. Below is a model-by-model breakdown with rationale.

🔹 School
Purpose:
Represents the largest academic division in the university (e.g., School of Medical Sciences).

Key Fields:
- `name`: Unique name of the school.
- `acronym`: A short code for the school (e.g., "SMS").

Relationships:
- One-to-many with `Department` (a school contains multiple departments).

Why It Matters:
Provides a high-level organizational structure for academic units.

🔹 Department
Purpose:
Represents an academic unit (e.g., Computer Science, Biochemistry) that owns programs and manages lecturers.

Key Fields:
- `name`: Unique name of the department.
- `acronym`: A short code for the department (e.g., "CS").
- `school_id`: Links to the `School` it belongs to.

Relationships:
- Many-to-one with `School`.
- One-to-many with `Program` (departments offer programs).
- One-to-many with `User`, `Lecturer`, and `AdminUser`.

Why It Matters:
Enables HOD-level access control and groups programs and lecturers for allocation.

🔹 Lecturer
Purpose:
Stores detailed professional information about a teaching staff member, separate from their user account.

Key Fields:
- `staff_id`: Unique identifier for the staff member.
- `rank`: Academic rank (e.g., "Professor", "Lecturer I").
- `qualification`: Highest academic qualification (e.g., "Ph.D. in Computer Science").
- `specialization`: Area of research or teaching expertise.
- `gender`, `phone`, `other_responsibilities`: Additional profile details.
- `department_id`: Links to the `Department` they belong to.

Relationships:
- One-to-one with `User` (a lecturer's profile is linked to a single user account).
- Many-to-one with `Department`.
- One-to-many with `CourseAllocation`.

Why It Matters:
Separates login credentials (`User`) from detailed academic profiles (`Lecturer`), allowing for richer data about teaching staff.

🔹 AdminUser
Purpose:
Stores detailed information about an admin staff member, separate from their user account.

Key Fields:
- `gender`, `phone`: Additional profile details.
- `department_id`: Links to the `Department` they belong to.

Relationships:
- One-to-one with `User` (an admin's profile is linked to a single user account).
- Many-to-one with `Department`.

Why It Matters:
Separates login credentials (`User`) from detailed admin profiles (`AdminUser`), allowing for richer data about administrative staff.

🔹 User
Purpose:
Represents all system users who can log in: lecturers, HODs, vetters, admins, and superadmins.

Key Fields:
- `name`, `email`, `password`: User identity and login credentials.
- `role`: Defines access level.
- `department_id`: Optional, links user to a department (null for superadmins).
- `lecturer_id`: Optional, links to a `Lecturer` profile.
- `admin_user_id`: Optional, links to an `AdminUser` profile.

Roles Supported:
- `superadmin`: Global access.
- `admin`: Can manage system settings and data.
- `vetter`: Can review and approve certain actions.
- `hod`: Manages allocations for their department.
- `lecturer`: Receives and views course allocations.

Relationships:
- One-to-one with `Lecturer`.
- One-to-one with `AdminUser`.
- Many-to-one with `Department`.

Why It Matters:
Supports fine-grained, role-based access control (RBAC) and secure authentication.

🔹 Program
Purpose:
Defines a degree track (e.g., B.Sc. Computer Science) within a department.

Key Fields:
- `name`: Full name of the academic program.
- `acronym`: A short code for the program (e.g., "CS").
- `department_id`: Links to the `Department` offering the program.

Relationships:
- Belongs to one `Department`.
- Has many `ProgramCourse` entries.
- One-to-many with `Specialization` (a program can have multiple specializations).

Why It Matters:
Helps isolate course requirements and allocations at the program level.

🔹 Specialization
Purpose:
Represents a specialized area of study within a `Program`, typically starting at a higher level (e.g., 300-Level).

Key Fields:
- `name`: The name of the specialization (e.g., "Software Engineering", "Data Science").
- `program_id`: Links the specialization to its parent `Program`.

Relationships:
- Many-to-one with `Program`.
- Many-to-many with `ProgramCourse` (a specialization consists of multiple courses, and a course can be in multiple specializations).

Why It Matters:
Allows the system to model academic programs that diverge into different tracks, each with its own set of required and elective courses.

🔹 CourseType
Purpose:
Represents the type of a course (e.g., 'General', 'Core', 'Elective').

Key Fields:
- `name`: Unique name of the course type.

Relationships:
- One-to-many with `Course` (a course type can be applied to many courses).

Why It Matters:
Normalizes course types, ensuring consistency and making them easier to manage.

🔹 Course
Purpose:
Represents an academic course (e.g., COSC201 – Data Structures).

Key Fields:
- `code`, `title`: Unique identifier and full name for the course.
- `units`: The number of credit units the course is worth.
- `course_type_id`: Links to the `CourseType` of the course.

Relationships:
- Linked to `ProgramCourse` (can be reused across programs).
- Many-to-one with `CourseType`.

Why It Matters:
Allows course definitions to be reused across multiple programs and bulletins.

🔹 Bulletin
Purpose:
Captures curriculum structure for a time-bound period (e.g., 2019–2023).

Key Fields:
- `name`, `start_year`, `end_year`: Identifiers for the curriculum period.
- `is_active`: Flags the currently used curriculum.

Relationships:
- One-to-many with `ProgramCourse`.

Why It Matters:
Allows course offerings to be versioned and tracked historically. Enables "special allocations" from past bulletins.

🔹 Semester & Level
Purpose:
Define academic periods (`Semester`) and student year groups (`Level`).

Key Fields:
- `name`: Unique identifier (e.g., "First Semester", "100L").

Relationships:
- Both are used in `ProgramCourse` to define when a course is offered and for which student level.

Why It Matters:
Enables filtering and organization of courses for allocation.

🔹 ProgramCourse
Purpose:
The central link model. Represents a specific course offering under a program, for a given level, semester, and curriculum bulletin.

Key Fields:
- `program_id`, `course_id`, `level_id`, `semester_id`, `bulletin_id`

Relationships:
- Belongs to `Program`, `Course`, `Semester`, `Level`, and `Bulletin`.
- One-to-many with `CourseAllocation`.
- Many-to-many with `Specialization` (a course offering can be part of one or more specializations).

Why It Matters:
This model is the core that defines *where*, *when*, and *under which curriculum* a course exists, enabling reuse, versioning, and allocation per session.

🔹 AcademicSession
Purpose:
Represents an academic session (e.g., 2024/2025) during which allocations occur.

Key Fields:
- `name`, `is_active`: Session identifier and flag.

Relationships:
- One-to-many with `CourseAllocation`.

Why It Matters:
Enables session-based allocation tracking and historical views of who taught what, when.

🔹 CourseAllocation
Purpose:
Defines the actual assignment of a lecturer to a course for a specific session.

Key Fields:
- `program_course_id`, `session_id`, `semester_id`, `lecturer_id`: The core allocation links.
- `group_name`: Optional, for splitting a course into groups (e.g., "Group A").
- `is_lead`: Flags the main lecturer among grouped allocations.
- `is_allocated`: A boolean flag indicating if the allocation is confirmed.
- `class_size`: The number of students in the course or group.
- `is_de_allocation`: True if the allocation is a direct entry allocation.
- `source_bulletin_id`: Points to the bulletin the special course was pulled from.

Constraints:
- Composite uniqueness on `(program_course_id, session_id, group_name)` ensures no group duplication per session.

Why It Matters:
Tracks the actual delivery of courses, supporting multi-lecturer assignments, group-based teaching, and DE allocations.

✅ Conclusion: System Strengths
🔁 Curriculum Versioning: Bulletins allow for flexible, historical curriculum tracking.
👥 Lecturer Grouping: Supports team-teaching and group splitting for large classes.
📊 Session-Based Allocation: Keeps history of each academic year cleanly organized.
🧱 Role-Based Access: Differentiates between admin, HODs, and lecturers.
