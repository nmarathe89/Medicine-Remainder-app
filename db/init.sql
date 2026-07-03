-- Reference schema for the Mediminder web app.
-- NOTE: The FastAPI backend creates these tables automatically on startup via
-- SQLAlchemy (see backend/app/database.py::init_db). This file documents the
-- schema and can be used to provision a database manually if desired.

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(16) NOT NULL DEFAULT 'user',   -- user | admin
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS medicines (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name           VARCHAR(64) NOT NULL,
    dosage         INTEGER NOT NULL DEFAULT 0,             -- mg; 0 = unspecified
    medicine_type  VARCHAR(16) NOT NULL DEFAULT 'None',    -- Bottle|Pill|Syringe|Tablet|None
    interval_hours INTEGER NOT NULL,                       -- 6|8|12|24
    start_time     VARCHAR(4) NOT NULL,                    -- 'HHMM'
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_medicine_name UNIQUE (user_id, name)
);

CREATE TABLE IF NOT EXISTS alerts (
    id           SERIAL PRIMARY KEY,
    medicine_id  INTEGER NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMPTZ NOT NULL,
    status       VARCHAR(16) NOT NULL DEFAULT 'pending',   -- pending|sent|taken|skipped
    sent_at      TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS feedback (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sentiment  VARCHAR(16) NOT NULL,                        -- positive | negative
    message    VARCHAR(500) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_id   VARCHAR(64) UNIQUE NOT NULL,                 -- JWT jti
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked    BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_medicines_user_id ON medicines(user_id);
CREATE INDEX IF NOT EXISTS ix_alerts_user_id ON alerts(user_id);
CREATE INDEX IF NOT EXISTS ix_alerts_scheduled_at ON alerts(scheduled_at);
CREATE INDEX IF NOT EXISTS ix_sessions_token_id ON sessions(token_id);
