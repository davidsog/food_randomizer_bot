import pandas as pd
from io import BytesIO
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import session_maker
from database.orm import (
    get_restaurants, get_groups, get_categories, get_items_by_category, 
    get_item, add_user, get_random_item, add_order, get_today_orders, delete_order,
    get_orders_for_stats
)
from keyboards.inline import (
    MenuCall, get_rests_kb, get_groups_kb, get_cats_kb, 
    get_items_kb, get_item_actions_kb, OrderCall, get_delete_order_kb,
    StatsCall, get_stats_kb, get_excel_kb
)
from keyboards.reply import user_main_kb

user_router = Router()

# --- 1. ГЛАВНОЕ МЕНЮ ---
@user_router.message(CommandStart())
async def start_cmd(message: types.Message):
    async with session_maker() as session:
        await add_user(session, message.from_user.id, message.from_user.username)
    await message.answer("Привет! Я помогу выбрать еду и прослежу за статистикой. 👇", reply_markup=user_main_kb)

# --- 2. КНОПКА РЕСТОРАНЫ ---
@user_router.message(F.text == "🍽 Рестораны")
async def show_restaurants(message: types.Message):
    async with session_maker() as session:
        rests = await get_restaurants(session)
    await message.answer("🍽 Выберите ресторан:", reply_markup=get_rests_kb(rests))

# --- 3. КНОПКА МОИ ЗАКАЗЫ ---
@user_router.message(F.text == "🛒 Мои заказы сегодня")
async def show_my_orders(message: types.Message):
    async with session_maker() as session:
        orders = await get_today_orders(session, message.from_user.id)
    
    if not orders:
        await message.answer("Сегодня вы еще ничего не заказывали 🤷‍♂️")
        return

    total_price = 0
    total_cals = 0
    await message.answer("📋 Ваши заказы за сегодня:")
    for order in orders:
        item = order.item
        price = order.fixed_price
        total_price += price
        total_cals += (item.calories or 0)
        info = f"🍔 <b>{item.name}</b>\n💰 {price}₽ | {item.calories} ккал"
        await message.answer(info, reply_markup=get_delete_order_kb(order.id))

    await message.answer(f"🏁 <b>ИТОГО: {total_price}₽ | {total_cals} ккал</b>")

@user_router.callback_query(OrderCall.filter(F.action == "delete"))
async def delete_order_handler(callback: types.CallbackQuery, callback_data: OrderCall):
    async with session_maker() as session:
        await delete_order(session, callback_data.order_id)
    await callback.answer("Заказ удален")
    await callback.message.delete()

# --- 4. СТАТИСТИКА ---
@user_router.message(F.text == "📊 Статистика")
async def show_stats_menu(message: types.Message):
    await message.answer("Выберите период отчета:", reply_markup=get_stats_kb())

@user_router.callback_query(StatsCall.filter(F.action == "view"))
async def show_stats_text(callback: types.CallbackQuery, callback_data: StatsCall):
    if callback_data.period == "back":
        await callback.message.edit_text("Выберите период отчета:", reply_markup=get_stats_kb())
        return

    days_map = {"week": 7, "month": 30, "all": None}
    days = days_map[callback_data.period]
    period_name = {"week": "неделю", "month": "месяц", "all": "всё время"}[callback_data.period]

    async with session_maker() as session:
        orders = await get_orders_for_stats(session, callback.from_user.id, days)

    if not orders:
        await callback.answer("За этот период заказов нет!", show_alert=True)
        return

    total_price = sum(o.fixed_price for o in orders)
    total_cals = sum(o.item.calories or 0 for o in orders)
    
    text = (
        f"📊 <b>Отчет за {period_name}:</b>\n\n"
        f"🛒 Всего заказов: {len(orders)}\n"
        f"💰 Потрачено: <b>{total_price}₽</b>\n"
        f"⚡️ Калории: {total_cals} ккал\n"
        f"📅 Средний чек: {int(total_price / len(orders))}₽\n"
    )
    await callback.message.edit_text(text, reply_markup=get_excel_kb(callback_data.period))

