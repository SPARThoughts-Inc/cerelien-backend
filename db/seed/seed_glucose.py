"""Seed CGM glucose readings (every 5 min for 30 days) and monthly A1C readings per patient."""

import random
from datetime import datetime, timedelta, timezone

import asyncpg

# Realistic glucose patterns
PATTERN_NORMAL = {"mean": 120, "std": 20}
PATTERN_POST_MEAL = {"mean": 160, "std": 30}
PATTERN_OVERNIGHT_LOW = {"mean": 90, "std": 15}

# Meal windows (hours of day in 24h format)
BREAKFAST_START, BREAKFAST_END = 7, 9
LUNCH_START, LUNCH_END = 12, 14
DINNER_START, DINNER_END = 18, 20
OVERNIGHT_START, OVERNIGHT_END = 0, 5


def _glucose_value(hour: int, rng: random.Random) -> float:
    """Generate a realistic glucose value based on time of day."""
    if OVERNIGHT_START <= hour < OVERNIGHT_END:
        val = rng.gauss(PATTERN_OVERNIGHT_LOW["mean"], PATTERN_OVERNIGHT_LOW["std"])
    elif (BREAKFAST_START <= hour < BREAKFAST_END) or (LUNCH_START <= hour < LUNCH_END) or (DINNER_START <= hour < DINNER_END):
        val = rng.gauss(PATTERN_POST_MEAL["mean"], PATTERN_POST_MEAL["std"])
    else:
        val = rng.gauss(PATTERN_NORMAL["mean"], PATTERN_NORMAL["std"])
    # Clamp to physiologically plausible range
    return round(max(40.0, min(400.0, val)), 1)


async def seed_glucose(conn: asyncpg.Connection, patient_ids: list[int]) -> None:
    """Insert 30 days of CGM readings (every 5 min) + monthly A1C per patient."""
    rng = random.Random(42)
    now = datetime.now(tz=timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(days=30)

    total_cgm = 0
    total_a1c = 0

    for pid in patient_ids:
        # CGM readings: every 5 minutes for 30 days = 8640 readings per patient
        cgm_rows: list[tuple] = []
        ts = start
        while ts < now:
            value = _glucose_value(ts.hour, rng)
            cgm_rows.append((pid, ts, "cgm", value, "mg/dL"))
            ts += timedelta(minutes=5)

        # Batch insert CGM readings
        await conn.executemany(
            """
            INSERT INTO glucose_readings (patient_id, reading_timestamp, reading_type, value, unit)
            VALUES ($1, $2, $3, $4, $5)
            """,
            cgm_rows,
        )
        total_cgm += len(cgm_rows)

        # Monthly A1C reading (one per patient, dated ~15 days ago)
        a1c_value = round(rng.gauss(7.2, 0.8), 1)
        a1c_value = max(5.0, min(14.0, a1c_value))
        a1c_ts = now - timedelta(days=15)
        await conn.execute(
            """
            INSERT INTO glucose_readings (patient_id, reading_timestamp, reading_type, value, unit)
            VALUES ($1, $2, $3, $4, $5)
            """,
            pid,
            a1c_ts,
            "a1c",
            a1c_value,
            "%",
        )
        total_a1c += 1

    print(f"  Seeded {total_cgm} CGM readings and {total_a1c} A1C readings.")
