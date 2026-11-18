"""Build the same small shop database from scratch for every run: {root}/shop.db.

Ground truth (checked in tests if you add one):
  delivered revenue      = 336.49 USD   (A17 42.50 + C03 120.00 + D11 18.75 + E05 99.99 + B43 55.25)
  top delivered spender  = Chloe (120.00)
  orders by IN customers = 3            (A17, A20 Asha; E05 Esha)
  refunded order         = C04, Chloe, 60.00 USD
  orders in October 2026 = 4            (B42, D11, E05, A20)
"""

import sqlite3
import sys
from pathlib import Path

root = Path(sys.argv[1])
db = root / "shop.db"
db.unlink(missing_ok=True)
con = sqlite3.connect(db)
con.executescript(
    """
    CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, country TEXT NOT NULL);
    CREATE TABLE orders (
        id TEXT PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(id),
        status TEXT NOT NULL,          -- delivered | processing | refunded | cancelled
        total_usd REAL NOT NULL,
        created_at TEXT NOT NULL       -- ISO date
    );
    INSERT INTO customers VALUES
        (1, 'Asha', 'IN'), (2, 'Ben', 'US'), (3, 'Chloe', 'FR'), (4, 'Dmitri', 'DE'), (5, 'Esha', 'IN');
    INSERT INTO orders VALUES
        ('A17', 1, 'delivered', 42.50, '2026-09-02'),
        ('B42', 2, 'processing', 15.00, '2026-10-11'),
        ('C03', 3, 'delivered', 120.00, '2026-08-20'),
        ('C04', 3, 'refunded', 60.00, '2026-09-15'),
        ('D11', 4, 'delivered', 18.75, '2026-10-01'),
        ('E05', 5, 'delivered', 99.99, '2026-10-20'),
        ('A20', 1, 'cancelled', 30.00, '2026-10-25'),
        ('B43', 2, 'delivered', 55.25, '2026-11-02');
    """
)
con.commit()
con.close()
