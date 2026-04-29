from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

from hibachi_mm.models import AccountState, ContractRules, Level, MarketSnapshot


class HibachiExchangeAdapter:
    """Thin adapter around hibachi-xyz SDK; no custom signing."""

    def __init__(self, cfg_exchange: Any, strategy_instance_id: str) -> None:
        self.cfg = cfg_exchange
        self.strategy_instance_id = strategy_instance_id
        self._sdk = self._build_sdk_clients()

    def _build_sdk_clients(self) -> dict[str, Any]:
        try:
            from hibachi_xyz import HibachiApiClient  # type: ignore
        except Exception:  # pragma: no cover
            return {}
        api_endpoint = os.getenv(self.cfg.api_endpoint_env) or self.cfg.api_endpoint
        data_endpoint = os.getenv(self.cfg.data_api_endpoint_env) or self.cfg.data_api_endpoint
        client = HibachiApiClient(
            api_endpoint=api_endpoint,
            data_api_endpoint=data_endpoint,
            api_key=os.getenv(self.cfg.api_key_env),
            account_id=os.getenv(self.cfg.account_id_env),
            private_key=os.getenv(self.cfg.private_key_env),
            public_key=os.getenv(self.cfg.public_key_env),
        )
        return {"rest": client}

    def fetch_startup_bundle(self, symbol: str) -> tuple[ContractRules, AccountState, list[dict], MarketSnapshot]:
        rest = self._sdk.get("rest")
        if rest is None:
            raise RuntimeError("hibachi-xyz SDK unavailable")

        inventory = rest.get_inventory()
        contract = next(c for c in inventory["futureContracts"] if c["symbol"] == symbol)

        cap = rest.get_capital_balance()
        info = rest.get_account_info()
        pending = rest.get_pending_orders(symbol=symbol)
        ob = rest.get_orderbook(symbol=symbol, depth=20, granularity=str(contract["tickSize"]))

        rules = ContractRules(
            symbol=symbol,
            tick_size=Decimal(str(contract["tickSize"])),
            step_size=Decimal(str(contract["stepSize"])),
            min_order_size=Decimal(str(contract["minOrderSize"])),
            min_notional=Decimal(str(contract["minNotional"])),
            initial_margin_rate=Decimal(str(contract["initialMarginRate"])),
            maintenance_margin_rate=Decimal(str(contract["maintenanceMarginRate"])),
            settlement_symbol=str(contract.get("settlementSymbol", "USDT")),
            underlying_symbol=str(contract.get("underlyingSymbol", "BTC")),
            orderbook_granularities=list(contract.get("orderbookGranularities", [])),
            status=str(contract.get("status", "UNKNOWN")),
        )

        equity = Decimal(str(cap.get("balance", "0")))
        total_unrealized = Decimal(str(info.get("totalUnrealizedPnl", "0")))
        balance = Decimal(str(info.get("balance", "0")))
        if equity <= Decimal("0"):
            equity = balance + total_unrealized

        position_qty = Decimal("0")
        for p in info.get("positions", []):
            if p.get("symbol") == symbol:
                qty = Decimal(str(p.get("quantity", "0")))
                direction = str(p.get("direction", "")).upper()
                if direction in {"LONG", "BUY", "BID"}:
                    position_qty = abs(qty)
                elif direction in {"SHORT", "SELL", "ASK"}:
                    position_qty = -abs(qty)
                else:
                    position_qty = qty

        account = AccountState(
            equity_usdt=equity,
            account_balance=balance,
            total_unrealized_pnl=total_unrealized,
            total_order_notional=Decimal(str(info.get("totalOrderNotional", "0"))),
            total_position_notional=Decimal(str(info.get("totalPositionNotional", "0"))),
            maker_fee_rate=Decimal(str(info.get("tradeMakerFeeRate", "0"))),
            taker_fee_rate=Decimal(str(info.get("tradeTakerFeeRate", "0"))),
            positions=list(info.get("positions", [])),
            current_symbol_position_qty=position_qty,
            current_symbol_position_notional_signed=position_qty * Decimal(str(ob["bestBidPrice"])),
        )

        snapshot = MarketSnapshot(
            symbol=symbol,
            best_bid_price=Decimal(str(ob["bestBidPrice"])),
            best_bid_qty=Decimal(str(ob["bestBidQty"])),
            best_ask_price=Decimal(str(ob["bestAskPrice"])),
            best_ask_qty=Decimal(str(ob["bestAskQty"])),
            orderbook_bids=[Level(Decimal(str(x[0])), Decimal(str(x[1]))) for x in ob.get("bids", [])],
            orderbook_asks=[Level(Decimal(str(x[0])), Decimal(str(x[1]))) for x in ob.get("asks", [])],
            mark_price=Decimal(str(ob.get("markPrice"))) if ob.get("markPrice") is not None else None,
            spot_price=Decimal(str(ob.get("spotPrice"))) if ob.get("spotPrice") is not None else None,
            funding_rate_estimation=Decimal(str(ob.get("fundingRateEstimation"))) if ob.get("fundingRateEstimation") is not None else None,
            ts_ms=int(ob.get("ts", 0)),
        )

        return rules, account, list(pending), snapshot
