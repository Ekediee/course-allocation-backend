
import argparse
from app import create_app, db
from app.models import User

def create_admin(name, email, password):
    """Creates a new superadmin user."""
    app = create_app()
    with app.app_context():
        if User.query.filter_by(email=email).first():
            print(f"Error: User with email '{email}' already exists.")
            return

        new_admin = User(
            name=name,
            email=email,
            role='superadmin'
        )
        new_admin.set_password(password)
        
        db.session.add(new_admin)
        db.session.commit()
        print(f"Successfully created superadmin user: {name} ({email})")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a new superadmin user.')
    parser.add_argument('name', type=str, help='The full name of the admin user.')
    parser.add_argument('email', type=str, help='The email address of the admin user.')
    parser.add_argument('password', type=str, help='The password for the admin user.')

    args = parser.parse_args()
    
    create_admin(args.name, args.email, args.password)
