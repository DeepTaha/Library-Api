"""
Seed script â€” creates test fines and borrowings for payment gateway testing.

Run with:  python seed_payments.py

Scenarios created:
  1. Zaid   (id=2) â€” PENDING fine Rs.180  â†’ test full payment flow
  2. Aamir  (id=5) â€” PAID fine Rs.150     â†’ test already-paid state
  3. Hamza  (id=7) â€” PENDING fine Rs.140  â†’ test borrowing block
  4. Ahmed  (id=8) â€” WAIVED fine Rs.70    â†’ test waived state
"""

import psycopg2
from datetime import datetime, timezone

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="library", user="postgres", password="lmessi10"
)
cur = conn.cursor()

print("\n=== Library Payment Seed Script ===\n")

# ------------------------------------------------------------------ #
# Scenario 1 â€” Zaid (id=2)                                           #
# Borrowing 8 already exists: book 3, returned 2026-06-14,           #
# due 2026-05-27 â†’ 18 days overdue â†’ Rs. 180                         #
# Fine status: PENDING â€” use this to test the full payment flow       #
# ------------------------------------------------------------------ #

cur.execute("SELECT id FROM fines WHERE borrowing_id = 8")
if not cur.fetchone():
    cur.execute("""
        INSERT INTO fines (borrowing_id, user_id, days_overdue, amount, status, created_at)
        VALUES (8, 2, 18, 180, 'pending', NOW())
    """)
    print("âœ“ Scenario 1 â€” Zaid: PENDING fine Rs.180 created (borrowing #8, 18 days overdue)")
else:
    print("- Scenario 1 â€” Zaid: fine already exists, skipping")


# ------------------------------------------------------------------ #
# Scenario 2 â€” Aamir (id=5)                                          #
# Borrowing 11 already exists: book 6, returned 2026-06-11,          #
# due 2026-05-27 â†’ 15 days overdue â†’ Rs. 150                         #
# Fine status: PAID â€” already settled                                 #
# ------------------------------------------------------------------ #

cur.execute("SELECT id FROM fines WHERE borrowing_id = 11")
if not cur.fetchone():
    cur.execute("""
        INSERT INTO fines (borrowing_id, user_id, days_overdue, amount, status, created_at, paid_at)
        VALUES (11, 5, 15, 150, 'paid', NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day')
    """)
    print("âœ“ Scenario 2 â€” Aamir: PAID fine Rs.150 created (borrowing #11, 15 days overdue)")
else:
    print("- Scenario 2 â€” Aamir: fine already exists, skipping")


# ------------------------------------------------------------------ #
# Scenario 3 â€” Hamza (id=7)                                          #
# New borrowing: book 7 (Gone Girl), borrowed June 1, due June 3,    #
# returned June 17 â†’ 14 days overdue â†’ Rs. 140                       #
# Fine status: PENDING â€” use this to test borrowing block             #
# ------------------------------------------------------------------ #

cur.execute("SELECT id FROM borrowings WHERE user_id = 7 AND book_id = 7")
row = cur.fetchone()
if not row:
    cur.execute("""
        INSERT INTO borrowings (book_id, user_id, borrowed_at, due_date, returned_at, is_overdue, extension_count)
        VALUES (7, 7,
            '2026-06-01 10:00:00+00',
            '2026-06-03 10:00:00+00',
            '2026-06-17 10:00:00+00',
            true, 0)
        RETURNING id
    """)
    hamza_borrowing_id = cur.fetchone()[0]
    cur.execute("""
        INSERT INTO fines (borrowing_id, user_id, days_overdue, amount, status, created_at)
        VALUES (%s, 7, 14, 140, 'pending', NOW())
    """, (hamza_borrowing_id,))
    print(f"âœ“ Scenario 3 â€” Hamza: borrowing #{hamza_borrowing_id} + PENDING fine Rs.140 created (14 days overdue)")
else:
    print("- Scenario 3 â€” Hamza: borrowing already exists, skipping")


# ------------------------------------------------------------------ #
# Scenario 4 â€” Ahmed (id=8)                                          #
# New borrowing: book 4 (To Kill a Mockingbird), borrowed June 1,    #
# due June 3, returned June 10 â†’ 7 days overdue â†’ Rs. 70             #
# Fine status: WAIVED â€” librarian forgave it                          #
# ------------------------------------------------------------------ #

cur.execute("SELECT id FROM borrowings WHERE user_id = 8 AND book_id = 4")
row = cur.fetchone()
if not row:
    cur.execute("""
        INSERT INTO borrowings (book_id, user_id, borrowed_at, due_date, returned_at, is_overdue, extension_count)
        VALUES (4, 8,
            '2026-06-01 10:00:00+00',
            '2026-06-03 10:00:00+00',
            '2026-06-10 10:00:00+00',
            true, 0)
        RETURNING id
    """)
    ahmed_borrowing_id = cur.fetchone()[0]
    cur.execute("""
        INSERT INTO fines (borrowing_id, user_id, days_overdue, amount, status, created_at)
        VALUES (%s, 8, 7, 70, 'waived', NOW())
    """, (ahmed_borrowing_id,))
    print(f"âœ“ Scenario 4 â€” Ahmed: borrowing #{ahmed_borrowing_id} + WAIVED fine Rs.70 created (7 days overdue)")
else:
    print("- Scenario 4 â€” Ahmed: borrowing already exists, skipping")


conn.commit()
cur.close()
conn.close()

print("\n=== Seed complete ===\n")
print("TEST CREDENTIALS (password: password123 for all)")
print("â”€" * 55)
print(f"{'User':<10} {'Role':<12} {'Scenario':<35}")
print("â”€" * 55)
print(f"{'Zaid':<10} {'READER':<12} Pay a Rs.180 fine (full flow)")
print(f"{'Aamir':<10} {'READER':<12} View already-paid fine")
print(f"{'Hamza':<10} {'READER':<12} Blocked from borrowing (pending Rs.140)")
print(f"{'Ahmed':<10} {'READER':<12} View waived fine, can borrow freely")
print(f"{'Fatima':<10} {'LIBRARIAN':<12} Waive fines, view all")
print(f"{'admin':<10} {'ADMIN':<12} Full access")
print("â”€" * 55)
print("\nEndpoints to test:")
print("  POST /auth/login              â†’ get token")
print("  GET  /fines/me                â†’ see your fines")
print("  POST /payments/initiate       â†’ body: {fine_id: <id>}")
print("  GET  /payments/me             â†’ payment history")
print("  POST /fines/{id}/waive        â†’ body: {reason: '...'} (librarian only)")
print("  POST /borrowings/             â†’ try borrow while fine pending â†’ blocked")
print()

