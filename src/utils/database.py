"""
Database setup — SQLite schema and seed data.

Creates a realistic support database with customers, orders, and tickets.
Called once at startup or via `python -m src.utils.database`.
"""

import sqlite3
from datetime import datetime, timedelta

from src.utils.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL DEFAULT 'free',
    created_at TEXT NOT NULL,
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    product TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    total REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'processing',
    tracking_number TEXT,
    ordered_at TEXT NOT NULL,
    delivered_at TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    priority TEXT NOT NULL DEFAULT 'medium',
    category TEXT,
    messages TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    resolved_at TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS refunds (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    amount REAL NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    approved_by TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
"""

SEED_CUSTOMERS = [
    ("C001", "Alice Johnson", "alice@example.com", "premium", "2024-01-15", "VIP customer, long-term subscriber"),
    ("C002", "Bob Smith", "bob@example.com", "free", "2024-06-20", ""),
    ("C003", "Carol Davis", "carol@example.com", "premium", "2023-11-01", "Enterprise account"),
    ("C004", "Dan Wilson", "dan@example.com", "free", "2025-01-10", "New customer"),
    ("C005", "Eve Martinez", "eve@example.com", "premium", "2024-03-05", "Referred by Carol Davis"),
]


def _seed_orders(cursor: sqlite3.Cursor) -> None:
    """Generate realistic orders for each customer."""
    now = datetime.utcnow()
    orders = [
        (
            "ORD-1001",
            "C001",
            "Wireless Headphones Pro",
            1,
            149.99,
            "delivered",
            "TRK-WH-99281",
            (now - timedelta(days=10)).isoformat(),
            (now - timedelta(days=3)).isoformat(),
        ),
        (
            "ORD-1002",
            "C001",
            "USB-C Charging Cable",
            3,
            29.97,
            "delivered",
            "TRK-UC-44821",
            (now - timedelta(days=30)).isoformat(),
            (now - timedelta(days=25)).isoformat(),
        ),
        (
            "ORD-1003",
            "C002",
            "Smart Watch Basic",
            1,
            199.99,
            "shipped",
            "TRK-SW-12093",
            (now - timedelta(days=2)).isoformat(),
            None,
        ),
        ("ORD-1004", "C002", "Phone Case", 1, 24.99, "processing", None, (now - timedelta(hours=6)).isoformat(), None),
        (
            "ORD-1005",
            "C003",
            "Laptop Stand Deluxe",
            2,
            159.98,
            "delivered",
            "TRK-LS-77342",
            (now - timedelta(days=15)).isoformat(),
            (now - timedelta(days=8)).isoformat(),
        ),
        (
            "ORD-1006",
            "C004",
            "Bluetooth Speaker",
            1,
            79.99,
            "cancelled",
            None,
            (now - timedelta(days=5)).isoformat(),
            None,
        ),
        (
            "ORD-1007",
            "C005",
            "Mechanical Keyboard",
            1,
            129.99,
            "delivered",
            "TRK-MK-55109",
            (now - timedelta(days=20)).isoformat(),
            (now - timedelta(days=14)).isoformat(),
        ),
        (
            "ORD-1008",
            "C005",
            "Monitor Arm",
            1,
            89.99,
            "shipped",
            "TRK-MA-33201",
            (now - timedelta(days=1)).isoformat(),
            None,
        ),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO orders (id, customer_id, product, quantity, total, status, tracking_number, ordered_at, delivered_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        orders,
    )


def _seed_tickets(cursor: sqlite3.Cursor) -> None:
    """Create a few existing tickets for context."""
    now = datetime.utcnow().isoformat()
    tickets = [
        ("TKT-2001", "C001", "Headphones not charging", "resolved", "medium", "technical", "[]", now, now, now),
        ("TKT-2002", "C003", "Bulk order discount inquiry", "open", "low", "billing", "[]", now, now, None),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO tickets (id, customer_id, subject, status, priority, category, messages, created_at, updated_at, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        tickets,
    )


def get_connection() -> sqlite3.Connection:
    """Return a connection to the support database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database() -> None:
    """Create tables and seed data. Safe to call multiple times."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript(SCHEMA)

    cursor.executemany(
        "INSERT OR IGNORE INTO customers (id, name, email, plan, created_at, notes) VALUES (?, ?, ?, ?, ?, ?)",
        SEED_CUSTOMERS,
    )
    _seed_orders(cursor)
    _seed_tickets(cursor)

    conn.commit()
    conn.close()
    print(f"[Database] Initialised at {DB_PATH}")


if __name__ == "__main__":
    init_database()
