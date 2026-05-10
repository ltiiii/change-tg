from __future__ import annotations

import asyncio
import json
from pathlib import Path

from exchange_bots.models import Order, utc_now_iso


class Storage:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.orders_path = data_dir / "orders.json"
        self.rates_path = data_dir / "rates.json"
        self._lock = asyncio.Lock()
        self._ensure_files()

    def _ensure_files(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.orders_path.exists():
            self.orders_path.write_text("[]", encoding="utf-8")
        if not self.rates_path.exists():
            self.rates_path.write_text("{}", encoding="utf-8")

    def _load_json(self, path: Path, default: object) -> object:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _save_json(self, path: Path, payload: object) -> None:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    async def get_rates(self) -> dict[str, dict[str, float | str]]:
        async with self._lock:
            data = self._load_json(self.rates_path, {})
        return dict(data)

    async def set_rate(self, currency: str, mode: str, value: float) -> dict[str, dict[str, float | str]]:
        async with self._lock:
            rates = self._load_json(self.rates_path, {})
            currency = currency.upper()
            rates.setdefault(currency, {"buy": 0.0, "sell": 0.0, "network": currency})
            rates[currency][mode] = value
            self._save_json(self.rates_path, rates)
        return dict(rates)

    async def list_orders(self) -> list[Order]:
        async with self._lock:
            raw_orders = self._load_json(self.orders_path, [])
        return [Order.from_dict(item) for item in raw_orders]

    async def get_order(self, order_id: str) -> Order | None:
        orders = await self.list_orders()
        for order in orders:
            if order.id == order_id:
                return order
        return None

    async def create_order(self, order: Order) -> Order:
        async with self._lock:
            raw_orders = self._load_json(self.orders_path, [])
            raw_orders.append(order.to_dict())
            self._save_json(self.orders_path, raw_orders)
        return order

    async def update_order_status(
        self,
        order_id: str,
        *,
        status: str,
        manager_id: int | None = None,
    ) -> Order | None:
        async with self._lock:
            raw_orders = self._load_json(self.orders_path, [])
            updated_order = None
            for item in raw_orders:
                if item["id"] != order_id:
                    continue
                item["status"] = status
                item["updated_at"] = utc_now_iso()
                if manager_id is not None:
                    item["manager_id"] = manager_id
                updated_order = Order.from_dict(item)
                break
            if updated_order is None:
                return None
            self._save_json(self.orders_path, raw_orders)
        return updated_order

    async def recent_orders(self, limit: int = 10) -> list[Order]:
        orders = await self.list_orders()
        return sorted(orders, key=lambda item: item.created_at, reverse=True)[:limit]

    async def active_orders(self) -> list[Order]:
        orders = await self.list_orders()
        active_statuses = {"new", "in_progress"}
        return [order for order in orders if order.status in active_statuses]
