import os
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, MetaData, DateTime, Text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Получаем URL базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")

# Для Render PostgreSQL меняем префикс
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("Обновлен URL для PostgreSQL")

logger.info(f"Подключение к базе данных")

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"connect_timeout": 10}
    )
    
    # Тестируем подключение
    with engine.connect() as conn:
        conn.execute("SELECT 1")
    
    logger.info("✅ Подключение к базе данных успешно")
    
except Exception as e:
    logger.error(f"❌ Ошибка подключения к базе данных: {e}")
    # Для локальной разработки создаем SQLite базу
    if "sqlite" not in DATABASE_URL:
        DATABASE_URL = "sqlite:///local.db"
        engine = create_engine(DATABASE_URL)
        logger.info("Создана локальная SQLite база данных")

metadata = MetaData()

# Таблица товаров
products = Table(
    'products',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(500), nullable=False),
    Column('category', String(200)),
    Column('price', Float),
    Column('rating', Float),
    Column('reviews', Integer, default=0),
    Column('url', Text),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('is_active', Integer, default=1)
)

# Таблица истории цен
price_history = Table(
    'price_history',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('product_id', Integer, nullable=False),
    Column('price', Float, nullable=False),
    Column('timestamp', DateTime, default=datetime.utcnow, nullable=False),
    Column('source', String(50), default='kaspi')
)

def init_db():
    """Инициализация базы данных"""
    try:
        # Создаем таблицы
        metadata.create_all(engine)
        logger.info("✅ Таблицы базы данных созданы/проверены")
        
        # Создаем индексы для оптимизации
        with engine.connect() as conn:
            # Индекс для быстрого поиска по product_id в истории цен
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_history_product_id 
                ON price_history(product_id)
            """)
            
            # Индекс для сортировки по времени
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_history_timestamp 
                ON price_history(timestamp DESC)
            """)
            
            # Индекс для категорий
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_products_category 
                ON products(category)
            """)
            
            logger.info("✅ Индексы созданы/проверены")
        
        # Добавляем тестовые данные если таблица пуста
        with engine.connect() as conn:
            result = conn.execute("SELECT COUNT(*) FROM products")
            count = result.scalar()
            
            if count == 0:
                logger.info("Добавляю тестовые данные...")
                
                # Тестовые товары
                test_products = [
                    {
                        "id": 1,
                        "name": "Смартфон Apple iPhone 14 Pro Max",
                        "category": "Смартфоны",
                        "price": 650000.0,
                        "rating": 4.8,
                        "reviews": 1250,
                        "url": "https://kaspi.kz/shop/p/apple-iphone-14-pro-max-256gb-fioletovyi-106363342/"
                    },
                    {
                        "id": 2,
                        "name": "Ноутбук Apple MacBook Pro 16",
                        "category": "Ноутбуки",
                        "price": 1250000.0,
                        "rating": 4.9,
                        "reviews": 840,
                        "url": "https://kaspi.kz/shop/p/apple-macbook-pro-16-mk183-seryi-102892005/"
                    },
                    {
                        "id": 3,
                        "name": "Наушники Apple AirPods Pro 2",
                        "category": "Наушники",
                        "price": 145000.0,
                        "rating": 4.7,
                        "reviews": 3120,
                        "url": "https://kaspi.kz/shop/p/apple-airpods-pro-2nd-generation-belyi-106662968/"
                    },
                    {
                        "id": 4,
                        "name": "Смарт-часы Apple Watch Series 8",
                        "category": "Смарт-часы",
                        "price": 280000.0,
                        "rating": 4.6,
                        "reviews": 1560,
                        "url": "https://kaspi.kz/shop/p/apple-watch-series-8-45-mm-aluminium-chernyi-106585020/"
                    },
                    {
                        "id": 5,
                        "name": "Планшет Apple iPad Air 5",
                        "category": "Планшеты",
                        "price": 420000.0,
                        "rating": 4.8,
                        "reviews": 920,
                        "url": "https://kaspi.kz/shop/p/apple-ipad-air-5-2022-wi-fi-10-9-64-gb-seryi-104235453/"
                    }
                ]
                
                # Добавляем товары
                for product in test_products:
                    conn.execute(
                        "INSERT OR IGNORE INTO products (id, name, category, price, rating, reviews, url) "
                        "VALUES (:id, :name, :category, :price, :rating, :reviews, :url)",
                        product
                    )
                
                # Добавляем историю цен для тестовых товаров
                import random
                from datetime import datetime, timedelta
                
                for product_id in range(1, 6):
                    base_price = random.uniform(100000, 1500000)
                    for days_ago in range(30, 0, -2):
                        price_date = datetime.utcnow() - timedelta(days=days_ago)
                        price_change = random.uniform(-0.1, 0.1)  # ±10%
                        current_price = base_price * (1 + price_change)
                        
                        conn.execute(
                            "INSERT INTO price_history (product_id, price, timestamp) "
                            "VALUES (:product_id, :price, :timestamp)",
                            {
                                "product_id": product_id,
                                "price": round(current_price, 2),
                                "timestamp": price_date
                            }
                        )
                
                logger.info(f"✅ Добавлено {len(test_products)} тестовых товаров с историей цен")
        
        logger.info("✅ База данных инициализирована успешно")
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Ошибка SQL при инициализации базы данных: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка при инициализации базы данных: {e}")
        raise

# Автоматическая инициализация при импорте
if __name__ != "__main__":
    init_db()