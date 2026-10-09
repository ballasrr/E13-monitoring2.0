"""Таблица неудачных попыток входа

Счётчик переехал из памяти процесса в базу: на сервере приложение
работает в нескольких рабочих процессах, и у каждого был свой счётчик.

Revision ID: c1a7e4b90f12
Revises: d9836f6b0ee1
Create Date: 2026-10-09
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "c1a7e4b90f12"
down_revision: Union[str, Sequence[str], None] = "d9836f6b0ee1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        # 45 символов — предел для записи адреса IPv6 текстом.
        sa.Column("ip", sa.String(length=45), nullable=False),
        sa.Column("login", sa.String(length=160), server_default="", nullable=False),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Индекс составной: запросы всегда вида «попытки с этого адреса
    # за последние N минут», и порядок колонок здесь существенен.
    op.create_index(
        "ix_login_attempts_ip_time", "login_attempts", ["ip", "attempted_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_login_attempts_ip_time", table_name="login_attempts")
    op.drop_table("login_attempts")
