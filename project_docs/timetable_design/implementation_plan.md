# Implementation Plan: Timetable Backend API

## Goal Description
Build a **Standalone Timetable Backend API** to support a dedicated Timetable Frontend. This service will operate independently of the main Course Allocation System but share the same underlying database. It includes advanced scheduling features for **Lecturer Constraints** and **Smart Course Prioritization**.

## Architecture: Shared-Database, Separate API
We will implement a "Sidecar" architecture where the new service lives alongside the main one.

### Components
1.  **Course Allocation System (Existing)**:
    - Continues to manage Users, Courses, and Allocations.
    
2.  **Timetable Backend (New Flask App)**:
    - **Purpose**: Serves the Timetable Frontend.
    - **Database Access**: Read-Only access to core business data; Read-Write access to scheduling data.

## Advanced Data Models

### 1. New Scheduling Models
- `Room`: `id`, `name`, `capacity`, `type`
- `TimeSlot`: `id`, `day`, `start`, `end` (e.g., 8:00-9:00)
- `TimetableEntry`: `id`, `allocation_id`, `room_id`, `slot_id`

### 2. Constraint Models (New)
To handle the "Human Considerations".
- `LecturerConstraint`:
    - `lecturer_id`: ForeignKey
    - `day`: Enum (Mon-Fri)
    - `start_time`: Time (optional)
    - `end_time`: Time (optional)
    - `priority`: Enum (`HIGH` for hard constraints, `MEDIUM` for preferences)
    - `constraint_type`: Enum 
        - `BUSY`: Cannot teach (e.g., Study Leave, Day Off).
        - `PREFERRED`: Wants to teach (e.g., "Prefers Morning", "Prefers Evening").

## Algorithmic Strategy: Multi-Pass CSP
We will use a **Multi-Pass Strategy** with **Distribution Constraints**.

### Pass 1: Global Courses (GEDS/GST)
*   **Filter**: Select all allocations where Course Code starts with `GEDS` or `GST`.
*   **Hard Constraint 1**: Maximize room usage (large classes).
*   **Hard Constraint 2 (New)**: **Distribution Rule**. GEDS courses cannot consume more than X% (e.g., 50%) of available Morning Slots (8am - 12pm). This ensures room is left for departmental core courses.
*   **Optimization**: Spread GEDS courses evenly across the week/day to prevent bottlenecks.
*   **Output**: Fix these `TimetableEntries` as **Immutable** for the next pass.

### Pass 2: Departmental Courses (Per Department)
*   **Filter**: Select allocations for `Department A`.
*   **Constraint**: 
    - Respect **Hard Constraints** (Lecturer Busy slots, Room/Level double booking).
    - Respect **Immutable Slots** (slots taken by GEDS in Pass 1).
    - Respect **Lecturer Constraints** (Adjunct availability).
*   **Optimization (New)**: 
    - **Lecturer Preferences**: Prioritize assigning "Preferred" slots (e.g., Morning vs Evening) defined in `LecturerConstraint`.

## Proposed Changes

### 1. Directory Structure
```
projects/course-allocation-backend/
├── app/                  # Existing Main App (Migrations live here)
├── timetable_service/    # [NEW] Timetable Backend
│   ├── app.py            
│   ├── models/           # Shared models + Constraint models
│   ├── services/         
│   │   ├── solver.py     # OR-Tools Logic
│   │   └── passes/       # Logic for "Pass 1" vs "Pass 2"
│   └── routes/           # API Endpoints
```

### 2. Database Schema Updates (In Main App)
Add these models to `app/models/timetable.py` (and migrate via Main App):
*   `Room`, `TimeSlot`
*   `LecturerConstraint`
*   `TimetableEntry`

### 3. API Endpoints
- `POST /api/v1/constraints`: Lecturers/Admins set preferences (e.g., "I am on study leave Tuesdays").
- `POST /api/v1/generate/geds`: Triggers Pass 1 (Global).
- `POST /api/v1/generate/department`: Triggers Pass 2 (Departmental).
- `GET /api/v1/timetables`: Returns grid.

## User Review Required
- **Precedence**: Is it correct that *all* GEDS courses are fixed first? (This implies Dept courses *must* work around them).
- **Morning Cap**: We will set a default cap (e.g., max 50% of Rooms can be used by GEDS in the morning). Does this sound reasonable?
