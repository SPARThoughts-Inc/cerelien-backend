"""Seed analytics results: risk scores, trends, and complication flags per patient."""

import json
import random

import asyncpg

COMPLICATION_OPTIONS = ["retinopathy", "nephropathy", "neuropathy", "cardiovascular"]
TREND_DIRECTIONS = ["improving", "stable", "worsening"]


async def seed_analytics(conn: asyncpg.Connection, patient_ids: list[int]) -> None:
    """Insert risk scores, trend data, and complication flags for each patient."""
    rng = random.Random(99)
    count = 0

    for pid in patient_ids:
        # Risk scores as JSON
        risk_score = json.dumps({
            "overall": round(rng.uniform(0.1, 0.95), 2),
            "cardiovascular": round(rng.uniform(0.05, 0.8), 2),
            "nephropathy": round(rng.uniform(0.05, 0.7), 2),
            "retinopathy": round(rng.uniform(0.05, 0.65), 2),
        })

        # Trend data as JSON
        trend = json.dumps({
            "direction": rng.choice(TREND_DIRECTIONS),
            "avg_glucose": round(rng.uniform(100, 200), 1),
            "time_in_range": round(rng.uniform(0.4, 0.85), 2),
        })

        # Random subset of complications (0 to 3)
        num_complications = rng.randint(0, 3)
        complications = rng.sample(COMPLICATION_OPTIONS, num_complications)
        complication_flags = json.dumps(complications)

        await conn.execute(
            """
            INSERT INTO analytics_results (patient_id, risk_score, trend, complication_flags)
            VALUES ($1, $2::jsonb, $3::jsonb, $4::jsonb)
            """,
            pid,
            risk_score,
            trend,
            complication_flags,
        )
        count += 1

    print(f"  Seeded {count} analytics result rows.")
