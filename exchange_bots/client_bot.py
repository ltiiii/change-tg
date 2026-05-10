from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message

from exchange_bots.config import load_settings
from exchange_bots.keyboards import (
    BUY_BUTTON,
    CALCULATOR_BUTTON,
    CRYPTO_SWAP_BUTTON,
    MIXER_BUTTON,
    OPERATOR_BUTTON,
    PROMO_BUTTON,
    REFERRAL_BUTTON,
    REVIEWS_BUTTON,
    RULES_BUTTON,
    SELL_BUTTON,
    admin_order_keyboard,
    client_main_keyboard,
    client_start_inline_keyboard,
    confirm_keyboard,
    currency_keyboard,
    direction_keyboard,
)
from exchange_bots.models import Order
from exchange_bots.storage import Storage


class ExchangeForm(StatesGroup):
    direction = State()
    currency = State()
    amount = State()
    details = State()


router = Router()
settings = load_settings()
storage = Storage(settings.data_dir)
admin_bot = Bot(
    settings.admin_bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)


WELCOME_TEXT = (
    "♻️ Wassup, HUSTLE TRADE это обменник электронных валют.\n"
    "Наша команда обменивает крипту с минимальной комиссией и быстро проводит сделки.\n\n"
    "💵 Для заказа выбери, что желаешь Купить либо Продать, "
    "но перед оплатой обязательно прочитай наши 📜 правила."
)


def rules_text() -> str:
    return (
        "📜 <b>Правила обмена</b>\n\n"
        "1. Перед переводом дождитесь подтверждения от оператора.\n"
        "2. Всегда проверяйте реквизиты и сеть перевода.\n"
        "3. Курс может быть зафиксирован только после принятия заявки.\n"
        "4. Если указаны неверные данные, заявка может быть отменена.\n"
        "5. Сохраняйте чек и переписку до завершения обмена."
    )


def operator_text() -> str:
    return (
        "🆘 <b>Оператор</b>\n\n"
        "Опишите вопрос или создайте заявку через кнопки меню. "
        "После этого администратор свяжется с вами в Telegram."
    )


def promo_text() -> str:
    return (
        "🗂 <b>Промокод</b>\n\n"
        "Пока раздел работает как заглушка. "
        "Позже сюда можно добавить активацию кодов на скидку или повышенный курс."
    )


def mixer_text() -> str:
    return (
        "🪄 <b>Чистка / Миксер BTC</b>\n\n"
        "Этот раздел пока информационный. "
        "Если хотите, следующим шагом я могу добавить отдельный сценарий заявок именно для этой услуги."
    )


def reviews_text() -> str:
    return (
        "📝 <b>Отзывы</b>\n\n"
        "Сюда можно вывести ссылки на ваш Telegram-канал, чат с отзывами или отдельный пост с репутацией."
    )


def format_order_preview(payload: dict[str, str | float]) -> str:
    direction_label = "RUB -> crypto" if payload["direction"] == "buy_crypto" else "crypto -> RUB"
    return (
        "🧾 <b>Проверьте заявку</b>\n\n"
        f"<b>Направление:</b> {direction_label}\n"
        f"<b>Валюта:</b> {payload['currency']}\n"
        f"<b>Отдаете:</b> {payload['amount_from']}\n"
        f"<b>Получаете:</b> {payload['amount_to']}\n"
        f"<b>Курс:</b> {payload['rate']}\n"
        f"<b>Реквизиты / детали:</b>\n{payload['details']}"
    )


def format_admin_order(order: Order) -> str:
    username = f"@{order.username}" if order.username else "без username"
    direction_label = "RUB -> crypto" if order.direction == "buy_crypto" else "crypto -> RUB"
    return (
        "📥 <b>Новая заявка</b>\n\n"
        f"<b>ID:</b> {order.id}\n"
        f"<b>Клиент:</b> {order.full_name} ({username})\n"
        f"<b>User ID:</b> <code>{order.user_id}</code>\n"
        f"<b>Направление:</b> {direction_label}\n"
        f"<b>Валюта:</b> {order.currency}\n"
        f"<b>Отдает:</b> {order.amount_from}\n"
        f"<b>Получает:</b> {order.amount_to}\n"
        f"<b>Курс:</b> {order.rate}\n"
        f"<b>Детали:</b>\n{order.details}\n\n"
        f"<b>Статус:</b> {order.status}"
    )


