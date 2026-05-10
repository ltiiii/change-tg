from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


BUY_BUTTON = "↙️ Купить"
SELL_BUTTON = "↗️ Продать"
CRYPTO_SWAP_BUTTON = "🔄 Обмен крипта - на крипту"
PROMO_BUTTON = "🗂 Промокод"
CALCULATOR_BUTTON = "🧮 Калькулятор"
MIXER_BUTTON = "🪄 Чистка / Миксер BTC"
REVIEWS_BUTTON = "📝 Отзывы"
REFERRAL_BUTTON = "👥 Рефералка"
OPERATOR_BUTTON = "🆘 Оператор"
RULES_BUTTON = "📜 Правила"


def client_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUY_BUTTON), KeyboardButton(text=SELL_BUTTON)],
            [KeyboardButton(text=CRYPTO_SWAP_BUTTON)],
            [KeyboardButton(text=PROMO_BUTTON)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери нужный раздел",
    )


def client_start_inline_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=RULES_BUTTON, callback_data="info:rules")
    builder.button(text=CALCULATOR_BUTTON, callback_data="info:calculator")
    builder.button(text=REVIEWS_BUTTON, callback_data="info:reviews")
    builder.button(text=REFERRAL_BUTTON, callback_data="info:referral")
    builder.button(text=MIXER_BUTTON, callback_data="info:mixer")
    builder.button(text=OPERATOR_BUTTON, callback_data="info:operator")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def direction_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💸 RUB -> Крипта", callback_data="direction:buy_crypto")
    builder.button(text="💰 Крипта -> RUB", callback_data="direction:sell_crypto")
    builder.adjust(1)
    return builder.as_markup()


def currency_keyboard(currencies: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for currency in currencies:
        builder.button(text=f"💱 {currency}", callback_data=f"currency:{currency}")
    builder.adjust(3)
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="order:confirm")
    builder.button(text="❌ Отменить", callback_data="order:cancel")
    builder.adjust(2)
    return builder.as_markup()


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Активные заявки"), KeyboardButton(text="Последние заявки")],
            [KeyboardButton(text="Курсы")],
        ],
        resize_keyboard=True,
    )


def admin_order_keyboard(order_id: str, status: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if status == "new":
        builder.button(text="🟡 Взять в работу", callback_data=f"admin:take:{order_id}")
    if status in {"new", "in_progress"}:
        builder.button(text="✅ Завершить", callback_data=f"admin:done:{order_id}")
        builder.button(text="❌ Отменить", callback_data=f"admin:cancel:{order_id}")
    builder.adjust(1, 2)
    return builder.as_markup()
