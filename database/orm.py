from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from datetime import date

from database.models import Restaurant, MenuGroup, Category, MenuItem, User, Order

# --- ДОБАВЛЕНИЕ (ДЛЯ АДМИНА) ---
async def add_restaurant(session: AsyncSession, name: str, description: str):
    res = await session.execute(select(Restaurant).where(Restaurant.name == name))
    existing = res.scalar()
    if existing:
        existing.description = description
        await session.commit()
        return existing
    else:
        new_rest = Restaurant(name=name, description=description)
        session.add(new_rest)
        await session.commit()
        return new_rest

async def add_menu_items(session: AsyncSession, restaurant_id: int, items_data: list):
    # Очистка старого меню этого ресторана
    # Удаляем группы (каскадно удалятся категории и блюда)
    await session.execute(delete(MenuGroup).where(MenuGroup.restaurant_id == restaurant_id))
    
    # Словари для кэширования ID, чтобы не делать лишние запросы
    groups_cache = {} # "Название": id
    cats_cache = {}   # ("Название", group_id): id

    for row in items_data:
        g_name = row.get('Группа', 'Разное')
        c_name = row.get('Категория', 'Общее')
        
        # 1. Работаем с Группой
        if g_name not in groups_cache:
            # Создаем группу
            group = MenuGroup(restaurant_id=restaurant_id, name=g_name)
            session.add(group)
            await session.flush() # Чтобы получить ID сразу
            groups_cache[g_name] = group.id
        
        g_id = groups_cache[g_name]
        
        # 2. Работаем с Категорией
        if (c_name, g_id) not in cats_cache:
            cat = Category(group_id=g_id, name=c_name)
            session.add(cat)
            await session.flush()
            cats_cache[(c_name, g_id)] = cat.id
            
        c_id = cats_cache[(c_name, g_id)]

        # 3. Создаем Блюдо
        new_item = MenuItem(
            category_id=c_id,
            name=row.get('Название блюда'),
            composition=row.get('Состав', ''),
            weight=str(row.get('Вес', '')),
            calories=row.get('Калории', 0),
            proteins=row.get('Белки', 0),
            fats=row.get('Жиры', 0),
            carbohydrates=row.get('Углеводы', 0),
            price=row.get('Цена', 0)
        )
        session.add(new_item)
    
    await session.commit()

# --- ПОЛУЧЕНИЕ ДАННЫХ (ДЛЯ ЮЗЕРА) ---

async def get_restaurants(session: AsyncSession):
    query = select(Restaurant).where(Restaurant.is_active == True)
    result = await session.execute(query)
    return result.scalars().all()

async def get_groups(session: AsyncSession, restaurant_id: int):
    query = select(MenuGroup).where(MenuGroup.restaurant_id == restaurant_id)
    result = await session.execute(query)
    return result.scalars().all()

async def get_categories(session: AsyncSession, group_id: int):
    query = select(Category).where(Category.group_id == group_id)
    result = await session.execute(query)
    return result.scalars().all()

async def get_items_by_category(session: AsyncSession, category_id: int):
    query = select(MenuItem).where(MenuItem.category_id == category_id)
    result = await session.execute(query)
    return result.scalars().all()

async def get_item(session: AsyncSession, item_id: int):
    # Подгружаем сразу категорию и группу, чтобы знать имена для кнопки "Назад"
    query = select(MenuItem).options(joinedload(MenuItem.category).joinedload(Category.group)).where(MenuItem.id == item_id)
    result = await session.execute(query)
    return result.scalar()

# --- РАНДОМ ---
async def get_random_item(session: AsyncSession, restaurant_id: int = None, group_id: int = 0, category_id: int = 0):
    query = select(MenuItem).options(joinedload(MenuItem.category).joinedload(Category.group)).join(Category).join(MenuGroup)
    
    if category_id:
        query = query.where(MenuItem.category_id == category_id)
    elif group_id:
        query = query.where(Category.group_id == group_id)
    elif restaurant_id:
        query = query.where(MenuGroup.restaurant_id == restaurant_id)
        
    query = query.order_by(func.random()).limit(1)
    result = await session.execute(query)
    return result.scalar()

# --- ЮЗЕРЫ И ЗАКАЗЫ ---
async def add_user(session: AsyncSession, telegram_id: int, username: str):
    query = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(query)
    user = result.scalar()
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.commit()
    return user

async def add_order(session: AsyncSession, telegram_id: int, item_id: int, quantity: int = 1):
    user_res = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user_res.scalar()
    if not user:
        user = User(telegram_id=telegram_id, username="Unknown")
        session.add(user)
        await session.flush()

    item = await session.get(MenuItem, item_id)
    new_order = Order(user_id=user.id, item_id=item_id, quantity=quantity, fixed_price=item.price)
    session.add(new_order)
    await session.commit()

async def get_today_orders(session: AsyncSession, telegram_id: int):
    user_res = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user_res.scalar()
    if not user: return []

    query = select(Order).options(joinedload(Order.item)).where(
        Order.user_id == user.id,
        func.date(Order.created) == date.today()
    ).order_by(Order.created.desc())
    
    result = await session.execute(query)
    return result.scalars().all()

async def delete_order(session: AsyncSession, order_id: int):
    await session.execute(delete(Order).where(Order.id == order_id))
    await session.commit()

from datetime import datetime, timedelta

# Получить статистику за период (days=None значит "за все время")
async def get_orders_for_stats(session: AsyncSession, telegram_id: int, days: int = None):
    user_res = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user_res.scalar()
    if not user: return []

    query = select(Order).options(
        joinedload(Order.item).joinedload(MenuItem.category).joinedload(Category.group).joinedload(MenuGroup.restaurant)
    ).where(Order.user_id == user.id)

    # Фильтр по дате, если указано кол-во дней
    if days:
        start_date = datetime.now() - timedelta(days=days)
        query = query.where(Order.created >= start_date)
    
    query = query.order_by(Order.created.desc())
    
    result = await session.execute(query)
    return result.scalars().all()