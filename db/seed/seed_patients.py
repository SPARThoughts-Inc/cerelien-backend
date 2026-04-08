"""Seed 10 sample patients with varying diabetes types."""

from datetime import date

import asyncpg

PATIENTS = [
    {
        "first_name": "Maria",
        "last_name": "Garcia",
        "date_of_birth": date(1955, 3, 12),
        "diabetes_type": "type_2",
        "phone_number": "+15551000001",
        "email": "maria.garcia@example.com",
    },
    {
        "first_name": "James",
        "last_name": "Wilson",
        "date_of_birth": date(1982, 7, 24),
        "diabetes_type": "type_1",
        "phone_number": "+15551000002",
        "email": "james.wilson@example.com",
    },
    {
        "first_name": "Priya",
        "last_name": "Patel",
        "date_of_birth": date(1990, 11, 5),
        "diabetes_type": "gestational",
        "phone_number": "+15551000003",
        "email": "priya.patel@example.com",
    },
    {
        "first_name": "Robert",
        "last_name": "Johnson",
        "date_of_birth": date(1948, 1, 18),
        "diabetes_type": "type_2",
        "phone_number": "+15551000004",
        "email": "robert.johnson@example.com",
    },
    {
        "first_name": "Aisha",
        "last_name": "Mohammed",
        "date_of_birth": date(1975, 6, 30),
        "diabetes_type": "type_2",
        "phone_number": "+15551000005",
        "email": "aisha.mohammed@example.com",
    },
    {
        "first_name": "Chen",
        "last_name": "Wei",
        "date_of_birth": date(1968, 9, 14),
        "diabetes_type": "type_1",
        "phone_number": "+15551000006",
        "email": "chen.wei@example.com",
    },
    {
        "first_name": "Elena",
        "last_name": "Kowalski",
        "date_of_birth": date(1958, 12, 2),
        "diabetes_type": "type_2",
        "phone_number": "+15551000007",
        "email": "elena.kowalski@example.com",
    },
    {
        "first_name": "David",
        "last_name": "Thompson",
        "date_of_birth": date(1985, 4, 20),
        "diabetes_type": "prediabetes",
        "phone_number": "+15551000008",
        "email": "david.thompson@example.com",
    },
    {
        "first_name": "Fatima",
        "last_name": "Al-Rashid",
        "date_of_birth": date(1962, 8, 9),
        "diabetes_type": "type_2",
        "phone_number": "+15551000009",
        "email": "fatima.alrashid@example.com",
    },
    {
        "first_name": "Michael",
        "last_name": "O'Brien",
        "date_of_birth": date(1978, 2, 15),
        "diabetes_type": "type_1",
        "phone_number": "+15551000010",
        "email": "michael.obrien@example.com",
    },
]


async def seed_patients(conn: asyncpg.Connection) -> list[int]:
    """Insert sample patients and return their IDs."""
    patient_ids: list[int] = []
    for p in PATIENTS:
        row = await conn.fetchrow(
            """
            INSERT INTO patients (first_name, last_name, date_of_birth, diabetes_type, phone_number, email)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            p["first_name"],
            p["last_name"],
            p["date_of_birth"],
            p["diabetes_type"],
            p["phone_number"],
            p["email"],
        )
        patient_ids.append(row["id"])
    print(f"  Seeded {len(patient_ids)} patients.")
    return patient_ids
