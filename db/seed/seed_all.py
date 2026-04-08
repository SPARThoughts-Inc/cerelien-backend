"""
Orchestrator: creates the full database schema and runs all seeders.

Usage:
    python -m db.seed.seed_all
"""

import asyncio
import os
import sys

import asyncpg

from db.seed.seed_analytics import seed_analytics
from db.seed.seed_glucose import seed_glucose
from db.seed.seed_medications import seed_medications
from db.seed.seed_patients import seed_patients

# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id              SERIAL PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    date_of_birth   DATE NOT NULL,
    diabetes_type   VARCHAR(30) NOT NULL,
    phone_number    VARCHAR(20) UNIQUE NOT NULL,
    email           VARCHAR(200),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Glucose readings (CGM + A1C)
CREATE TABLE IF NOT EXISTS glucose_readings (
    id                  SERIAL PRIMARY KEY,
    patient_id          INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    reading_timestamp   TIMESTAMPTZ NOT NULL,
    reading_type        VARCHAR(10) NOT NULL,       -- 'cgm' or 'a1c'
    value               NUMERIC(6,1) NOT NULL,
    unit                VARCHAR(10) NOT NULL,        -- 'mg/dL' or '%'
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_glucose_patient_ts
    ON glucose_readings (patient_id, reading_timestamp DESC);

-- Analytics results
CREATE TABLE IF NOT EXISTS analytics_results (
    id                  SERIAL PRIMARY KEY,
    patient_id          INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    risk_score          JSONB NOT NULL DEFAULT '{}',
    trend               JSONB NOT NULL DEFAULT '{}',
    complication_flags  JSONB NOT NULL DEFAULT '[]',
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_analytics_patient
    ON analytics_results (patient_id);

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
    id              SERIAL PRIMARY KEY,
    patient_id      INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    channel         VARCHAR(20) NOT NULL,            -- 'sms', 'voice', 'web'
    status          VARCHAR(20) NOT NULL DEFAULT 'active',
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_conversations_patient
    ON conversations (patient_id);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id              SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,            -- 'user', 'assistant', 'system'
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages (conversation_id);

-- Medications
CREATE TABLE IF NOT EXISTS medications (
    id              SERIAL PRIMARY KEY,
    patient_id      INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    dosage          VARCHAR(50) NOT NULL,
    frequency       VARCHAR(50) NOT NULL,
    adherence_rate  NUMERIC(3,2),
    start_date      TIMESTAMPTZ,
    end_date        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_medications_patient
    ON medications (patient_id);
"""


async def main() -> None:
    database_url = os.environ.get("NEON_DATABASE_URL", "")
    if not database_url:
        print("ERROR: NEON_DATABASE_URL environment variable is not set.")
        sys.exit(1)

    print(f"Connecting to database...")
    conn: asyncpg.Connection = await asyncpg.connect(database_url)

    try:
        # Create schema
        print("Creating schema...")
        await conn.execute(SCHEMA_SQL)
        print("  Schema created.")

        # Run seeders in order
        print("Seeding patients...")
        patient_ids = await seed_patients(conn)

        print("Seeding glucose readings (this may take a moment)...")
        await seed_glucose(conn, patient_ids)

        print("Seeding analytics results...")
        await seed_analytics(conn, patient_ids)

        print("Seeding medications...")
        await seed_medications(conn, patient_ids)

        print("\nAll seed data inserted successfully.")
    finally:
        await conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
