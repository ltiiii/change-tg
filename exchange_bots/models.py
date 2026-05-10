from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Order:
    id: str
    user_id: int
    username: str | None
    full_name: str
    direction: str
    currency: str
    amount_from: float
    amount_to: float
    rate: float
    details: str
    status: str = "new"
    manager_id: int | None = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def create(
        cls,
        *,
        user_id: int,
        username: str | None,
        full_name: str,
        direction: str,
        currency: str,
        amount_from: float,
        amount_to: float,
        rate: float,
        details: str,
    ) -> "Order":
        return cls(
            id=uuid4().hex[:10].upper(),
            user_id=user_id,
            username=username,
            full_name=full_name,
            direction=direction,
            currency=currency,
            amount_from=amount_from,
            amount_to=amount_to,
            rate=rate,
            details=details,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Order":
        return cls(**payload)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
