import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('8903269443:AAE0EdALLu6fa-jk3H0tMi8u2s1xFQdy-oU')

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ответ на /start"""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("📊 О нас", callback_data='about')],
        [InlineKeyboardButton("🎮 Игры", callback_data='games'),
         InlineKeyboardButton("📞 Контакты", callback_data='contacts')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
        f"Я тестовый бот. Вот что я умею:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ответ на /help"""
    await update.message.reply_text(
        "📖 Доступные команды:\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/info - Информация о боте\n"
        "Просто напиши мне любое сообщение!"
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ответ на /info"""
    await update.message.reply_text(
        "🤖 Бот создан на Python с библиотекой python-telegram-bot\n"
        "Версия: 1.0.0\n"
        "Хостинг: Render.com / Railway.app"
    )

# --- Обработка callback-запросов ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'about':
        await query.edit_message_text(
            "📊 О нас:\n"
            "Этот бот создан в качестве примера.\n"
            "Вы можете модифицировать его под свои задачи!"
        )
    elif query.data == 'games':
        keyboard = [
            [InlineKeyboardButton("🎲 Случайное число", callback_data='random')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🎮 Выберите игру:",
            reply_markup=reply_markup
        )
    elif query.data == 'contacts':
        await query.edit_message_text(
            "📞 Контакты:\n"
            "Email: example@example.com\n"
            "GitHub: github.com/your-username"
        )
    elif query.data == 'random':
        import random
        num = random.randint(1, 100)
        await query.edit_message_text(
            f"🎲 Ваше случайное число: {num}\n\n"
            "Нажмите /start для возврата в меню"
        )
    elif query.data == 'back':
        await start(update, context)

# --- Обработка текстовых сообщений ---
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Эхо-ответ на любое сообщение"""
    text = update.message.text
    await update.message.reply_text(
        f"📩 Вы написали: {text}\n\n"
        "Я простой эхо-бот. Используйте /start для меню."
    )

# --- Обработка ошибок ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")

# --- Запуск бота ---
def main():
    """Главная функция запуска"""
    # Создаём приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем команды
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('info', info))
    
    # Регистрируем callback-запросы
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Регистрируем обработчик сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запуск бота
    print("🚀 Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()