from __future__ import annotations

import os
import time
from decimal import Decimal
from typing import Any


def decimal_to_sdk_float(v: Decimal) -> float:
    return float(str(v))


class HibachiGateway:
    def __init__(self, config):
        self.config = config
        self.client = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            from hibachi_xyz import HibachiApiClient  # type: ignore
        except Exception:
            self.client = None
            return
        api_key = os.getenv(self.config.exchange.api_key_env, "")
        account_id = os.getenv(self.config.exchange.account_id_env, "")
        private_key = os.getenv(self.config.exchange.private_key_env, "")
        public_key = os.getenv(self.config.exchange.public_key_env, "")
        if not (api_key and account_id and private_key and public_key):
            self.client = None
            return
        self.client = HibachiApiClient(
            api_endpoint=self.config.exchange.api_endpoint,
            data_api_endpoint=self.config.exchange.data_api_endpoint,
            api_key=api_key,
            account_id=account_id,
            private_key=private_key,
            public_key=public_key,
        )

    def fetch_market(self, symbol: str) -> dict[str, Any] | None:
        if self.client is None:
            return None
        try:
            ob = self.client.get_orderbook(symbol=symbol, depth=20)
            best_bid = Decimal(str(ob["bids"][0][0]))
            best_ask = Decimal(str(ob["asks"][0][0]))
            mid = (best_bid + best_ask) / Decimal("2")
            mark = self.client.get_mark_price(symbol=symbol)
            funding = self.client.get_funding_rate_estimation(symbol=symbol)
            return {
                "ts_ms": int(time.time() * 1000),
                "symbol": symbol,
                "best_bid": str(best_bid),
                "best_ask": str(best_ask),
                "mid": str(mid),
                "mark_price": str(Decimal(str(mark.get("price", mid)))),
                "predicted_funding": str(Decimal(str(funding.get("rate", "0")))),
                "spread_bps": str(((best_ask - best_bid) / mid) * Decimal("10000")),
            }
        except Exception:
            return None

    def fetch_account(self) -> dict[str, Any] | None:
        if self.client is None:
            return None
        try:
            cap = self.client.get_capital_balance()
            acc = self.client.get_account_info()
            eq = Decimal(str(cap.get("balance", "0")))
            bal = Decimal(str(acc.get("balance", "0")))
            upnl = Decimal(str(acc.get("totalUnrealizedPnl", "0")))
            order_notional = Decimal(str(acc.get("totalOrderNotional", "0")))
            pos_notional = Decimal(str(acc.get("totalPositionNotional", "0")))
            free_margin = eq - (order_notional * Decimal("0.05"))
            free_pct = Decimal("0") if eq == 0 else (free_margin / eq) * Decimal("100")
            lev = Decimal("0") if eq == 0 else pos_notional / eq
            return {
                "ts_ms": int(time.time() * 1000),
                "equity": str(eq),
                "balance": str(bal),
                "unrealized_pnl": str(upnl),
                "realized_pnl": "0",
                "fee": "0",
                "funding_pnl": "0",
                "free_margin": str(free_margin),
                "free_margin_pct": str(free_pct),
                "total_order_notional": str(order_notional),
                "total_position_notional": str(pos_notional),
                "leverage": str(lev),
                "position_qty": "0",
                "position_notional": str(pos_notional),
                "liquidation_risk_pct": str(max(Decimal("0"), Decimal("100") - free_pct)),
            }
        except Exception:
            return None

    def place_limit_entry(self, symbol: str, side: str, price: Decimal, qty: Decimal, post_only: bool = True) -> dict[str, Any] | None:
        if self.client is None:
            return None
        try:
            return self.client.place_limit_order(symbol=symbol, side=side, price=decimal_to_sdk_float(price), quantity=decimal_to_sdk_float(qty), post_only=post_only)
        except Exception:
            return None
