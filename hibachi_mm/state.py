from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS engine_heartbeats(ts_ms INTEGER PRIMARY KEY, mode TEXT, engine_status TEXT, symbol TEXT);
CREATE TABLE IF NOT EXISTS market_snapshots(ts_ms INTEGER PRIMARY KEY, symbol TEXT, best_bid TEXT, best_ask TEXT, mid TEXT, mark_price TEXT, predicted_funding TEXT, spread_bps TEXT);
CREATE TABLE IF NOT EXISTS account_snapshots(ts_ms INTEGER PRIMARY KEY, equity TEXT, balance TEXT, unrealized_pnl TEXT, realized_pnl TEXT, fee TEXT, funding_pnl TEXT, free_margin TEXT, free_margin_pct TEXT, total_order_notional TEXT, total_position_notional TEXT, leverage TEXT);
CREATE TABLE IF NOT EXISTS risk_snapshots(ts_ms INTEGER PRIMARY KEY, scenario TEXT, free_margin_pct TEXT, leverage TEXT, liquidation_risk_pct TEXT, reason TEXT);
CREATE TABLE IF NOT EXISTS quote_decisions(ts_ms INTEGER PRIMARY KEY, scenario TEXT, should_bid INTEGER, should_ask INTEGER, bid_price TEXT, bid_qty TEXT, ask_price TEXT, ask_qty TEXT, gross_spread_bps TEXT, net_edge_bps TEXT, reason TEXT);
CREATE TABLE IF NOT EXISTS orders(order_id TEXT, nonce TEXT, symbol TEXT, side TEXT, order_role TEXT, reduce_only INTEGER, price TEXT, qty TEXT, status TEXT, created_at_ms INTEGER, updated_at_ms INTEGER, strategy_instance_id TEXT, parent_fill_id TEXT, PRIMARY KEY(order_id, nonce));
CREATE TABLE IF NOT EXISTS fills(fill_id TEXT PRIMARY KEY, ts_ms INTEGER, order_id TEXT, side TEXT, price TEXT, qty TEXT, fee TEXT, realized_pnl TEXT);
CREATE TABLE IF NOT EXISTS pnl_snapshots(ts_ms INTEGER PRIMARY KEY, equity TEXT, realized_pnl TEXT, unrealized_pnl TEXT, total_pnl TEXT);
CREATE TABLE IF NOT EXISTS warnings(ts_ms INTEGER PRIMARY KEY, code TEXT, message TEXT);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, ts_ms INTEGER, level TEXT, event_type TEXT, payload TEXT);
"""


class StateStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def insert_event(self, ts_ms: int, level: str, event_type: str, payload: str) -> None:
        self.conn.execute("INSERT INTO events(ts_ms, level, event_type, payload) VALUES(?,?,?,?)", (ts_ms, level, event_type, payload))
        self.conn.commit()

    def insert_heartbeat(self, ts_ms: int, mode: str, engine_status: str, symbol: str) -> None:
        self.conn.execute("INSERT OR REPLACE INTO engine_heartbeats(ts_ms, mode, engine_status, symbol) VALUES(?,?,?,?)", (ts_ms, mode, engine_status, symbol))
        self.conn.commit()

    def insert_market_snapshot(self, rec: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO market_snapshots(ts_ms, symbol, best_bid, best_ask, mid, mark_price, predicted_funding, spread_bps) VALUES(?,?,?,?,?,?,?,?)",
            (rec["ts_ms"], rec["symbol"], rec["best_bid"], rec["best_ask"], rec["mid"], rec.get("mark_price"), rec.get("predicted_funding"), rec.get("spread_bps")),
        )
        self.conn.commit()

    def insert_account_snapshot(self, rec: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO account_snapshots(ts_ms, equity, balance, unrealized_pnl, realized_pnl, fee, funding_pnl, free_margin, free_margin_pct, total_order_notional, total_position_notional, leverage) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (rec["ts_ms"], rec["equity"], rec["balance"], rec["unrealized_pnl"], rec["realized_pnl"], rec["fee"], rec["funding_pnl"], rec["free_margin"], rec["free_margin_pct"], rec["total_order_notional"], rec["total_position_notional"], rec["leverage"]),
        )
        self.conn.commit()

    def insert_risk_snapshot(self, rec: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO risk_snapshots(ts_ms, scenario, free_margin_pct, leverage, liquidation_risk_pct, reason) VALUES(?,?,?,?,?,?)",
            (rec["ts_ms"], rec["scenario"], rec["free_margin_pct"], rec["leverage"], rec["liquidation_risk_pct"], rec["reason"]),
        )
        self.conn.commit()

    def insert_quote_decision(self, rec: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO quote_decisions(ts_ms, scenario, should_bid, should_ask, bid_price, bid_qty, ask_price, ask_qty, gross_spread_bps, net_edge_bps, reason) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (rec["ts_ms"], rec["scenario"], 1 if rec["should_bid"] else 0, 1 if rec["should_ask"] else 0, rec.get("bid_price"), rec.get("bid_qty"), rec.get("ask_price"), rec.get("ask_qty"), rec.get("gross_spread_bps"), rec.get("net_edge_bps"), rec.get("reason", "")),
        )
        self.conn.commit()

    def upsert_order(self, rec: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO orders(order_id, nonce, symbol, side, order_role, reduce_only, price, qty, status, created_at_ms, updated_at_ms, strategy_instance_id, parent_fill_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (rec.get("order_id", ""), rec.get("nonce", ""), rec["symbol"], rec["side"], rec["order_role"], 1 if rec["reduce_only"] else 0, rec["price"], rec["qty"], rec["status"], rec["created_at_ms"], rec["updated_at_ms"], rec["strategy_instance_id"], rec.get("parent_fill_id")),
        )
        self.conn.commit()

    def insert_fill(self, rec: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO fills(fill_id, ts_ms, order_id, side, price, qty, fee, realized_pnl) VALUES(?,?,?,?,?,?,?,?)",
            (rec["fill_id"], rec["ts_ms"], rec["order_id"], rec["side"], rec["price"], rec["qty"], rec["fee"], rec["realized_pnl"]),
        )
        self.conn.commit()

    def insert_pnl_snapshot(self, rec: dict) -> None:
        self.conn.execute("INSERT OR REPLACE INTO pnl_snapshots(ts_ms, equity, realized_pnl, unrealized_pnl, total_pnl) VALUES(?,?,?,?,?)", (rec["ts_ms"], rec["equity"], rec["realized_pnl"], rec["unrealized_pnl"], rec["total_pnl"]))
        self.conn.commit()

    def insert_warning(self, ts_ms: int, code: str, message: str) -> None:
        self.conn.execute("INSERT OR REPLACE INTO warnings(ts_ms, code, message) VALUES(?,?,?)", (ts_ms, code, message))
        self.conn.commit()

    def query(self, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.execute(sql, args)
        return cur.fetchall()

    def list_open_orders(self) -> list[dict]:
        rows = self.query("SELECT order_id, nonce, symbol, side, order_role, reduce_only, status, price, qty, created_at_ms FROM orders WHERE status IN ('NEW','PARTIALLY_FILLED') ORDER BY created_at_ms DESC")
        return [dict(r) for r in rows]


def reconcile_unknown_orders(pending_orders: list[dict], known_orders: list[dict]) -> list[dict]:
    known = {(o.get("order_id", ""), o.get("nonce", "")) for o in known_orders}
    return [p for p in pending_orders if (p.get("order_id", ""), p.get("nonce", "")) not in known]
