# Audit Log Feature — Implementation Plan

## Overview

Add a database-backed audit log that records every significant user action across the system. The log will capture *who* did *what*, *when*, and on *which resource*, providing a full trail for accountability and debugging.

---

## Open Questions for Your Approval

> [Flashing Notice: IMPORTANT]
> Please answer these before I proceed — they affect the design directly.

1. **Which actions should be logged?**
   Below is the proposed list. Please confirm or remove any:
   - `LOGIN` — user logs in (auth/login)
   - `SESSION_CREATED` — new academic session initialized
   - `SESSION_ACTIVATED` — an existing session switched to active
   - `BULLETIN_CREATED` — new bulletin created
   - `BULLETIN_ACTIVATED` — bulletin switched to active
   - `SEMESTER_STATUS_CHANGED` — first/second/summer semester enabled or disabled
   - `COURSE_ALLOCATED` — a course is allocated to a lecturer
   - `ALLOCATION_UPDATED` — an existing allocation is modified
   - `ALLOCATION_DELETED` — an allocation is removed
   - `ALLOCATION_SUBMITTED` — department HOD submits allocations for a semester
   - `ALLOCATION_VETTED` — vetter approves a department's allocations
   - `ALLOCATION_PUSHED_TO_UMIS` — allocations pushed to UMIS
   - `COURSE_ADDED_TO_CURRICULUM` — ProgramCourse record created
   - `COURSE_REMOVED_FROM_CURRICULUM` — ProgramCourse record deleted

2. **Who can view the audit logs?**
   I'm proposing `superadmin` and `vetter` only. Should `hod` also have access (filtered to their own department's actions)?

3. **Should IP address be captured?**
   This is useful for security auditing. Flask can read it from `request.remote_addr`. Yes or no?

---

## Proposed Changes

### Component 1 — Data Model

---

#### [MODIFY] [models.py](file:///c:/Users/HP/projects/course-allocation-backend/app/models/models.py)

Add a new `AuditLog` model at the bottom of the file:

```python
class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # nullable for system actions
    action = db.Column(db.String(60), nullable=False)           # e.g. "COURSE_ALLOCATED"
    resource_type = db.Column(db.String(60), nullable=True)     # e.g. "CourseAllocation"
    resource_id = db.Column(db.String(60), nullable=True)       # e.g. "42"
    details = db.Column(db.Text, nullable=True)                 # JSON string with extra context
    ip_address = db.Column(db.String(45), nullable=True)        # IPv4/IPv6
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    user = db.relationship('User', backref='audit_logs')
```

**Field rationale:**
- `action` — a short UPPER_SNAKE_CASE string, easy to filter/query
- `resource_type` + `resource_id` — identifies the target record (generic, avoids one FK per resource type)
- `details` — a JSON blob for rich context (e.g., `{"bulletin_id": 3, "bulletin_name": "2023–2027"}`)
- `user_id` is nullable to allow future system-triggered log entries

#### [MODIFY] [models/__init__.py](file:///c:/Users/HP/projects/course-allocation-backend/app/models/__init__.py)

Export `AuditLog` from the package:
```python
from .models import (
    ..., AuditLog  # added
)
```

---

### Component 2 — Service Layer

---

#### [NEW] `app/services/audit_service.py`

A single `log_action()` helper that any route or service can call:

```python
import json
from app import db
from app.models.models import AuditLog
from datetime import datetime, timezone

def log_action(
    action: str,
    user_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None
):
    """
    Persists a single audit log entry to the database.
    Safe to call inside an existing db.session — does NOT commit on its own.
    The caller is responsible for committing the parent transaction.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(entry)
```

> [!NOTE]
> `log_action()` intentionally does **not** call `db.session.commit()`. It adds the entry to the current session so it commits atomically with the parent action. This means if the parent transaction rolls back, the audit log entry also rolls back — preventing phantom log entries for failed actions.

---

### Component 3 — Route Integration

---

The following files receive explicit `log_action()` calls **only at the lines where the DB commit happens**, adding minimal code to each:

#### [MODIFY] [session_routes.py](file:///c:/Users/HP/projects/course-allocation-backend/app/routes/session_routes.py)
- `initialize_session()` → log `SESSION_CREATED`
- `update_session()` → log `SESSION_ACTIVATED`

#### [MODIFY] [bulletin_route.py](file:///c:/Users/HP/projects/course-allocation-backend/app/routes/bulletin_route.py)
- `create_bulletin()` → log `BULLETIN_CREATED`

