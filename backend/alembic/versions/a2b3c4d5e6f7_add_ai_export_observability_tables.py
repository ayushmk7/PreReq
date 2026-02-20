"""add ai, export, observability tables

Revision ID: a2b3c4d5e6f7
Revises: 75cc9c04410b
Create Date: 2026-02-20 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = '75cc9c04410b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to existing tables
    op.add_column('concept_graphs', sa.Column('annotation', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('question_text', sa.Text(), nullable=True))
    op.add_column('readiness_results', sa.Column('run_id', sa.UUID(), nullable=True))
    op.add_column('class_aggregates', sa.Column('run_id', sa.UUID(), nullable=True))
    op.add_column('clusters', sa.Column('run_id', sa.UUID(), nullable=True))
    op.add_column('parameters', sa.Column('k', sa.Integer(), nullable=False, server_default='4'))

    # Compute runs
    op.create_table('compute_runs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exam_id', sa.UUID(), nullable=False),
        sa.Column('run_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('students_processed', sa.Integer(), nullable=True),
        sa.Column('concepts_processed', sa.Integer(), nullable=True),
        sa.Column('parameters_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('graph_version', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id'),
    )

    # Intervention results
    op.create_table('intervention_results',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exam_id', sa.UUID(), nullable=False),
        sa.Column('run_id', sa.UUID(), nullable=True),
        sa.Column('concept_id', sa.String(length=255), nullable=False),
        sa.Column('students_affected', sa.Integer(), nullable=False),
        sa.Column('downstream_concepts', sa.Integer(), nullable=False),
        sa.Column('current_readiness', sa.Float(), nullable=False),
        sa.Column('impact', sa.Float(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('suggested_format', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # AI suggestions
    op.create_table('ai_suggestions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exam_id', sa.UUID(), nullable=False),
        sa.Column('suggestion_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('input_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('prompt_version', sa.String(length=50), nullable=True),
        sa.Column('request_id', sa.UUID(), nullable=False),
        sa.Column('token_usage', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('validation_errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('reviewed_by', sa.String(length=255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_note', sa.Text(), nullable=True),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.Column('before_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('after_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Audit log
    op.create_table('audit_log',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exam_id', sa.UUID(), nullable=True),
        sa.Column('actor', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=255), nullable=True),
        sa.Column('before_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('after_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Export runs
    op.create_table('export_runs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exam_id', sa.UUID(), nullable=False),
        sa.Column('compute_run_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('file_checksum', sa.String(length=64), nullable=True),
        sa.Column('manifest_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('export_runs')
    op.drop_table('audit_log')
    op.drop_table('ai_suggestions')
    op.drop_table('intervention_results')
    op.drop_table('compute_runs')
    op.drop_column('parameters', 'k')
    op.drop_column('clusters', 'run_id')
    op.drop_column('class_aggregates', 'run_id')
    op.drop_column('readiness_results', 'run_id')
    op.drop_column('questions', 'question_text')
    op.drop_column('concept_graphs', 'annotation')
