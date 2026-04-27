from __future__ import annotations

import sqlite3
from pathlib import Path


class Ledger:
    def __init__(self, sqlite_path: str) -> None:
        self.path = Path(sqlite_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_orders (
                order_id TEXT PRIMARY KEY,
                nonce TEXT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                price TEXT NOT NULL,
                qty TEXT NOT NULL,
                created_at_ms INTEGER NOT NULL,
                updated_at_ms INTEGER NOT NULL,
                status TEXT NOT NULL,
                strategy_instance_id TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def upsert_order(self, order: dict) -> None:
        self.conn.execute(
            """
            INSERT INTO bot_orders (
                order_id, nonce, symbol, side, price, qty, created_at_ms, updated_at_ms, status, strategy_instance_id
            ) VALUES (:order_id,:nonce,:symbol,:side,:price,:qty,:created_at_ms,:updated_at_ms,:status,:strategy_instance_id)
            ON CONFLICT(order_id) DO UPDATE SET
                nonce=excluded.nonce,
                price=excluded.price,
                qty=excluded.qty,
                updated_at_ms=excluded.updated_at_ms,
                status=excluded.status
            """,
            order,
        )
        self.conn.commit()

    def get_order_ids(self, symbol: str) -> set[str]:
        rows = self.conn.execute("SELECT order_id FROM bot_orders WHERE symbol = ?", (symbol,)).fetchall()
        return {row[0] for row in rows}

    def close(self) -> None:
        self.conn.close()
