from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
  order_id TEXT,
  nonce TEXT,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  order_role TEXT NOT NULL,
  reduce_only INTEGER NOT NULL,
  price TEXT NOT NULL,
  qty TEXT NOT NULL,
  created_at_ms INTEGER NOT NULL,
  updated_at_ms INTEGER NOT NULL,
  status TEXT NOT NULL,
  strategy_instance_id TEXT NOT NULL,
  parent_fill_id TEXT,
  PRIMARY KEY(order_id, nonce)
);
"""


class StateStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def upsert_order(self, rec: dict) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO orders(order_id, nonce, symbol, side, order_role, reduce_only, price, qty, created_at_ms, updated_at_ms, status, strategy_instance_id, parent_fill_id)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                rec.get("order_id", ""),
                rec.get("nonce", ""),
                rec["symbol"],
                rec["side"],
                rec["order_role"],
                1 if rec["reduce_only"] else 0,
                rec["price"],
                rec["qty"],
                rec["created_at_ms"],
                rec["updated_at_ms"],
                rec["status"],
                rec["strategy_instance_id"],
                rec.get("parent_fill_id"),
            ),
        )
        self.conn.commit()

    def list_open_orders(self) -> list[dict]:
        cur = self.conn.execute("SELECT order_id, nonce, symbol, side, order_role, reduce_only, status FROM orders WHERE status IN ('NEW','PARTIALLY_FILLED')")
        rows = cur.fetchall()
        return [
            {
                "order_id": r[0],
                "nonce": r[1],
                "symbol": r[2],
                "side": r[3],
                "order_role": r[4],
                "reduce_only": bool(r[5]),
                "status": r[6],
            }
            for r in rows
        ]


def reconcile_unknown_orders(pending_orders: list[dict], known_orders: list[dict]) -> list[dict]:
    known = {(o.get("order_id", ""), o.get("nonce", "")) for o in known_orders}
    unknown = []
    for p in pending_orders:
        key = (p.get("order_id", ""), p.get("nonce", ""))
        if key not in known:
            unknown.append(p)
    return unknown
