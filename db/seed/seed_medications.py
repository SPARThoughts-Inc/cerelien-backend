"""Seed 1-3 medications per patient with adherence rates."""

import random
from datetime import datetime, timedelta, timezone

import asyncpg

MEDICATIONS = [
    {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily"},
    {"name": "Insulin Glargine", "dosage": "20 units", "frequency": "once daily"},
    {"name": "Insulin Lispro", "dosage": "10 units", "frequency": "three times daily"},
    {"name": "Semaglutide", "dosage": "0.5mg", "frequency": "once weekly"},
    {"name": "Empagliflozin", "dosage": "10mg", "frequency": "once daily"},
    {"name": "Sitagliptin", "dosage": "100mg", "frequency": "once daily"},
    {"name": "Glipizide", "dosage": "5mg", "frequency": "once daily"},
]


async def seed_medications(conn: asyncpg.Connection, patient_ids: list[int]) -> None:
    """Insert 1-3 medications per patient with realistic adherence rates."""
    rng = random.Random(77)
    now = datetime.now(tz=timezone.utc)
    count = 0

    for pid in patient_ids:
        num_meds = rng.randint(1, 3)
        chosen = rng.sample(MEDICATIONS, num_meds)

        for med in chosen:
            adherence_rate = round(rng.uniform(0.55, 0.99), 2)
            start_date = now - timedelta(days=rng.randint(30, 365))
            await conn.execute(
                """
                INSERT INTO medications (patient_id, name, dosage, frequency, adherence_rate, start_date)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                pid,
                med["name"],
                med["dosage"],
                med["frequency"],
                adherence_rate,
                start_date,
            )
            count += 1

    print(f"  Seeded {count} medication rows.")
