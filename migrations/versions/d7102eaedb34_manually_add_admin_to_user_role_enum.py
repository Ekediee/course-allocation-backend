"""Manually add admin to user role enum

Revision ID: d7102eaedb34
Revises: 82a88aa8df82
Create Date: 2025-11-18 17:46:02.073794

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7102eaedb34'
down_revision = '82a88aa8df82'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE user MODIFY COLUMN role ENUM('superadmin', 'admin', 'vetter', 'hod', 'lecturer') NULL")


def downgrade():
    op.execute("ALTER TABLE user MODIFY COLUMN role ENUM('superadmin', 'vetter', 'hod', 'lecturer') NULL")
