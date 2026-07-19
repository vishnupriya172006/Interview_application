"""Create the InterviewGuard schema."""

from alembic import op
import sqlalchemy as sa

revision = "20260716_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("company_name", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "interviews",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("recruiter_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.Column("candidate_email", sa.String(length=255), nullable=False),
        sa.Column("meeting_id", sa.String(length=255), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("status", sa.String(length=50)),
        sa.Column("integrity_score", sa.Float()),
        sa.Column("risk_level", sa.String(length=50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_interviews_meeting_id", "interviews", ["meeting_id"], unique=True)
    for name, columns in {
        "monitoring_events": [sa.Column("event_type", sa.String(length=50), nullable=False), sa.Column("severity", sa.String(length=20), nullable=False), sa.Column("details", sa.String(length=1000)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))],
        "deepfake_predictions": [sa.Column("score", sa.Float(), nullable=False), sa.Column("label", sa.String(length=20), nullable=False)],
        "eye_gaze_logs": [sa.Column("horizontal_gaze", sa.Float()), sa.Column("vertical_gaze", sa.Float()), sa.Column("gaze_direction", sa.String(length=20), nullable=False), sa.Column("looking_away", sa.Boolean()), sa.Column("attention_score", sa.Float())],
        "phone_detection_logs": [sa.Column("phone_detected", sa.Boolean()), sa.Column("confidence", sa.Float()), sa.Column("count", sa.Integer())],
        "liveness_logs": [sa.Column("is_live", sa.Boolean()), sa.Column("blink_rate", sa.Float()), sa.Column("head_movement_score", sa.Float()), sa.Column("smile_score", sa.Float())],
    }.items():
        op.create_table(name, sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("interview_id", sa.String(length=36), sa.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False), sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()")), *columns)
    op.create_table("reports", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("interview_id", sa.String(length=36), sa.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False), sa.Column("pdf_path", sa.String(length=500), nullable=False), sa.Column("integrity_score", sa.Float(), nullable=False), sa.Column("risk_level", sa.String(length=20), nullable=False), sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")))


def downgrade() -> None:
    for table in ("reports", "liveness_logs", "phone_detection_logs", "eye_gaze_logs", "deepfake_predictions", "monitoring_events", "interviews"):
        op.drop_table(table)
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
