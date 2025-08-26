feat: Implement Course Management API Endpoints

This commit introduces the backend API for managing courses, including fetching,
creating single courses, and batch uploading courses via CSV.

Key changes include:
- Added `GET /api/v1/courses` to retrieve all courses with related program,
  specialization, bulletin, and level information.
- Added `POST /api/v1/courses` to create a single course, with validation
  for required fields and uniqueness of course code.
- Added `POST /api/v1/courses/batch` for bulk course creation from CSV files,
  supporting partial success with error reporting for invalid rows.
- Created `app/services/course_service.py` to centralize course-related
  business logic, adhering to the project's service layer guidelines.
- Implemented `app/routes/course_routes.py` to define the new API endpoints
  and integrate with the course service.
- Registered the new `course_bp` blueprint in `app/__init__.py`.
- Developed `tests/test_course_routes.py` with unit and integration tests
  covering all new endpoints, ensuring functionality and robustness.
- Corrected a CSV parsing bug in `batch_create_courses` service function.