async def notify_admins(order: Order) -> None:
    message_text = format_admin_order(order)
    for admin_id in settings.admin_ids:
        await admin_bot.send_message(
            admin_id,
            message_text,
            reply_markup=admin_order_keyboard(order.id, order.status),
        )


async def send_welcome(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=client_start_inline_keyboard())
    await message.answer("Выберите действие в меню ниже.", reply_markup=client_main_keyboard())


async def send_referral(message: Message, user_id: int) -> None:
    referral_link = f"https://t.me/{(await message.bot.me()).username}?start=ref_{user_id}"
    await message.answer(
        "👥 <b>Рефералка</b>\n\n"
        f"Ваша персональная ссылка:\n{referral_link}\n\n"
        "В текущем MVP ссылка генерируется, но начисления пока не ведутся."
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await send_welcome(message, state)


@router.message(F.text == RULES_BUTTON)
async def show_rules(message: Message) -> None:
    await message.answer(rules_text())


@router.message(F.text == OPERATOR_BUTTON)
async def show_operator(message: Message) -> None:
    await message.answer(operator_text())


@router.message(F.text == PROMO_BUTTON)
async def show_promo(message: Message) -> None:
    await message.answer(promo_text())


@router.message(F.text == MIXER_BUTTON)
async def show_mixer(message: Message) -> None:
    await message.answer(mixer_text())


@router.message(F.text == REVIEWS_BUTTON)
async def show_reviews(message: Message) -> None:
    await message.answer(reviews_text())


@router.message(F.text == REFERRAL_BUTTON)
async def show_referral(message: Message) -> None:
    await send_referral(message, message.from_user.id)


@router.message(F.text == BUY_BUTTON)
async def start_buy_exchange(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(direction="buy_crypto")
    await state.set_state(ExchangeForm.currency)
    rates = await storage.get_rates()
    await message.answer("💸 Выберите валюту для покупки.", reply_markup=currency_keyboard(sorted(rates.keys())))


@router.message(F.text == SELL_BUTTON)
async def start_sell_exchange(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(direction="sell_crypto")
    await state.set_state(ExchangeForm.currency)
    rates = await storage.get_rates()
    await message.answer("💰 Выберите валюту для продажи.", reply_markup=currency_keyboard(sorted(rates.keys())))


@router.message(F.text == CALCULATOR_BUTTON)
async def start_exchange_calculator(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ExchangeForm.direction)
    await message.answer("🧮 Выберите направление расчета.", reply_markup=direction_keyboard())


@router.message(F.text == CRYPTO_SWAP_BUTTON)
async def start_crypto_to_crypto(message: Message) -> None:
    await message.answer(
        "🔄 <b>Обмен крипта - на крипту</b>\n\n"
        "Этот сценарий пока не включен в логику обмена. "
        "Если нужно, следующим шагом я добавлю отдельную заявку: какую монету отдаете, какую получаете, сеть и сумму."
    )


@router.callback_query(F.data == "info:rules")
async def show_rules_inline(callback: CallbackQuery) -> None:
    await callback.message.answer(rules_text())
    await callback.answer()


@router.callback_query(F.data == "info:calculator")
async def start_exchange_calculator_inline(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ExchangeForm.direction)
    await callback.message.answer("🧮 Выберите направление расчета.", reply_markup=direction_keyboard())
    await callback.answer()


@router.callback_query(F.data == "info:reviews")
async def show_reviews_inline(callback: CallbackQuery) -> None:
    await callback.message.answer(reviews_text())
    await callback.answer()


@router.callback_query(F.data == "info:referral")
async def show_referral_inline(callback: CallbackQuery) -> None:
    referral_link = f"https://t.me/{(await callback.message.bot.me()).username}?start=ref_{callback.from_user.id}"
    await callback.message.answer(
        "👥 <b>Рефералка</b>\n\n"
        f"Ваша персональная ссылка:\n{referral_link}\n\n"
        "В текущем MVP ссылка генерируется, но начисления пока не ведутся."
    )
    await callback.answer()


@router.callback_query(F.data == "info:mixer")
async def show_mixer_inline(callback: CallbackQuery) -> None:
    await callback.message.answer(mixer_text())
    await callback.answer()


@router.callback_query(F.data == "info:operator")
async def show_operator_inline(callback: CallbackQuery) -> None:
    await callback.message.answer(operator_text())
    await callback.answer()


@router.callback_query(F.data.startswith("direction:"))
async def pick_direction(callback: CallbackQuery, state: FSMContext) -> None:
    direction = callback.data.split(":", 1)[1]
    rates = await storage.get_rates()
    await state.update_data(direction=direction)
    await state.set_state(ExchangeForm.currency)
    await callback.message.answer(
        "💱 Выберите валюту.",
        reply_markup=currency_keyboard(sorted(rates.keys())),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("currency:"))
async def pick_currency(callback: CallbackQuery, state: FSMContext) -> None:
    currency = callback.data.split(":", 1)[1].upper()
    data = await state.get_data()
    direction = data["direction"]
    rates = await storage.get_rates()
    rate_info = rates[currency]
    network = rate_info.get("network", currency)
    rate = rate_info["buy"] if direction == "buy_crypto" else rate_info["sell"]

    await state.update_data(currency=currency, rate=rate, network=network)
    await state.set_state(ExchangeForm.amount)

    if direction == "buy_crypto":
        text = (
            f"💸 Вы выбрали <b>{currency}</b> в сети <b>{network}</b>.\n"
            f"Текущий курс: <b>{rate} RUB</b> за 1 {currency}.\n\n"
            "Введите сумму в <b>рублях</b>, которую клиент отдает."
        )
    else:
        text = (
            f"💰 Вы выбрали <b>{currency}</b> в сети <b>{network}</b>.\n"
            f"Текущий курс выплаты: <b>{rate} RUB</b> за 1 {currency}.\n\n"
            f"Введите сумму в <b>{currency}</b>, которую клиент отдает."
        )

    await callback.message.answer(text)
    await callback.answer()


@router.message(ExchangeForm.amount)
async def capture_amount(message: Message, state: FSMContext) -> None:
    raw_amount = (message.text or "").replace(",", ".").strip()
    try:
        amount = float(raw_amount)
    except ValueError:
        await message.answer("Введите числовую сумму. Пример: <code>15000</code> или <code>0.25</code>.")
        return

    if amount <= 0:
        await message.answer("Сумма должна быть больше нуля.")
        return

    data = await state.get_data()
    direction = data["direction"]
    currency = data["currency"]
    rate = float(data["rate"])

    if direction == "buy_crypto":
        amount_from = round(amount, 2)
        amount_to = round(amount / rate, 8)
        prompt = (
            f"✅ По текущему курсу клиент получит примерно <b>{amount_to} {currency}</b>.\n\n"
            "Отправьте детали заявки: кошелек клиента, банк для оплаты, имя получателя, комментарии."
        )
    else:
        amount_from = round(amount, 8)
        amount_to = round(amount * rate, 2)
        prompt = (
            f"✅ По текущему курсу клиент получит примерно <b>{amount_to} RUB</b>.\n\n"
            "Отправьте детали заявки: куда выплачивать RUB, банк, ФИО, номер карты или СБП, комментарии."
        )

    await state.update_data(amount_from=amount_from, amount_to=amount_to)
    await state.set_state(ExchangeForm.details)
    await message.answer(prompt)


@router.message(ExchangeForm.details)
async def capture_details(message: Message, state: FSMContext) -> None:
    details = (message.text or "").strip()
    if len(details) < 8:
        await message.answer("Опишите детали чуть подробнее, чтобы админ смог провести обмен.")
        return

    await state.update_data(details=details)
    data = await state.get_data()
    await message.answer(
        format_order_preview(data),
        reply_markup=confirm_keyboard(),
    )


@router.callback_query(F.data == "order:cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("❌ Создание заявки отменено.", reply_markup=client_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "order:confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    user = callback.from_user
    order = Order.create(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        direction=data["direction"],
        currency=data["currency"],
        amount_from=float(data["amount_from"]),
        amount_to=float(data["amount_to"]),
        rate=float(data["rate"]),
        details=data["details"],
    )
    await storage.create_order(order)
    await notify_admins(order)
    await callback.message.answer(
        f"✅ Заявка <b>{order.id}</b> создана. Администратор уже получил уведомление.",
        reply_markup=client_main_keyboard(),
    )
    await state.clear()
    await callback.answer()


async def main(*, handle_signals: bool = True) -> None:
    bot = Bot(
        settings.client_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot, handle_signals=handle_signals)


if __name__ == "__main__":
    asyncio.run(main())
