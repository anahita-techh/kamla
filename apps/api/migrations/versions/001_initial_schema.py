from alembic import op

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(_UPGRADE_SQL)


def downgrade() -> None:
    op.execute(_DOWNGRADE_SQL)


_DOWNGRADE_SQL = """
DROP FUNCTION IF EXISTS ensure_user(text, text);
DROP TABLE IF EXISTS audit_events CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS recommendations CASCADE;
DROP TABLE IF EXISTS study_sessions CASCADE;
DROP TABLE IF EXISTS study_plan_versions CASCADE;
DROP TABLE IF EXISTS study_plans CASCADE;
DROP TABLE IF EXISTS constraints CASCADE;
DROP TABLE IF EXISTS goals CASCADE;
DROP TABLE IF EXISTS pyq_question_topics CASCADE;
DROP TABLE IF EXISTS pyq_questions CASCADE;
DROP TABLE IF EXISTS pyq_papers CASCADE;
DROP TABLE IF EXISTS topic_progress CASCADE;
DROP TABLE IF EXISTS topics CASCADE;
DROP TABLE IF EXISTS assignments CASCADE;
DROP TABLE IF EXISTS exams CASCADE;
DROP TABLE IF EXISTS attendance_records CASCADE;
DROP TABLE IF EXISTS attendance_summaries CASCADE;
DROP TABLE IF EXISTS timetable_exceptions CASCADE;
DROP TABLE IF EXISTS timetable_entries CASCADE;
DROP TABLE IF EXISTS subjects CASCADE;
DROP TABLE IF EXISTS semesters CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;
"""


