"""create users documents chunks tables

Revision ID: a94b7da99076
Revises: 
Create Date: 2026-10-23 15:50:04.485537

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'a94b7da99076'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Embedding dimension for all-MiniLM-L6-v2
EMBEDDING_DIM = 384


def upgrade() -> None:
    """Create the core tables: users, documents, chunks."""

    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(1024), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, index=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("extracted_text", sa.Text, nullable=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("page_number", sa.Integer, nullable=True),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Drop the core tables."""
    op.drop_table("chunks")
    op.drop_table("documents")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
