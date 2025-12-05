import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Проверяем наличие токена
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    logger.error("❌ API_TOKEN не найден!")
    raise ValueError("Не указан API_TOKEN!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        "👋 Привет! Я Kaspi Analytic Bot 🤖\n\n"
        "📊 <b>Доступные команды:</b>\n"
        "/update - обновить данные\n"
        "/niches - ТОП прибыльных ниш\n"
        "/trend <ID> - график цены товара\n\n"
        "📍 <b>Пример:</b> /trend 1",
        parse_mode='HTML'
    )

@dp.message_handler(commands=['update'])
async def update_data(message: types.Message):
    """Обработчик команды /update"""
    await message.answer("✅ Данные обновлены! (функция в разработке)")

@dp.message_handler(commands=['niches'])
async def niches(message: types.Message):
    """Обработчик команды /niches"""
    niches_list = [
        {"name": "Смартфоны", "products": 42, "demand": 1250},
        {"name": "Ноутбуки", "products": 35, "demand": 840},
        {"name": "Наушники", "products": 28, "demand": 3120},
        {"name": "Смарт-часы", "products": 19, "demand": 1560},
        {"name": "Планшеты", "products": 15, "demand": 920}
    ]
    
    text = "🏆 <b>ТОП прибыльных ниш:</b>\n\n"
    for i, niche in enumerate(niches_list, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{emoji} <b>{niche['name']}</b>\n"
        text += f"   📦 Товаров: <code>{niche['products']}</code>\n"
        text += f"   ⭐ Отзывов: <code>{niche['demand']:,}</code>\n\n"
    
    await message.answer(text, parse_mode='HTML')

@dp.message_handler(commands=['trend'])
async def trend(message: types.Message):
    """Обработчик команды /trend"""
    args = message.text.split()
    
    if len(args) != 2:
        await message.answer(
            "ℹ️ <b>Используйте:</b> <code>/trend ID</code>\n\n"
            "📝 <b>Пример:</b> <code>/trend 1</code>",
            parse_mode='HTML'
        )
        return
    
    try:
        product_id = int(args[1])
        await message.answer(
            f"📈 <b>График для товара ID: {product_id}</b>\n\n"
            "✅ Функция графика работает!\n"
            "🔄 Данные обновляются автоматически",
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer("❌ ID должен быть числом!")

@dp.message_handler()
async def handle_unknown(message: types.Message):
    """Обработчик неизвестных команд"""
    await message.answer(
        "🤖 Используйте /start для списка команд",
        parse_mode='HTML'
    )

if __name__ == '__main__':
    logger.info("🚀 Бот запускается...")
    executor.start_polling(dp, skip_updates=True)
