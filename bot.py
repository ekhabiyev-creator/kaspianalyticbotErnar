import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from analytics import get_top_niches, plot_price_trend
from scheduler import scheduler, update_all_categories
from dotenv import load_dotenv
from db import init_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Проверяем наличие токена
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    logger.error("❌ API_TOKEN не найден в переменных окружения!")
    logger.error("Добавьте API_TOKEN в файл .env или в настройки Render")
    raise ValueError("Не указан API_TOKEN!")

# Инициализация базы данных
init_db()

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    """Обработчик команды /start"""
    user_name = message.from_user.full_name
    await message.answer(
        f"👋 Привет, {user_name}!\n"
        f"Я Kaspi Analytic Bot 🤖\n\n"
        f"📊 <b>Доступные команды:</b>\n"
        f"/update - обновить данные с Kaspi\n"
        f"/niches - ТОП прибыльных ниш\n"
        f"/trend <ID> - график динамики цены товара\n\n"
        f"📍 <b>Пример:</b> /trend 1\n"
        f"🔄 <b>Автообновление:</b> каждые 6 часов",
        parse_mode='HTML'
    )
    logger.info(f"Пользователь {user_name} (ID: {message.from_user.id}) запустил бота")

@dp.message_handler(commands=['update'])
async def update_data(message: types.Message):
    """Обработчик команды /update"""
    user_id = message.from_user.id
    await message.answer("🔄 Запускаю обновление данных...")
    logger.info(f"Пользователь {user_id} запросил обновление данных")
    
    try:
        # Запускаем обновление асинхронно
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, update_all_categories)
        
        await message.answer(
            "✅ <b>Данные успешно обновлены!</b>\n\n"
            "📊 Теперь доступны:\n"
            "• Актуальные ТОП ниши (/niches)\n"
            "• Обновленные графики цен (/trend)\n"
            "• Новая информация о товарах",
            parse_mode='HTML'
        )
        logger.info(f"Данные обновлены по запросу пользователя {user_id}")
    except Exception as e:
        error_msg = f"❌ Ошибка при обновлении: {str(e)}"
        await message.answer(error_msg)
        logger.error(f"Ошибка обновления для пользователя {user_id}: {e}")

@dp.message_handler(commands=['niches'])
async def niches(message: types.Message):
    """Обработчик команды /niches"""
    try:
        await message.answer("📊 Ищу ТОП ниши...")
        top = get_top_niches(limit=10)
        
        if not top:
            await message.answer(
                "📭 <b>Нет данных о нишах</b>\n\n"
                "Сначала обновите данные командой:\n"
                "<code>/update</code>",
                parse_mode='HTML'
            )
            return
        
        text = "🏆 <b>ТОП прибыльных ниш:</b>\n\n"
        
        for i, niche in enumerate(top, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            products_emoji = "📦"
            reviews_emoji = "⭐"
            
            text += f"{emoji} <b>{niche['name']}</b>\n"
            text += f"   {products_emoji} Товаров: <code>{niche['products']}</code>\n"
            text += f"   {reviews_emoji} Отзывов: <code>{niche['demand']:,}</code>\n\n"
        
        text += "📈 <i>Для анализа конкретного товара используйте /trend ID</i>"
        
        await message.answer(text, parse_mode='HTML')
        logger.info(f"Показаны ниши для пользователя {message.from_user.id}")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        logger.error(f"Ошибка получения ниш: {e}")

@dp.message_handler(commands=['trend'])
async def trend(message: types.Message):
    """Обработчик команды /trend"""
    args = message.text.split()
    
    if len(args) != 2:
        await message.answer(
            "ℹ️ <b>Используйте правильный формат:</b>\n\n"
            "<code>/trend ID_товара</code>\n\n"
            "📝 <b>Примеры:</b>\n"
            "<code>/trend 1</code>\n"
            "<code>/trend 2</code>\n"
            "<code>/trend 3</code>\n\n"
            "🔧 <b>Доступные тестовые ID:</b> 1, 2, 3",
            parse_mode='HTML'
        )
        return
    
    try:
        product_id = int(args[1])
        user_id = message.from_user.id
        
        await message.answer(f"📈 Генерирую график для товара ID: <code>{product_id}</code>...", parse_mode='HTML')
        logger.info(f"Пользователь {user_id} запросил график для товара {product_id}")
        
        buf = plot_price_trend(product_id)
        
        if buf:
            await bot.send_photo(
                message.chat.id,
                buf,
                caption=(
                    f"📊 <b>График цены товара</b>\n"
                    f"🆔 ID: <code>{product_id}</code>\n\n"
                    f"📅 <i>Данные обновлены автоматически</i>\n"
                    f"🔄 Следующее обновление через 6 часов"
                ),
                parse_mode='HTML'
            )
            logger.info(f"График для товара {product_id} отправлен пользователю {user_id}")
        else:
            await message.answer(
                f"❌ <b>Нет данных для товара ID: {product_id}</b>\n\n"
                f"Попробуйте:\n"
                f"1. Обновить данные: <code>/update</code>\n"
                f"2. Проверить доступные ID: 1, 2, 3, 4, 5\n"
                f"3. Убедиться, что товар существует",
                parse_mode='HTML'
            )
            
    except ValueError:
        await message.answer(
            "❌ <b>ID должен быть числом!</b>\n\n"
            "Используйте: <code>/trend 1</code>",
            parse_mode='HTML'
        )
    except Exception as e:
        await message.answer(f"❌ <b>Ошибка:</b> {str(e)}", parse_mode='HTML')
        logger.error(f"Ошибка построения графика: {e}")

@dp.message_handler()
async def handle_unknown(message: types.Message):
    """Обработчик неизвестных команд"""
    await message.answer(
        "🤖 <b>Я не понимаю эту команду</b>\n\n"
        "Используйте /start для списка команд\n"
        "Или /help для подробной справки",
        parse_mode='HTML'
    )

def main():
    """Основная функция запуска бота"""
    try:
        # Запускаем планировщик если он еще не запущен
        if not scheduler.running:
            scheduler.start()
            logger.info("✅ Планировщик запущен")
        
        # Информация о запуске
        logger.info("=" * 50)
        logger.info("🚀 Запуск Kaspi Analytic Bot")
        logger.info(f"🤖 Токен: {'Установлен' if API_TOKEN else 'ОТСУТСТВУЕТ!'}")
        logger.info("=" * 50)
        
        # Запускаем бота
        executor.start_polling(dp, skip_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")
        raise

if __name__ == '__main__':
    main()