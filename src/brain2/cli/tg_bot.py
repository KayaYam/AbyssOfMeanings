import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
from pathlib import Path
from .ask import run_ask  # Прямой импорт функции
try:
    from .folder_import import main as run_import
    from .extract import main as run_extract
    from .index import main as run_indexing
except ImportError as e:
    print(f"Ошибка импорта: {e}")

# Настройки
DIARY_DIR = Path("data/import/diary")
DIARY_DIR.mkdir(parents=True, exist_ok=True)
MENU_KEYBOARD = [
    ['📝 Дневник', '📊 Трекер'], 
    ['🧠 Рефлексия', '❓ Вопрос'],
    ['🔙 Главное меню'] # Кнопка выхода
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Эта функция должна быть ОПРЕДЕЛЕНА до того, как мы её вызываем внизу"""
    markup = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(
        "Второй мозг на связи. Выбери режим работы в меню внизу:", 
        reply_markup=markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # 1. Логика переключения режимов
    if user_text == '🔙 Главное меню':
        context.user_data['mode'] = '❓ Вопрос'
        await update.message.reply_text("Режим сброшен. Я готов к обычным вопросам.")
        return

    if user_text in ['📝 Дневник', '📊 Трекер', '🧠 Рефлексия', '❓ Вопрос']:
        context.user_data['mode'] = user_text
        await update.message.reply_text(f"Активирован режим: {user_text}. Жду твой текст!")
        return

    # 2. Получаем текущий режим
    mode = context.user_data.get('mode', '❓ Вопрос')

    if mode == '📝 Дневник':
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = DIARY_DIR / f"{timestamp}.txt"
        file_path.write_text(user_text, encoding="utf-8")
        
        status_msg = await update.message.reply_text("📥 Записываю в память...")
        
        try:
            # 1. Добавляем в базу данных
            run_import() 
            
            # 2. Индексация (extract НЕ НУЖЕН для txt)
            run_indexing()
            
            await status_msg.edit_text("✅ Готово! Твой 'Второй мозг' стал умнее.")
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка: {str(e)}")
        
        context.user_data['mode'] = '❓ Вопрос'
        return

    # 3. Логика анализа (Рефлексия или Вопрос)
    elif mode in ['🧠 Рефлексия', '❓ Вопрос']:
        msg = await update.message.reply_text("🚀 Работаю над ответом...")
        q_mode = "reflect" if mode == '🧠 Рефлексия' else "ask"
        
        # Прямой вызов функции из ask.py
        full_response = run_ask(user_text, mode=q_mode)
        
        # Тот самый "резак" текста
        MAX_LEN = 4000
        if len(full_response) > MAX_LEN:
            chunks = [full_response[i:i+MAX_LEN] for i in range(0, len(full_response), MAX_LEN)]
            await msg.edit_text(chunks[0])
            for chunk in chunks[1:]:
                await update.message.reply_text(chunk)
        else:
            await msg.edit_text(full_response)

if __name__ == "__main__":
    # НЕ ЗАБУДЬ СМЕНИТЬ ТОКЕН
    app = Application.builder().token("8297431808:AAErySszmaEu-WztWrqIEx3_Xn6xuhogAYM").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот готов к работе...")
    app.run_polling()