@user_router.callback_query(StatsCall.filter(F.action == "excel"))
async def send_stats_excel(callback: types.CallbackQuery, callback_data: StatsCall):
    await callback.answer("Генерирую файл... ⏳")
    days_map = {"week": 7, "month": 30, "all": None}
    days = days_map[callback_data.period]

    async with session_maker() as session:
        orders = await get_orders_for_stats(session, callback.from_user.id, days)

    if not orders:
        await callback.answer("Нет данных")
        return

    data = []
    for o in orders:
        data.append({
            "Дата": o.created.strftime("%Y-%m-%d %H:%M"),
            "Ресторан": o.item.category.group.restaurant.name,
            "Категория": o.item.category.name,
            "Блюдо": o.item.name,
            "Цена": o.fixed_price,
            "Калории": o.item.calories,
            "Белки": o.item.proteins,
            "Жиры": o.item.fats,
            "Углеводы": o.item.carbohydrates
        })

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Статистика')
    output.seek(0)

    filename = f"stats_{callback_data.period}.xlsx"
    input_file = types.BufferedInputFile(output.read(), filename=filename)
    await callback.message.answer_document(document=input_file, caption=f"📂 Ваш отчет за {callback_data.period}")

# --- 5. ГЛАВНЫЙ ЦИКЛ НАВИГАЦИИ ---
@user_router.callback_query(MenuCall.filter())
async def menu_navigation(callback: types.CallbackQuery, callback_data: MenuCall):
    session = session_maker()
    try:
        async with session:
            # 1. ЗАКАЗ
            if callback_data.level == 5 and callback_data.action == "order":
                await add_order(session, callback.from_user.id, callback_data.item_id, quantity=1)
                await callback.answer(f"✅ Заказ записан!", show_alert=True)
                return

            # 2. РАНДОМ / БЛЮДО
            elif callback_data.level == 4:
                item = None
                is_random = False
                if callback_data.action == "random":
                    item = await get_random_item(session, callback_data.rest_id, callback_data.group_id, callback_data.category_id)
                    if not item:
                        await callback.answer("Здесь пока пусто 🤷‍♂️", show_alert=True)
                        return
                    is_random = True
                else:
                    item = await get_item(session, callback_data.item_id)
                
                # Определяем контекст навигации (для кнопки "Назад" и "Заказать")
                if is_random:
                    # Если рандом, то "Назад" должно вести в реальную категорию блюда
                    nav_group_id = item.category.group_id
                    nav_category_id = item.category_id
                else:
                    # Если обычный просмотр, используем текущий путь
                    nav_group_id = callback_data.group_id
                    nav_category_id = callback_data.category_id
                
                text = (
                    f"{'🎲 Случайный выбор!' if is_random else ''}\n"
                    f"🍔 <b>{item.name}</b>\n\n"
                    f"⚖️ Вес: {item.weight}\n"
                    f"📃 Состав: {item.composition}\n"
                    f"⚡ Ккал: {item.calories}\n"
                    f"🥩 Б/Ж/У: {item.proteins} / {item.fats} / {item.carbohydrates}\n\n"
                    f"💰 <b>Цена: {item.price}₽</b>"
                )
                try:
                    await callback.message.edit_text(
                        text, 
                        reply_markup=get_item_actions_kb(
                            callback_data.rest_id, 
                            callback_data.group_id, 
                            callback_data.category_id, 
                            item.id, 
                            is_random=is_random,
                            nav_group_id=nav_group_id,
                            nav_category_id=nav_category_id
                        )
                    )
                except TelegramBadRequest:
                    await callback.answer("🎲 То же самое!")
                    return

            # 3. НАВИГАЦИЯ
            elif callback_data.level == 0:
                rests = await get_restaurants(session)
                await callback.message.edit_text("🍽 Выберите ресторан:", reply_markup=get_rests_kb(rests))

            elif callback_data.level == 1:
                groups = await get_groups(session, callback_data.rest_id)
                await callback.message.edit_text("📂 Выберите раздел:", reply_markup=get_groups_kb(groups, callback_data.rest_id))

            elif callback_data.level == 2:
                # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
                # Было: cats = await get_categories(session, callback_data.rest_id, callback_data.group_id)
                # Стало (rest_id убрали):
                cats = await get_categories(session, callback_data.group_id)
                await callback.message.edit_text(f"⬇ Выберите категорию:", reply_markup=get_cats_kb(cats, callback_data.rest_id, callback_data.group_id))

            elif callback_data.level == 3:
                items = await get_items_by_category(session, callback_data.category_id)
                await callback.message.edit_text(f"⬇ Выберите блюдо:", reply_markup=get_items_kb(items, callback_data.rest_id, callback_data.group_id, callback_data.category_id))

        await callback.answer()
    except Exception as e:
        print(f"Ошибка меню: {e}")
        await callback.answer("Ошибка навигации", show_alert=True)