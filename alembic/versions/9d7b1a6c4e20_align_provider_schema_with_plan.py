"""align provider schema with canonical plan

Revision ID: 9d7b1a6c4e20
Revises: 4c1e7e3415cb
Create Date: 2026-10-25 22:21:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9d7b1a6c4e20"
down_revision: Union[str, Sequence[str], None] = "4c1e7e3415cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "services_provider_profile_id_fkey",
        "services",
        type_="foreignkey",
    )
    op.drop_index("ix_services_provider_profile_id", table_name="services")
    op.execute(
        """
        UPDATE services
        SET provider_profile_id = provider_profiles.user_id
        FROM provider_profiles
        WHERE services.provider_profile_id = provider_profiles.id
        """
    )

    op.drop_constraint("provider_profiles_pkey", "provider_profiles", type_="primary")
    op.drop_constraint(
        "provider_profiles_user_id_key",
        "provider_profiles",
        type_="unique",
    )
    op.add_column(
        "provider_profiles",
        sa.Column("display_name", sa.String(length=255), nullable=True),
    )
    op.execute(
        """
        UPDATE provider_profiles
        SET display_name = users.full_name
        FROM users
        WHERE provider_profiles.user_id = users.id
        """
    )
    op.alter_column("provider_profiles", "display_name", nullable=False)
    op.drop_column("provider_profiles", "id")
    op.create_primary_key(
        "provider_profiles_pkey",
        "provider_profiles",
        ["user_id"],
    )

    op.alter_column(
        "services",
        "provider_profile_id",
        new_column_name="provider_id",
    )
    op.drop_column("services", "description")
    op.add_column(
        "services",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "services_provider_id_fkey",
        "services",
        "provider_profiles",
        ["provider_id"],
        ["user_id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_services_provider_id",
        "services",
        ["provider_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_services_provider_id", table_name="services")
    op.drop_constraint("services_provider_id_fkey", "services", type_="foreignkey")
    op.add_column(
        "provider_profiles",
        sa.Column("id", sa.Uuid(), nullable=True),
    )
    op.execute("UPDATE provider_profiles SET id = gen_random_uuid()")
    op.alter_column("provider_profiles", "id", nullable=False)
    op.drop_constraint("provider_profiles_pkey", "provider_profiles", type_="primary")
    op.create_primary_key("provider_profiles_pkey", "provider_profiles", ["id"])
    op.create_unique_constraint(
        "provider_profiles_user_id_key",
        "provider_profiles",
        ["user_id"],
    )

    op.alter_column(
        "services",
        "provider_id",
        new_column_name="provider_profile_id",
    )
    op.execute(
        """
        UPDATE services
        SET provider_profile_id = provider_profiles.id
        FROM provider_profiles
        WHERE services.provider_profile_id = provider_profiles.user_id
        """
    )
    op.drop_column("services", "is_active")
    op.add_column("services", sa.Column("description", sa.Text(), nullable=True))
    op.create_foreign_key(
        "services_provider_profile_id_fkey",
        "services",
        "provider_profiles",
        ["provider_profile_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_services_provider_profile_id",
        "services",
        ["provider_profile_id"],
        unique=False,
    )
    op.drop_column("provider_profiles", "display_name")
