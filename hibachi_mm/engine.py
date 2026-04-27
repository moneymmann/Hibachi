from __future__ import annotations

import os

from hibachi_mm.config import BotConfig

LIVE_ACK = "I_UNDERSTAND_PERP_RISK"


class LiveGateError(RuntimeError):
    pass


def validate_live_gate(config: BotConfig, unknown_open_orders_count: int) -> None:
    if os.getenv("HIBACHI_ENABLE_LIVE_TRADING") != LIVE_ACK:
        raise LiveGateError("HIBACHI_ENABLE_LIVE_TRADING is not acknowledged")
    if config.exit_policy.maker_entry_only and not config.exit_policy.emergency_taker_exit:
        raise LiveGateError("maker_only_exit mode is forbidden in live")
    if (not config.exchange.allow_unknown_open_orders) and unknown_open_orders_count > 0:
        raise LiveGateError("unknown open orders exist")


def can_enable_cancel_on_disconnect(config: BotConfig) -> bool:
    return bool(config.exchange.dedicated_subaccount_confirmed)
