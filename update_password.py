from app import db
from app.models import User

users = User.query.all()
for user in users:
    if not user.password:
        user.set_password("defaultd123")
db.session.commit()

print("All users updated with default passwords.")
