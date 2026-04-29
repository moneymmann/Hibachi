from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

from hibachi_mm.config import BotConfig
from hibachi_mm.engine import LIVE_ACK


@dataclass
class SecurityReport:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def _is_private_file(path: Path) -> bool:
    mode = path.stat().st_mode
    group_or_other = stat.S_IRWXG | stat.S_IRWXO
    return (mode & group_or_other) == 0


def run_security_checks(config: BotConfig, mode: str, env_path: str = ".env") -> SecurityReport:
    errors: list[str] = []
    warnings: list[str] = []

    if mode == "live":
        if os.getenv("HIBACHI_ENABLE_LIVE_TRADING") != LIVE_ACK:
            errors.append("HIBACHI_ENABLE_LIVE_TRADING 확인 문자열이 없습니다.")
        if config.exit_policy.maker_entry_only and not config.exit_policy.emergency_taker_exit:
            errors.append("emergency_taker_exit=false 는 live 금지 구성입니다.")

    if not config.exchange.dedicated_subaccount_confirmed:
        warnings.append("dedicated_subaccount_confirmed=false 입니다. 전용 서브계정 사용을 강력 권장합니다.")

    env_file = Path(env_path)
    if env_file.exists() and not _is_private_file(env_file):
        warnings.append(f"{env_path} 파일 권한이 느슨합니다. chmod 600 권장")

    state_path = Path(config.state.sqlite_path)
    if state_path.exists() and not _is_private_file(state_path):
        warnings.append(f"state db 파일 권한이 느슨합니다: {state_path}")

    key_names = [
        config.exchange.api_key_env,
        config.exchange.private_key_env,
        config.exchange.public_key_env,
        config.exchange.account_id_env,
    ]
    for key in key_names:
        if mode == "live" and not os.getenv(key):
            errors.append(f"필수 환경변수 누락: {key}")

    for line_key in ["api_key", "private_key", "secret"]:
        if line_key in config.exchange.api_endpoint.lower() or line_key in config.exchange.data_api_endpoint.lower():
            warnings.append("endpoint 값에 민감정보 문자열 패턴이 있어 확인 필요")

    return SecurityReport(errors=errors, warnings=warnings)
