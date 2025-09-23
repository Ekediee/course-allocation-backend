from app import db
from app.models import DepartmentAllocationState, AcademicSession, User
from datetime import datetime, timezone

def get_allocation_status(department_id, semester_id):
    """
    Checks if the allocation for a given department and semester is submitted for the active session.
    """
    session = AcademicSession.query.filter_by(is_active=True).first()
    if not session:
        return False, "No active session found."

    state = DepartmentAllocationState.query.filter_by(
        department_id=department_id,
        session_id=session.id,
        semester_id=semester_id
    ).first()

    return state.is_submitted if state else False, None

def submit_allocation(department_id, user_id, semester_id):
    """
    Submits the allocation for a department and semester for the active session.
    """
    session = AcademicSession.query.filter_by(is_active=True).first()
    if not session:
        return None, "No active academic session found."

    # Find or create the state
    state = DepartmentAllocationState.query.filter_by(
        department_id=department_id,
        session_id=session.id,
        semester_id=semester_id
    ).first()

    if not state:
        state = DepartmentAllocationState(
            department_id=department_id,
            session_id=session.id,
            semester_id=semester_id
        )
        db.session.add(state)
    
    if state.is_submitted:
        return None, "Allocations for this department and semester have already been submitted."

    state.is_submitted = True
    state.submitted_at = datetime.now(timezone.utc)
    state.submitted_by_id = user_id
    
    db.session.commit()
    return state, None

def unblock_allocation(department_id, semester_id):
    """
    Unblocks a department's allocation for a given semester in the active session.
    """
    session = AcademicSession.query.filter_by(is_active=True).first()
    if not session:
        return None, "No active academic session found."

    state = DepartmentAllocationState.query.filter_by(
        department_id=department_id,
        session_id=session.id,
        semester_id=semester_id
    ).first()

    if not state or not state.is_submitted:
        return None, "Allocations for this department and semester are not currently submitted."

    state.is_submitted = False
    db.session.commit()
    
    return state, None