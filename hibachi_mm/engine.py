from __future__ import annotations

import os
import time
from dataclasses import asdict

from hibachi_mm.audit import AuditLogger
from hibachi_mm.config import BotConfig
from hibachi_mm.exchange import HibachiExchangeAdapter
from hibachi_mm.risk import evaluate_risk
from hibachi_mm.state import Ledger
from hibachi_mm.strategy import make_quote_decision


def run_mode(mode: str, config: BotConfig) -> int:
    if mode == "live":
        gate = os.getenv("HIBACHI_ENABLE_LIVE_TRADING", "")
        if gate != "I_UNDERSTAND_PERP_RISK":
            raise SystemExit("HIBACHI_ENABLE_LIVE_TRADING gate is missing")

    exchange = HibachiExchangeAdapter(config.exchange, config.strategy_instance_id)
    ledger = Ledger(config.state.sqlite_path)
    audit = AuditLogger(config.logging.audit_log_path)

    rules, account, pending, market = exchange.fetch_startup_bundle(config.exchange.symbol)
    known_ids = ledger.get_order_ids(config.exchange.symbol)
    bot_owned = [o for o in pending if str(o.get("orderId")) in known_ids]
    unknown = [o for o in pending if str(o.get("orderId")) not in known_ids]
    account.pending_bot_orders = bot_owned
    account.pending_unknown_orders = unknown

    if mode == "live" and unknown and not config.exchange.allow_unknown_open_orders:
        raise SystemExit("unknown open orders detected; halting live mode")

    if mode == "inspect":
        audit.log({
            "event": "inspect_snapshot",
            "mode": mode,
            "symbol": config.exchange.symbol,
            "pendingBot": len(bot_owned),
            "pendingUnknown": len(unknown),
            "contractStatus": rules.status,
            "equityUSDT": str(account.equity_usdt),
        })
        return 0

    risk_status = evaluate_risk(config.risk, account, rules.initial_margin_rate, int(time.time() * 1000) - market.ts_ms)
    decision = make_quote_decision(
        config.strategy,
        config.risk,
        market,
        rules,
        account,
        risk_status.free_margin_approx,
        risk_status.free_margin_pct,
    )

    audit.log(
        {
            "event": "quote_decision",
            "mode": mode,
            "symbol": config.exchange.symbol,
            "bestBid": str(market.best_bid_price),
            "bestAsk": str(market.best_ask_price),
            "bidPrice": str(decision.bid_price) if decision.bid_price else None,
            "bidQty": str(decision.bid_qty) if decision.bid_qty else None,
            "askPrice": str(decision.ask_price) if decision.ask_price else None,
            "askQty": str(decision.ask_qty) if decision.ask_qty else None,
            "mid": str(decision.mid),
            "grossSpreadBps": str(decision.gross_spread_bps),
            "netEdgeBps": str(decision.net_edge_bps),
            "makerFeeRate": str(account.maker_fee_rate),
            "takerFeeRate": str(account.taker_fee_rate),
            "entryMarginPct": str(config.strategy.entry_margin_pct),
            "edgeSizeMultiplier": str(decision.edge_size_multiplier),
            "bidPositionMultiplier": str(decision.bid_position_multiplier),
            "askPositionMultiplier": str(decision.ask_position_multiplier),
            "bidMarginBudgetUSDT": str(decision.bid_margin_budget_usdt),
            "askMarginBudgetUSDT": str(decision.ask_margin_budget_usdt),
            "bidNotionalUSDT": str(decision.bid_notional_usdt),
            "askNotionalUSDT": str(decision.ask_notional_usdt),
            "equityUSDT": str(account.equity_usdt),
            "freeMarginApprox": str(risk_status.free_margin_approx),
            "freeMarginPct": str(risk_status.free_margin_pct),
            "totalOrderNotional": str(account.total_order_notional),
            "totalPositionNotional": str(account.total_position_notional),
            "currentPositionQty": str(account.current_symbol_position_qty),
            "currentPositionNotionalSigned": str(account.current_symbol_position_notional_signed),
            "projectedTotalLeverage": str(
                max(decision.projected_long_notional, decision.projected_short_notional) / account.equity_usdt
                if account.equity_usdt > 0
                else 0
            ),
            "reason": decision.reason,
            "orderId": None,
            "nonce": None,
        }
    )

    if mode == "live":
        # Intentionally conservative: execution plumbing should only place LIMIT+POST_ONLY.
        # No market or IOC logic is implemented here.
        pass

    ledger.close()
    return 0
