from apscheduler.schedulers.background import BackgroundScheduler
import logging
from db import engine
import random
from datetime import datetime

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def update_all_categories():
    """Обновление данных из всех категорий"""
    try:
        logger.info("Запуск обновления данных...")
        
        # Здесь должен быть реальный парсинг
        # Для примера обновляем тестовые данные
        
        with engine.connect() as conn:
            # Обновляем цены в истории для тестовых товаров
            for product_id in range(1, 6):
                new_price = random.uniform(10000, 1000000)
                conn.execute(
                    "INSERT INTO price_history (product_id, price, timestamp) VALUES (?, ?, ?)",
                    (product_id, new_price, datetime.utcnow())
                )
        
        logger.info("Обновление данных завершено успешно")
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении данных: {e}")

# Настраиваем планировщик: обновление каждые 6 часов
scheduler.add_job(
    update_all_categories,
    'interval',
    hours=6,
    id='update_job',
    name='Обновление данных Kaspi'
)

# Автоматический запуск планировщика
try:
    if not scheduler.running:
        scheduler.start()
        logger.info("Планировщик запущен")
except Exception as e:
    logger.error(f"Ошибка запуска планировщика: {e}")