_UPGRADE_SQL = r"""
-- Roles (optional; ignored if not permitted). Application DML should use kamla_app (NOBYPASSRLS).
-- Migrations/DDL should use kamla_migrator (BYPASSRLS).
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kamla_migrator') THEN
    CREATE ROLE kamla_migrator NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kamla_app') THEN
    CREATE ROLE kamla_app NOLOGIN;
  END IF;
  BEGIN
    ALTER ROLE kamla_migrator BYPASSRLS;
  EXCEPTION WHEN insufficient_privilege THEN
    NULL;
  END;
  BEGIN
    ALTER ROLE kamla_app NOBYPASSRLS;
  EXCEPTION WHEN insufficient_privilege THEN
    NULL;
  END;
EXCEPTION WHEN insufficient_privilege THEN
  NULL;
END $$;

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id TEXT NOT NULL UNIQUE,
  email TEXT,
  timezone TEXT,
  onboarding_completed_at TIMESTAMPTZ,
  billing_status TEXT,
  deleted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE profiles (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  display_name TEXT,
  college TEXT,
  degree TEXT,
  sleep_hours_min INTEGER NOT NULL DEFAULT 7,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE semesters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  is_current BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX semesters_user_id_idx ON semesters (user_id);
CREATE UNIQUE INDEX semesters_one_current ON semesters (user_id) WHERE is_current;

CREATE TABLE subjects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  semester_id UUID NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  code TEXT,
  attendance_threshold_pct NUMERIC(5, 2) NOT NULL DEFAULT 75,
  attendance_source TEXT NOT NULL DEFAULT 'manual_counts',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT subjects_attendance_source_check CHECK (attendance_source IN ('manual_counts', 'per_session')),
  CONSTRAINT subjects_threshold_check CHECK (attendance_threshold_pct >= 0 AND attendance_threshold_pct <= 100)
);
CREATE INDEX subjects_user_id_idx ON subjects (user_id);
CREATE INDEX subjects_user_semester_idx ON subjects (user_id, semester_id);

CREATE TABLE timetable_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  day_of_week INTEGER NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  location TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT timetable_dow_check CHECK (day_of_week >= 0 AND day_of_week <= 6)
);
CREATE INDEX timetable_entries_user_id_idx ON timetable_entries (user_id);

CREATE TABLE timetable_exceptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
  exception_date DATE NOT NULL,
  kind TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT timetable_exceptions_kind_check CHECK (kind IN ('cancelled', 'holiday', 'extra'))
);
CREATE INDEX timetable_exceptions_user_id_idx ON timetable_exceptions (user_id);

CREATE TABLE attendance_summaries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  classes_attended INTEGER NOT NULL,
  classes_conducted INTEGER NOT NULL,
  as_of DATE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT attendance_summaries_user_subject_key UNIQUE (user_id, subject_id),
  CONSTRAINT attendance_attended_check CHECK (classes_attended >= 0),
  CONSTRAINT attendance_conducted_check CHECK (classes_conducted >= 0),
  CONSTRAINT attendance_attended_lte_conducted_check CHECK (classes_attended <= classes_conducted)
);
CREATE INDEX attendance_summaries_user_id_idx ON attendance_summaries (user_id);

CREATE TABLE attendance_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  session_date DATE NOT NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT attendance_records_status_check CHECK (status IN ('attended', 'absent', 'excused', 'cancelled'))
);
CREATE INDEX attendance_records_user_id_idx ON attendance_records (user_id);

CREATE TABLE exams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  exam_at TIMESTAMPTZ NOT NULL,
  kind TEXT NOT NULL DEFAULT 'other',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT exams_kind_check CHECK (kind IN ('ca', 'midsem', 'endsem', 'other'))
);
CREATE INDEX exams_user_id_idx ON exams (user_id);
CREATE INDEX exams_user_exam_at_idx ON exams (user_id, exam_at);

CREATE TABLE assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  due_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX assignments_user_id_idx ON assignments (user_id);
CREATE INDEX assignments_user_due_at_idx ON assignments (user_id, due_at);

CREATE TABLE topics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  syllabus_ref TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX topics_user_id_idx ON topics (user_id);

CREATE TABLE topic_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic_id UUID NOT NULL UNIQUE REFERENCES topics(id) ON DELETE CASCADE,
  completion_pct INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT topic_progress_pct_check CHECK (completion_pct >= 0 AND completion_pct <= 100)
);
CREATE INDEX topic_progress_user_id_idx ON topic_progress (user_id);

CREATE TABLE pyq_papers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  original_filename TEXT NOT NULL,
  r2_key TEXT NOT NULL,
  content_type TEXT NOT NULL,
  byte_size INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'uploaded',
  processing_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pyq_papers_status_check CHECK (status IN ('uploaded', 'scanning', 'processing', 'ready', 'failed')),
  CONSTRAINT pyq_papers_size_check CHECK (byte_size > 0 AND byte_size <= 10485760)
);
CREATE INDEX pyq_papers_user_id_idx ON pyq_papers (user_id);

CREATE TABLE pyq_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  paper_id UUID NOT NULL REFERENCES pyq_papers(id) ON DELETE CASCADE,
  question_no TEXT,
  prompt_text TEXT NOT NULL,
  marks NUMERIC(6, 2),
  year INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX pyq_questions_user_id_idx ON pyq_questions (user_id);

CREATE TABLE pyq_question_topics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES pyq_questions(id) ON DELETE CASCADE,
  topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  confidence NUMERIC(4, 3) NOT NULL,
  source TEXT NOT NULL,
  reviewed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pyq_question_topics_source_check CHECK (source IN ('llm', 'user')),
  CONSTRAINT pyq_question_topics_confidence_check CHECK (confidence >= 0 AND confidence <= 1)
);
CREATE INDEX pyq_question_topics_user_id_idx ON pyq_question_topics (user_id);

CREATE TABLE goals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  desired_hours_per_week NUMERIC(6, 2) NOT NULL,
  priority INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX goals_user_id_idx ON goals (user_id);

CREATE TABLE constraints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  type TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT constraints_kind_check CHECK (kind IN ('hard', 'soft')),
  CONSTRAINT constraints_type_check CHECK (type IN ('attendance_min', 'sleep_min', 'fixed_busy', 'hours_target', 'custom'))
);
CREATE INDEX constraints_user_id_idx ON constraints (user_id);

CREATE TABLE study_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  semester_id UUID NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT study_plans_status_check CHECK (status IN ('active', 'archived'))
);
CREATE INDEX study_plans_user_id_idx ON study_plans (user_id);

CREATE TABLE study_plan_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  created_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT study_plan_versions_plan_ver UNIQUE (plan_id, version)
);
CREATE INDEX study_plan_versions_user_id_idx ON study_plan_versions (user_id);

CREATE TABLE study_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_version_id UUID NOT NULL REFERENCES study_plan_versions(id) ON DELETE CASCADE,
  goal_id UUID REFERENCES goals(id) ON DELETE SET NULL,
  topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
  starts_at TIMESTAMPTZ NOT NULL,
  ends_at TIMESTAMPTZ NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'planned',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT study_sessions_status_check CHECK (status IN ('planned', 'done', 'skipped'))
);
CREATE INDEX study_sessions_user_id_idx ON study_sessions (user_id);

CREATE TABLE recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'pending',
  kind TEXT NOT NULL,
  reason TEXT NOT NULL,
  evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
  proposed_action JSONB NOT NULL DEFAULT '{}'::jsonb,
  disclosures JSONB NOT NULL DEFAULT '{}'::jsonb,
  accepted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT recommendations_status_check CHECK (status IN ('pending', 'accepted', 'rejected', 'modified'))
);
CREATE INDEX recommendations_user_id_idx ON recommendations (user_id);

CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX conversations_user_id_idx ON conversations (user_id);

CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  content_text TEXT NOT NULL,
  structured_payload JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT messages_role_check CHECK (role IN ('user', 'assistant', 'system'))
);
CREATE INDEX messages_user_id_idx ON messages (user_id);
CREATE INDEX messages_user_created_at_idx ON messages (user_id, created_at);

CREATE TABLE audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id UUID,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX audit_events_user_id_idx ON audit_events (user_id);

CREATE OR REPLACE FUNCTION ensure_user(p_clerk_user_id text, p_email text)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
SET row_security = off
AS $$
DECLARE
  v_id uuid;
BEGIN
  SELECT id INTO v_id FROM users WHERE clerk_user_id = p_clerk_user_id;
  IF v_id IS NOT NULL THEN
    UPDATE users
    SET email = COALESCE(p_email, email), updated_at = now()
    WHERE id = v_id;
    INSERT INTO profiles (user_id)
    VALUES (v_id)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN v_id;
  END IF;
  INSERT INTO users (clerk_user_id, email)
  VALUES (p_clerk_user_id, p_email)
  RETURNING id INTO v_id;
  INSERT INTO profiles (user_id) VALUES (v_id);
  RETURN v_id;
END;
$$;

REVOKE ALL ON FUNCTION ensure_user(text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION ensure_user(text, text) TO PUBLIC;

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;
CREATE POLICY users_isolation ON users
  USING (id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
  WITH CHECK (id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);

DO $$
DECLARE
  t text;
  tables text[] := ARRAY[
    'profiles', 'semesters', 'subjects', 'timetable_entries', 'timetable_exceptions',
    'attendance_summaries', 'attendance_records', 'exams', 'assignments', 'topics',
    'topic_progress', 'pyq_papers', 'pyq_questions', 'pyq_question_topics', 'goals',
    'constraints', 'study_plans', 'study_plan_versions', 'study_sessions',
    'recommendations', 'conversations', 'messages', 'audit_events'
  ];
BEGIN
  FOREACH t IN ARRAY tables LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format(
      'CREATE POLICY %I ON %I FOR ALL USING (user_id = NULLIF(current_setting(''app.current_user_id'', true), '''')::uuid) WITH CHECK (user_id = NULLIF(current_setting(''app.current_user_id'', true), '''')::uuid)',
      t || '_isolation',
      t
    );
  END LOOP;
END $$;

DO $$
BEGIN
  GRANT USAGE ON SCHEMA public TO kamla_app;
  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO kamla_app;
  GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO kamla_app;
  GRANT EXECUTE ON FUNCTION ensure_user(text, text) TO kamla_app;
EXCEPTION WHEN undefined_object OR insufficient_privilege THEN
  NULL;
END $$;
"""