#### [MODIFY] [admin_user_routes.py](file:///c:/Users/HP/projects/course-allocation-backend/app/routes/admin_user_routes.py)
- `set_first_semester_status()` → log `SEMESTER_STATUS_CHANGED`
- `set_second_semester_status()` → log `SEMESTER_STATUS_CHANGED`
- `set_summer_semester_status()` → log `SEMESTER_STATUS_CHANGED`

#### [MODIFY] [auth/routes.py](file:///c:/Users/HP/projects/course-allocation-backend/app/auth/routes.py)
- `login()` → log `LOGIN` (only on successful login, before returning response)

#### [MODIFY] [allocation_service.py](file:///c:/Users/HP/projects/course-allocation-backend/app/services/allocation_service.py)
- Allocation create → log `COURSE_ALLOCATED`
- Allocation update → log `ALLOCATION_UPDATED`
- Allocation delete → log `ALLOCATION_DELETED`
- Submission → log `ALLOCATION_SUBMITTED`
- Vetting → log `ALLOCATION_VETTED`
- UMIS push → log `ALLOCATION_PUSHED_TO_UMIS`

---

### Component 4 — Query API

---

#### [NEW] `app/routes/audit_routes.py`

Two read-only endpoints:

| Method | URL | Description |
|---|---|---|
| `GET` | `/api/v1/audit-logs/` | Paginated list of all audit logs. Supports `?action=`, `?user_id=`, `?page=`, `?per_page=` filters. Restricted to `superadmin` / `vetter`. |
| `GET` | `/api/v1/audit-logs/<int:user_id>` | All actions by a specific user. |

Response shape per entry:
```json
{
  "id": 1,
  "action": "COURSE_ALLOCATED",
  "user": { "id": 5, "name": "Dr. Adebayo" },
  "resource_type": "CourseAllocation",
  "resource_id": "42",
  "details": { "course_code": "CSC301", "semester": "First Semester" },
  "ip_address": "102.89.0.1",
  "created_at": "2026-07-08T11:14:00Z"
}
```

#### [MODIFY] [app/__init__.py](file:///c:/Users/HP/projects/course-allocation-backend/app/__init__.py)
Register the new `audit_bp` blueprint at `/api/v1/audit-logs`.

---

### Component 5 — Database Migration

---

Run after all code is in place:
```bash
flask db migrate -m "Add AuditLog model"
flask db upgrade
```

---

### Component 6 — Tests

---

#### [NEW] `tests/test_audit_log.py`

Tests to cover:
- `log_action()` correctly persists a record when called inside a transaction
- `log_action()` rolls back cleanly if the parent transaction fails
- `GET /api/v1/audit-logs/` returns paginated results for superadmin
- `GET /api/v1/audit-logs/` returns 403 for non-admin users
- Calling `initialize_session()` creates a `SESSION_CREATED` audit entry
- Calling `login()` creates a `LOGIN` audit entry

---

### Component 7 — Documentation

---

#### [MODIFY] [model_document.md](file:///c:/Users/HP/projects/course-allocation-backend/model_document.md)
Add the `AuditLog` model to the documentation per the project rules.

---

## Verification Plan

### Automated Tests
```bash
pytest tests/test_audit_log.py -v
```

### Manual Verification
1. Activate a session on local dev → check `audit_log` table for a `SESSION_CREATED` row
2. Call `GET /api/v1/audit-logs/` as superadmin → confirm paginated response
3. Call `GET /api/v1/audit-logs/` as a lecturer → confirm 403

---

## Summary of Files Affected

| File | Change |
|---|---|
| `app/models/models.py` | Add `AuditLog` model class |
| `app/models/__init__.py` | Export `AuditLog` |
| `app/services/audit_service.py` | **NEW** — `log_action()` helper |
| `app/routes/audit_routes.py` | **NEW** — query API endpoints |
| `app/routes/session_routes.py` | Add 2 `log_action()` calls |
| `app/routes/bulletin_route.py` | Add 1 `log_action()` call |
| `app/routes/admin_user_routes.py` | Add 3 `log_action()` calls |
| `app/auth/routes.py` | Add 1 `log_action()` call |
| `app/services/allocation_service.py` | Add ~6 `log_action()` calls |
| `app/__init__.py` | Register `audit_bp` blueprint |
| `model_document.md` | Document new model |
| `tests/test_audit_log.py` | **NEW** — test suite |
