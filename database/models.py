from sqlalchemy import String, Integer, Float, Boolean, BigInteger, ForeignKey, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class Restaurant(Base):
    __tablename__ = 'restaurants'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

# Новая таблица: Группы (Еда, Напитки...)
class MenuGroup(Base):
    __tablename__ = 'menu_groups'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey('restaurants.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    restaurant = relationship("Restaurant", backref="groups")

# Новая таблица: Категории (Супы, Завтраки...)
class Category(Base):
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey('menu_groups.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    group = relationship("MenuGroup", backref="categories")

class MenuItem(Base):
    __tablename__ = 'menu_items'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Привязываем товар сразу к Категории (а через нее узнаем Группу и Ресторан)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    composition: Mapped[str] = mapped_column(String(400), nullable=True)
    weight: Mapped[str] = mapped_column(String(50), nullable=True)
    
    calories: Mapped[float] = mapped_column(Float, nullable=True)
    proteins: Mapped[float] = mapped_column(Float, nullable=True)
    fats: Mapped[float] = mapped_column(Float, nullable=True)
    carbohydrates: Mapped[float] = mapped_column(Float, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    category = relationship("Category", backref="items")

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)

class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey('menu_items.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    fixed_price: Mapped[float] = mapped_column(Float, nullable=False) 
    
    item = relationship("MenuItem")
    user = relationship("User")