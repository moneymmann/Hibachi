from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import anyio

ALLOWED_GRANULARITY = (Decimal("0.1"), Decimal("1"), Decimal("10"), Decimal("100"))


def _d(v) -> Decimal:
    return Decimal(str(v))


def _attr(obj, *names, default=None):
    for n in names:
        if isinstance(obj, dict) and n in obj:
            return obj[n]
        if hasattr(obj, n):
            return getattr(obj, n)
    return default


def _levels(ob, side_name):
    val = _attr(ob, side_name)
    if val is None and side_name == "bids":
        val = _attr(ob, "bid")
    if val is None and side_name == "asks":
        val = _attr(ob, "ask")
    return list(val or [])


def _lvl_price_qty(level):
    return _d(_attr(level, "price")), _d(_attr(level, "quantity", "qty", default="0"))


@dataclass
class MarketSnapshot:
    best_bid: Decimal
    best_ask: Decimal
    mid: Decimal
    tick_size: Decimal


@dataclass
class AccountSnapshot:
    equity: Decimal
    free_margin: Decimal
    current_position_qty: Decimal
    current_position_notional_signed: Decimal
    maker_fee_rate: Decimal
    taker_fee_rate: Decimal


class HibachiExchange:
    def __init__(self, cfg: dict, env: dict):
        from hibachi_xyz import HibachiApiClient

        ex = cfg["exchange"]
        env_name = ex["environment"].upper()
        self.symbol = ex["symbol"]
        self.depth = int(ex.get("orderbook_depth", 20))
        g = Decimal(str(ex.get("orderbook_granularity", "0.1")))
        self.granularity = g if g in ALLOWED_GRANULARITY else Decimal("0.1")
        self.timeout = float(ex.get("api_timeout_sec", 5))
        self.client = HibachiApiClient(
            api_url=env.get(f"HIBACHI_API_ENDPOINT_{env_name}") or env.get("HIBACHI_API_ENDPOINT"),
            data_api_url=env.get(f"HIBACHI_DATA_API_ENDPOINT_{env_name}") or env.get("HIBACHI_DATA_API_ENDPOINT"),
            api_key=env.get(f"HIBACHI_API_KEY_{env_name}") or env.get("HIBACHI_API_KEY"),
            account_id=env.get(f"HIBACHI_ACCOUNT_ID_{env_name}") or env.get("HIBACHI_ACCOUNT_ID"),
            private_key=env.get(f"HIBACHI_PRIVATE_KEY_{env_name}") or env.get("HIBACHI_PRIVATE_KEY"),
        )

    async def _run(self, fn):
        with anyio.fail_after(self.timeout):
            return await anyio.to_thread.run_sync(fn)

    async def get_market_snapshot(self) -> MarketSnapshot:
        ob = await self._run(lambda: self.client.get_orderbook(self.symbol, self.depth, float(self.granularity)))
        bids = _levels(ob, "bids")
        asks = _levels(ob, "asks")
        if not bids or not asks:
            raise RuntimeError("empty orderbook")
        best_bid, _ = _lvl_price_qty(bids[0])
        best_ask, _ = _lvl_price_qty(asks[0])
        return MarketSnapshot(best_bid, best_ask, (best_bid + best_ask) / Decimal("2"), self.granularity)

    async def get_account_snapshot(self) -> AccountSnapshot:
        bal = await self._run(lambda: self.client.get_capital_balance())
        info = await self._run(lambda: self.client.get_account_info())
        equity = _d(_attr(bal, "equity", "balance", default="0"))
        free_margin = _d(_attr(bal, "free_margin", "available_margin", default=equity))
        pos_qty = _d(_attr(info, "current_position_qty", "position_qty", default="0"))
        pos_not = _d(_attr(info, "current_position_notional_signed", "position_notional_signed", default="0"))
        maker = _d(_attr(info, "maker_fee_rate", default="0"))
        taker = _d(_attr(info, "taker_fee_rate", default="0"))
        return AccountSnapshot(equity, free_margin, pos_qty, pos_not, maker, taker)

    async def get_pending_orders(self):
        r = await self._run(lambda: self.client.get_pending_orders(self.symbol))
        for name in ("orders", "data", "result", "items", "pending_orders"):
            v = _attr(r, name)
            if v is not None:
                return list(v)
        return list(r) if isinstance(r, list) else []

    async def place_limit(self, side: str, price: Decimal, qty: Decimal, *, reduce_only: bool = False):
        return await self._run(lambda: self.client.place_order(symbol=self.symbol, side=side, price=float(price), quantity=float(qty), post_only=True, reduce_only=reduce_only))

    async def cancel_order(self, order_id: str):
        return await self._run(lambda: self.client.cancel_order(order_id=order_id))
