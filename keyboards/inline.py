from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

# Используем короткий префикс 'm' и только ID
class MenuCall(CallbackData, prefix="m"):
    level: int
    rest_id: int = 0
    group_id: int = 0
    category_id: int = 0
    item_id: int = 0
    action: str = "_" 

class OrderCall(CallbackData, prefix="o"):
    action: str
    order_id: int

def get_delete_order_kb(order_id):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Удалить", callback_data=OrderCall(action="delete", order_id=order_id).pack()))
    return builder.as_markup()

def get_nav_buttons(builder, level, rest_id=0, group_id=0, category_id=0):
    if level == 1:
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data=MenuCall(level=0).pack()))
    elif level == 2:
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data=MenuCall(level=1, rest_id=rest_id).pack()))
    elif level == 3:
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data=MenuCall(level=2, rest_id=rest_id, group_id=group_id).pack()))
    elif level == 4:
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data=MenuCall(level=3, rest_id=rest_id, group_id=group_id, category_id=category_id).pack()))
    return builder

def get_rests_kb(restaurants):
    builder = InlineKeyboardBuilder()
    for rest in restaurants:
        builder.add(InlineKeyboardButton(text=rest.name, callback_data=MenuCall(level=1, rest_id=rest.id).pack()))
    builder.adjust(2)
    return builder.as_markup()

def get_groups_kb(groups, rest_id):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🎲 Случайное из ресторана", callback_data=MenuCall(level=4, rest_id=rest_id, action="random").pack()))
    
    for gr in groups:
        builder.add(InlineKeyboardButton(text=gr.name, callback_data=MenuCall(level=2, rest_id=rest_id, group_id=gr.id).pack()))
    builder.adjust(1, 2)
    get_nav_buttons(builder, 1, rest_id=rest_id)
    return builder.as_markup()

def get_cats_kb(cats, rest_id, group_id):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🎲 Случайное здесь", callback_data=MenuCall(level=4, rest_id=rest_id, group_id=group_id, action="random").pack()))
    
    for cat in cats:
        builder.add(InlineKeyboardButton(text=cat.name, callback_data=MenuCall(level=3, rest_id=rest_id, group_id=group_id, category_id=cat.id).pack()))
    builder.adjust(1, 2)
    get_nav_buttons(builder, 2, rest_id, group_id=group_id)
    return builder.as_markup()

def get_items_kb(items, rest_id, group_id, category_id):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🎲 Случайное здесь", callback_data=MenuCall(level=4, rest_id=rest_id, group_id=group_id, category_id=category_id, action="random").pack()))
    
    for item in items:
        builder.add(InlineKeyboardButton(text=f"{item.name} | {item.price}₽", callback_data=MenuCall(level=4, rest_id=rest_id, group_id=group_id, category_id=category_id, item_id=item.id).pack()))
    builder.adjust(1)
    get_nav_buttons(builder, 3, rest_id, group_id=group_id, category_id=category_id)
    return builder.as_markup()

def get_item_actions_kb(rest_id, group_id, category_id, item_id, is_random=False):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Я взял это (1 шт)", callback_data=MenuCall(level=5, rest_id=rest_id, group_id=group_id, category_id=category_id, item_id=item_id, action="order").pack()))
    
    if is_random:
        builder.add(InlineKeyboardButton(text="🔄 Предложи другое", callback_data=MenuCall(level=4, rest_id=rest_id, group_id=group_id, category_id=category_id, action="random").pack()))
    
    builder.adjust(1)
    # Возврат в список блюд (уровень 3)
    get_nav_buttons(builder, 4, rest_id, group_id, category_id)
    return builder.as_markup()

# --- СТАТИСТИКА ---
class StatsCall(CallbackData, prefix="stats"):
    period: str # 'week', 'month', 'all'
    action: str # 'view', 'excel'

def get_stats_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📅 За неделю", callback_data=StatsCall(period="week", action="view").pack()))
    builder.add(InlineKeyboardButton(text="🗓 За месяц", callback_data=StatsCall(period="month", action="view").pack()))
    builder.add(InlineKeyboardButton(text="♾ За всё время", callback_data=StatsCall(period="all", action="view").pack()))
    return builder.as_markup()

def get_excel_kb(period):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📥 Скачать Excel", callback_data=StatsCall(period=period, action="excel").pack()))
    # Кнопка назад к выбору периода
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data=StatsCall(period="back", action="view").pack()))
    return builder.as_markup()