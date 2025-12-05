from db import engine
from sqlalchemy import text
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
import logging
from datetime import datetime, timedelta

# Используем Agg backend для работы без GUI (важно для Render)
matplotlib.use('Agg')
logger = logging.getLogger(__name__)

def get_top_niches(limit=10):
    """Получение ТОП ниш по количеству товаров и отзывов"""
    try:
        with engine.connect() as conn:
            # Запрос для получения ТОП категорий
            query = text("""
                SELECT 
                    category as name,
                    COUNT(*) as products,
                    SUM(reviews) as demand
                FROM products 
                WHERE category IS NOT NULL 
                AND category != ''
                AND is_active = 1
                GROUP BY category 
                ORDER BY demand DESC, products DESC
                LIMIT :limit
            """)
            
            result = conn.execute(query, {"limit": limit})
            
            niches_list = []
            for row in result:
                niches_list.append({
                    "name": row.name,
                    "products": row.products,
                    "demand": int(row.demand) if row.demand else 0
                })
            
            logger.info(f"Получено {len(niches_list)} ниш")
            return niches_list
            
    except Exception as e:
        logger.error(f"Ошибка получения ниш: {e}")
        # Возвращаем тестовые данные при ошибке
        return [
            {"name": "Смартфоны", "products": 42, "demand": 1250},
            {"name": "Ноутбуки", "products": 35, "demand": 840},
            {"name": "Наушники", "products": 28, "demand": 3120},
            {"name": "Смарт-часы", "products": 19, "demand": 1560},
            {"name": "Планшеты", "products": 15, "demand": 920}
        ]

def get_price_trend(product_id):
    """Получение истории цен для товара"""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    price,
                    timestamp
                FROM price_history 
                WHERE product_id = :product_id
                ORDER BY timestamp ASC
            """)
            
            result = conn.execute(query, {"product_id": product_id})
            trend_data = []
            
            for row in result:
                trend_data.append({
                    "price": float(row.price),
                    "time": row.timestamp
                })
            
            logger.info(f"Получено {len(trend_data)} записей истории цен для товара {product_id}")
            return trend_data
            
    except Exception as e:
        logger.error(f"Ошибка получения истории цен для товара {product_id}: {e}")
        return []

def plot_price_trend(product_id):
    """Построение графика динамики цены"""
    try:
        trend = get_price_trend(product_id)
        
        if not trend:
            logger.warning(f"Нет данных для построения графика товара {product_id}")
            return None
        
        # Подготавливаем данные
        times = [t['time'] for t in trend]
        prices = [t['price'] for t in trend]
        
        # Получаем информацию о товаре
        product_name = "Товар"
        with engine.connect() as conn:
            query = text("SELECT name FROM products WHERE id = :product_id")
            result = conn.execute(query, {"product_id": product_id})
            row = result.fetchone()
            if row:
                product_name = row.name
        
        # Создаем график
        plt.figure(figsize=(12, 6), facecolor='#f8f9fa')
        
        # Основной график
        plt.plot(times, prices, marker='o', linestyle='-', 
                color='#2c3e50', linewidth=2.5, markersize=6,
                markerfacecolor='#e74c3c', markeredgecolor='#c0392b')
        
        # Настройки графика
        plt.title(f"📈 Динамика цены: {product_name[:50]}...", 
                 fontsize=16, fontweight='bold', color='#2c3e50', pad=20)
        plt.xlabel("Дата", fontsize=12, color='#34495e')
        plt.ylabel("Цена (₸)", fontsize=12, color='#34495e')
        
        # Форматирование оси X для дат
        plt.gcf().autofmt_xdate()
        
        # Добавляем сетку
        plt.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # Добавляем аннотации для минимального и максимального значения
        min_price = min(prices)
        max_price = max(prices)
        min_time = times[prices.index(min_price)]
        max_time = times[prices.index(max_price)]
        
        # Линии минимума и максимума
        plt.axhline(y=min_price, color='#27ae60', linestyle=':', alpha=0.7, linewidth=1.5)
        plt.axhline(y=max_price, color='#e74c3c', linestyle=':', alpha=0.7, linewidth=1.5)
        
        # Аннотации
        plt.annotate(f'Мин: {min_price:,.0f}₸', 
                    xy=(min_time, min_price),
                    xytext=(10, 10),
                    textcoords='offset points',
                    color='#27ae60',
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#d5f4e6', alpha=0.8))
        
        plt.annotate(f'Макс: {max_price:,.0f}₸', 
                    xy=(max_time, max_price),
                    xytext=(10, -20),
                    textcoords='offset points',
                    color='#e74c3c',
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#fadbd8', alpha=0.8))
        
        # Текущая цена
        current_price = prices[-1]
        plt.annotate(f'Текущая: {current_price:,.0f}₸', 
                    xy=(times[-1], current_price),
                    xytext=(-100, 20),
                    textcoords='offset points',
                    arrowprops=dict(arrowstyle='->', color='#3498db'),
                    color='#2980b9',
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='#ebf5fb', alpha=0.9))
        
        # Настройка внешнего вида
        plt.gca().set_facecolor('#ffffff')
        plt.tight_layout()
        
        # Сохраняем в буфер
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', 
                   facecolor=plt.gcf().get_facecolor())
        buf.seek(0)
        plt.close()
        
        logger.info(f"График для товара {product_id} успешно построен")
        return buf
        
    except Exception as e:
        logger.error(f"Ошибка построения графика для товара {product_id}: {e}")
        return None