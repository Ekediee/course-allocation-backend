📘 Course Allocation System – Model Documentation & Design Rationale
This system supports dynamic allocation of courses to lecturers based on academic sessions, departmental structure, curriculum bulletins, and grouping requirements. Below is a model-by-model breakdown with rationale.

🔹 Department
Purpose:
Represents an academic unit (e.g., Computer Science, Biochemistry) that owns programs and manages lecturers.

Key Fields:
name: Unique identifier of the department.

Relationships:
One-to-many with Program (departments offer programs).

One-to-many with User (lecturers and HODs belong to a department).

Why It Matters:
Enables HOD-level access control and program grouping for allocations.

🔹 Program
Purpose:
Defines a degree track (e.g., B.Sc. Computer Science) within a department.

Key Fields:
name: Full name of the academic program.

department_id: Links to the department offering the program.

Relationships:
Belongs to one Department.

Has many ProgramCourse entries (courses offered under the program).

Why It Matters:
Helps isolate course requirements and allocations at the program level.

🔹 Course
Purpose:
Represents an academic course (e.g., COSC201 – Data Structures).

Key Fields:
code, title: Identifiers and labels for the course.

Relationships:
Linked to ProgramCourse (can be reused across programs).

Why It Matters:
Allows course reuse across multiple programs and bulletins.

🔹 Bulletin
Purpose:
Captures curriculum structure for a time-bound period (e.g., 2019–2023).

Key Fields:
name, start_year, end_year

is_active: Flags the currently used curriculum.

Relationships:
One-to-many with ProgramCourse.

Why It Matters:
Allows course offerings to be tracked historically and reused as “special allocations” from past bulletins.

🔹 Semester
Purpose:
Defines academic periods (e.g., First Semester, Second Semester).

Key Fields:
name: Unique name of the semester.

Relationships:
Used by ProgramCourse.

Why It Matters:
Used to organize course offerings by semester, and filter allocations accordingly.

🔹 Level
Purpose:
Captures student levels (e.g., 100L, 200L, 300L).

Key Fields:
name: Level label (unique).

Relationships:
Used in ProgramCourse.

Why It Matters:
Enables level-specific filtering for allocations and program structuring.

🔹 ProgramCourse
Purpose:
Represents a course offering under a specific program, semester, level, and bulletin.

Key Fields:
program_id, course_id, semester_id, level_id, bulletin_id

units: Credit units of the course

grouping_enabled: Whether the course can be split into groups for allocation

Relationships:
Belongs to Program, Course, Semester, Level, and Bulletin

One-to-many with CourseAllocation

Why It Matters:
This model is the core link that defines where, when, and under which curriculum a course exists — enabling reuse, versioning, and allocation per session.

🔹 AcademicSession
Purpose:
Represents an academic session (e.g., 2024/2025) during which allocations occur.

Key Fields:
name, is_active: Session identifier and flag

Relationships:
One-to-many with CourseAllocation

Why It Matters:
Enables session-based allocation tracking and historical views of who taught what, when.

🔹 User
Purpose:
Represents all system users: lecturers, HODs, and superadmins.

Key Fields:
name, email, role: User identity and access level

department_id: Optional, null for superadmins

Roles Supported:
superadmin: Global access, can initialize sessions

hod: Manages allocations for their department

lecturer: Receives course allocations

Relationships:
One-to-many with CourseAllocation

Why It Matters:
Supports fine-grained, role-based access and lecturer-course assignments.

🔹 CourseAllocation
Purpose:
Defines the actual allocation of a lecturer to a course (optionally to a group within the course) for a session.

Key Fields:
program_course_id, session_id, lecturer_id

group_name: Optional (e.g., "Group A", null if no groups)

is_lead: Flags the main lecturer among grouped allocations

is_special_allocation: True if the course was selected from a previous bulletin

source_bulletin_id: Points to the bulletin the course was pulled from

Constraints:
Composite uniqueness: (program_course_id, session_id, group_name) ensures no group duplication

Why It Matters:
Tracks actual delivery of courses — including:

Multi-lecturer support

Special allocations from previous bulletins

Group-based assignments

Lead lecturer designation

✅ Conclusion: System Strengths
🔁 Curriculum Versioning: Bulletins allow for flexible, historical curriculum tracking.

👥 Lecturer Grouping: Supports team-teaching and group splitting for large classes.

📊 Session-Based Allocation: Keeps history of each academic year cleanly organized.

🧱 Role-Based Access: Differentiates between admin, HODs, and lecturers.

🔄 Allocation Reuse: Facilitates copying from previous sessions when needed.