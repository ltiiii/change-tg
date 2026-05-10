from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from exchange_bots.config import load_settings
from exchange_bots.keyboards import admin_menu_keyboard, admin_order_keyboard
from exchange_bots.models import Order
from exchange_bots.storage import Storage


router = Router()
settings = load_settings()
storage = Storage(settings.data_dir)
client_bot = Bot(
    settings.client_bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


def format_rates(rates: dict[str, dict[str, float | str]]) -> str:
    lines = ["<b>Текущие курсы</b>", ""]
    for currency, info in sorted(rates.items()):
        lines.append(
            f"<b>{currency}</b> | buy: <code>{info['buy']}</code> | "
            f"sell: <code>{info['sell']}</code> | network: <code>{info.get('network', currency)}</code>"
        )
    return "\n".join(lines)


def format_order(order: Order) -> str:
    username = f"@{order.username}" if order.username else "без username"
    direction_label = "RUB -> crypto" if order.direction == "buy_crypto" else "crypto -> RUB"
    manager_text = str(order.manager_id) if order.manager_id else "не назначен"
    return (
        f"<b>Заявка {order.id}</b>\n\n"
        f"<b>Клиент:</b> {order.full_name} ({username})\n"
        f"<b>User ID:</b> <code>{order.user_id}</code>\n"
        f"<b>Направление:</b> {direction_label}\n"
        f"<b>Валюта:</b> {order.currency}\n"
        f"<b>Отдает:</b> {order.amount_from}\n"
        f"<b>Получает:</b> {order.amount_to}\n"
        f"<b>Курс:</b> {order.rate}\n"
        f"<b>Детали:</b>\n{order.details}\n\n"
        f"<b>Статус:</b> {order.status}\n"
        f"<b>Менеджер:</b> {manager_text}\n"
        f"<b>Создана:</b> {order.created_at}"
    )


async def notify_client(order: Order) -> None:
    status_map = {
        "in_progress": "взята в работу",
        "completed": "успешно завершена",
        "cancelled": "отменена",
    }
    status_label = status_map.get(order.status, order.status)
    await client_bot.send_message(
        order.user_id,
        f"Статус вашей заявки <b>{order.id}</b> изменен: <b>{status_label}</b>.",
    )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещен.")
        return
    await message.answer(
        "Админ-бот запущен. Здесь вы будете получать заявки и менять их статус.",
        reply_markup=admin_menu_keyboard(),
    )


@router.message(F.text == "Активные заявки")
@router.message(Command("pending"))
async def show_active_orders(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещен.")
        return

    orders = await storage.active_orders()
    if not orders:
        await message.answer("Активных заявок нет.")
        return

    for order in sorted(orders, key=lambda item: item.created_at, reverse=True):
        await message.answer(
            format_order(order),
            reply_markup=admin_order_keyboard(order.id, order.status),
        )


@router.message(F.text == "Последние заявки")
@router.message(Command("orders"))
async def show_recent_orders(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещен.")
        return

    orders = await storage.recent_orders()
    if not orders:
        await message.answer("Заявок пока нет.")
        return

    for order in orders:
        await message.answer(
            format_order(order),
            reply_markup=admin_order_keyboard(order.id, order.status),
        )


@router.message(F.text == "Курсы")
@router.message(Command("rates"))
async def show_rates(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещен.")
        return

    rates = await storage.get_rates()
    await message.answer(format_rates(rates))


@router.message(Command("setrate"))
async def set_rate(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещен.")
        return

    parts = (message.text or "").split()
    if len(parts) != 4:
        await message.answer("Формат: /setrate USDT buy 98.5")
        return

    _, currency, mode, value_raw = parts
    mode = mode.lower()
    if mode not in {"buy", "sell"}:
        await message.answer("Допустимые режимы: buy или sell.")
        return

    try:
        value = float(value_raw.replace(",", "."))
    except ValueError:
        await message.answer("Курс должен быть числом.")
        return

    if value <= 0:
        await message.answer("Курс должен быть больше нуля.")
        return

    await storage.set_rate(currency, mode, value)
    rates = await storage.get_rates()
    await message.answer(format_rates(rates))


@router.callback_query(F.data.startswith("admin:"))
async def process_admin_action(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, action, order_id = callback.data.split(":")
    status_map = {
        "take": "in_progress",
        "done": "completed",
        "cancel": "cancelled",
    }
    new_status = status_map[action]

    updated = await storage.update_order_status(
        order_id,
        status=new_status,
        manager_id=callback.from_user.id,
    )
    if updated is None:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await callback.message.edit_text(
        format_order(updated),
        reply_markup=admin_order_keyboard(updated.id, updated.status),
    )
    await notify_client(updated)
    await callback.answer("Статус обновлен")


async def main(*, handle_signals: bool = True) -> None:
    bot = Bot(
        settings.admin_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot, handle_signals=handle_signals)


if __name__ == "__main__":
    asyncio.run(main())
