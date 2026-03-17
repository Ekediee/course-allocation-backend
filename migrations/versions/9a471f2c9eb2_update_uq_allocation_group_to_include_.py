"""Update uq_allocation_group to include semester_id

Revision ID: 9a471f2c9eb2
Revises: c77ba5335823
Create Date: 2026-03-17 12:00:21.356500

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a471f2c9eb2'
down_revision = 'c77ba5335823'
branch_labels = None
depends_on = None


def upgrade():
    # Disable foreign key checks to allow dropping the constraint
    op.execute('SET FOREIGN_KEY_CHECKS=0;')
    
    # Drop the old unique constraint
    op.execute('ALTER TABLE course_allocation DROP INDEX uq_allocation_group;')
    
    # Create the new unique constraint with semester_id
    op.execute('ALTER TABLE course_allocation ADD UNIQUE KEY uq_allocation_group (program_course_id, session_id, semester_id, group_name);')
    
    # Re-enable foreign key checks
    op.execute('SET FOREIGN_KEY_CHECKS=1;')


def downgrade():
    # Disable foreign key checks to allow dropping the constraint
    op.execute('SET FOREIGN_KEY_CHECKS=0;')
    
    # Revert back to the original unique constraint (without semester_id)
    op.execute('ALTER TABLE course_allocation DROP INDEX uq_allocation_group;')
    op.execute('ALTER TABLE course_allocation ADD UNIQUE KEY uq_allocation_group (program_course_id, session_id, group_name);')
    
    # Re-enable foreign key checks
    op.execute('SET FOREIGN_KEY_CHECKS=1;')
