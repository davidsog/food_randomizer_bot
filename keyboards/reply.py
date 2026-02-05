from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Кнопки главного меню админа
admin_main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Добавить в текущий"),
            KeyboardButton(text="🆕 Создать новый"),
        ],
        [
            KeyboardButton(text="❌ Выйти из админки")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие..."
)

# Кнопки главного меню ПОЛЬЗОВАТЕЛЯ
user_main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🍽 Рестораны"),
            KeyboardButton(text="🛒 Мои заказы сегодня"),
        ],
        [
            KeyboardButton(text="📊 Статистика")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Что будем делать?"
)

# Кнопка отмены (пригодится внутри сценариев)
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔙 Отмена")]],
    resize_keyboard=True
)