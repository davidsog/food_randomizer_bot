import os
import pandas as pd
from aiogram import Router, F, types, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_PASSWORD
from keyboards.reply import admin_main_kb, cancel_kb
from database.engine import session_maker
from database.orm import add_restaurant, add_menu_items

admin_router = Router()

class AdminStates(StatesGroup):
    waiting_for_password = State()
    waiting_for_new_name = State()
    waiting_for_new_desc = State()
    waiting_for_file = State()

# --- ЛОГИКА ОТМЕНЫ ---
@admin_router.message(StateFilter('*'), F.text.lower().in_({"отмена", "🔙 отмена", "❌ выйти из админки"}))
async def cancel_action(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Вышли из режима админа.", reply_markup=types.ReplyKeyboardRemove())
        return
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=admin_main_kb)

# --- ВХОД ---
@admin_router.message(Command("admin"))
async def start_admin_login(message: types.Message, state: FSMContext):
    await message.answer("🔒 Введите пароль:", reply_markup=cancel_kb)
    await state.set_state(AdminStates.waiting_for_password)

@admin_router.message(AdminStates.waiting_for_password)
async def check_password(message: types.Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await message.answer("✅ Добро пожаловать, Шеф!", reply_markup=admin_main_kb)
        await state.clear()
    else:
        await message.answer("❌ Неверный пароль.")

# --- СОЗДАНИЕ РЕСТОРАНА ---
@admin_router.message(F.text == "🆕 Создать новый")
async def start_create_restaurant(message: types.Message, state: FSMContext):
    await message.answer("Введите название ресторана:", reply_markup=cancel_kb)
    await state.set_state(AdminStates.waiting_for_new_name)

@admin_router.message(AdminStates.waiting_for_new_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите краткое описание (или -):")
    await state.set_state(AdminStates.waiting_for_new_desc)

@admin_router.message(AdminStates.waiting_for_new_desc)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        "📂 Отправьте Excel-файл.\n"
        "Столбцы (строго так): Группа, Категория, Название блюда, Состав, Вес, Калории, Белки, Жиры, Углеводы, Цена"
    )
    await state.set_state(AdminStates.waiting_for_file)

# --- ОБРАБОТКА ФАЙЛА (ИСПРАВЛЕННАЯ 2.0) ---
@admin_router.message(AdminStates.waiting_for_file, F.document)
async def process_menu_file(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    rest_name = data['name']
    rest_desc = data['description']

    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_path = f"temp_{file.file_unique_id}.xlsx"
    await bot.download_file(file.file_path, file_path)

    try:
        # Читаем Excel
        df = pd.read_excel(file_path)
        
        # Очистка данных:
        
        # 1. Текстовые поля: убираем nan
        text_cols = ['Группа', 'Категория', 'Название блюда', 'Состав', 'Вес']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('nan', '')

        # 2. Числовые поля: меняем запятую на точку и конвертируем
        num_cols = ['Калории', 'Белки', 'Жиры', 'Углеводы', 'Цена']
        for col in num_cols:
            if col in df.columns:
                # Сначала превращаем в строку, меняем запятую на точку
                df[col] = df[col].astype(str).str.replace(',', '.')
                # Теперь превращаем в число
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        menu_data = df.to_dict(orient='records')

        async with session_maker() as session:
            restaurant = await add_restaurant(session, rest_name, rest_desc)
            await add_menu_items(session, restaurant.id, menu_data)
        
        await message.answer(f"✅ Ресторан '{rest_name}' загружен!\nБлюд: {len(menu_data)}", reply_markup=admin_main_kb)
        await state.clear()

    except Exception as e:
        error_msg = str(e)[:1000]
        await message.answer(f"❌ Ошибка при чтении файла:\n\n{error_msg}...")
    
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)