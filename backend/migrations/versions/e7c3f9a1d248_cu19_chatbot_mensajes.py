"""CU19: Atender Cliente con Chatbot -- tabla de mensajes por sesion

Revision ID: e7c3f9a1d248
Revises: d6b2e8a4c913
Create Date: 2026-09-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e7c3f9a1d248"
down_revision = "d6b2e8a4c913"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chatbot_mensaje",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chatbot_id", sa.Integer(), sa.ForeignKey("chatbot.id"), nullable=False),
        sa.Column("remitente", sa.String(length=10), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("fecha", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_chatbot_mensaje_chatbot_id", "chatbot_mensaje", ["chatbot_id"])


def downgrade() -> None:
    op.drop_index("ix_chatbot_mensaje_chatbot_id", table_name="chatbot_mensaje")
    op.drop_table("chatbot_mensaje")
