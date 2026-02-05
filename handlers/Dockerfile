# Используем легкий Linux с Python 3.10
FROM python:3.10-slim

# Указываем рабочую папку внутри контейнера
WORKDIR /app

# Сначала копируем только список библиотек (для кэширования)
COPY requirements.txt .

# Устанавливаем библиотеки
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта
COPY . .

# Команда для запуска бота
CMD ["python", "main.py"]