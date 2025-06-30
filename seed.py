from app import create_app, db
from icecream import ic
from app.models.models import Semester, Level, User

app = create_app()
with app.app_context():
    levels = ['100L', '200L', '300L', '400L', '500L', '600L']
    semesters = ['First Semester', 'Second Semester']

    for name in levels:
        if not Level.query.filter_by(name=name).first():
            db.session.add(Level(name=name))

    for name in semesters:
        if not Semester.query.filter_by(name=name).first():
            db.session.add(Semester(name=name))

    # Add superadmin (no department)
    superadmin = User(
        name='System Admin',
        email='alloc_admin@babcock.edu.ng',
        role='superadmin',
        department_id=None
    )
    if not User.query.filter_by(name='System Admin').first():
        db.session.add(superadmin)

    # Add vetter (no department)
    vetter = User(
        name='Vetter',
        email='alloc_vetter@babcock.edu.ng',
        role='vetter',
        department_id=None
    )
    if not User.query.filter_by(name='Vetter').first():
        db.session.add(vetter)

    db.session.commit()
    ic("Levels and Semesters seeded.")
