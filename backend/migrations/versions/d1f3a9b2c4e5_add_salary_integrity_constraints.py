"""add salary integrity constraints

Revision ID: d1f3a9b2c4e5
Revises: 9cfeb8603f89
"""

from alembic import op

revision = "d1f3a9b2c4e5"
down_revision = "9cfeb8603f89"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("employees") as batch_op:
        batch_op.create_check_constraint(
            "ck_employee_left_on_after_hired_on",
            "left_on IS NULL OR left_on >= hired_on",
        )

    with op.batch_alter_table("compensation_records") as batch_op:
        batch_op.create_check_constraint(
            "ck_compensation_amount_positive",
            "amount_minor > 0",
        )
        batch_op.create_check_constraint(
            "ck_compensation_base_amount_positive",
            "base_amount_minor > 0",
        )
        batch_op.create_check_constraint(
            "ck_compensation_fx_rate_positive",
            "fx_rate_micros > 0",
        )

    with op.batch_alter_table("salary_bands") as batch_op:
        batch_op.create_check_constraint(
            "ck_salary_band_ordered_positive",
            "min_minor > 0 AND min_minor <= mid_minor AND mid_minor <= max_minor",
        )


def downgrade() -> None:
    with op.batch_alter_table("salary_bands") as batch_op:
        batch_op.drop_constraint(
            "ck_salary_band_ordered_positive",
            type_="check",
        )

    with op.batch_alter_table("compensation_records") as batch_op:
        batch_op.drop_constraint(
            "ck_compensation_fx_rate_positive",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_compensation_base_amount_positive",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_compensation_amount_positive",
            type_="check",
        )

    with op.batch_alter_table("employees") as batch_op:
        batch_op.drop_constraint(
            "ck_employee_left_on_after_hired_on",
            type_="check",
        )