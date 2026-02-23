import logging
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Токен берётся из переменной окружения (настроим на Render)
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://ggddop.github.io/planner")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== МОТИВАЦИОННЫЕ ФРАЗЫ =====
MORNING_QUOTES = [
    "🌅 Доброе утро! Новый день — новые возможности. Что сегодня сделаешь для своего будущего?",
    "☀️ Утро! Помни: один маленький шаг сегодня — это огромный прыжок через год.",
    "🚀 С добрым утром! Самые успешные люди начинают день с планирования. Ты уже открыл планер?",
    "💪 Доброе утро, чемпион! Сегодня — идеальный день чтобы сделать то, что ты откладывал.",
    "⚡ Утро! Вчера ты мечтал о том, чем займёшься сегодня. Время действовать!",
    "🌟 Доброе утро! Каждый день это 86 400 секунд. Используй их с умом.",
    "🎯 Утро нового дня! Поставь одну главную задачу и сосредоточься на ней.",
]

EVENING_QUOTES = [
    "🌙 Добрый вечер! Как прошёл день? Отметь выполненные задачи в планере.",
    "✅ Вечер! Время подвести итоги дня. Даже маленький прогресс — это победа.",
    "🌆 Вечер наступил. Запланируй завтрашний день сейчас — утром скажешь себе спасибо.",
    "💫 Добрый вечер! Три вещи которые ты сделал сегодня — уже достижение. Записал их?",
    "🔥 Вечер! Ты справился с ещё одним днём. Завтра — ещё лучше.",
]

MOTIVATION_QUOTES = [
    "💡 Дисциплина — это выбор между тем чего хочешь сейчас и тем чего хочешь больше всего.",
    "🏆 Успех — это сумма небольших усилий повторяемых день за днём.",
    "⚡ Не жди идеального момента. Возьми момент и сделай его идеальным.",
    "🎯 Цель без плана — это просто желание. Твой планер превращает желания в реальность.",
    "🌱 Маленькие привычки создают большие результаты. Не пропускай ни дня.",
    "💪 Единственный человек которым ты должен быть лучше, чем вчера — это ты сам.",
    "🚀 Начни там где ты есть. Используй то что имеешь. Делай что можешь.",
    "🔥 Мотивация приводит тебя в движение. Привычка удерживает тебя на пути.",
    "⭐ Каждый эксперт когда-то был новичком. Каждый профессионал когда-то не умел.",
    "🌟 Твои цели не слишком большие. Твои привычки пока ещё слишком маленькие.",
]

# ===== КНОПКА ОТКРЫТИЯ ПЛАНЕРА =====
def get_planner_keyboard():
    keyboard = [[
        InlineKeyboardButton(
            "📱 Открыть Планер",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]]
    return InlineKeyboardMarkup(keyboard)

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📱 Открыть Планер", web_app=WebAppInfo(url=WEBAPP_URL))],
        [
            InlineKeyboardButton("💡 Мотивация", callback_data="motivation"),
            InlineKeyboardButton("📊 О боте", callback_data="about"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== КОМАНДЫ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "друг"

    text = (
        f"👋 Привет, {name}!\n\n"
        f"Я твой личный бот-планер. Помогаю не забывать о целях и мотивирую двигаться вперёд.\n\n"
        f"📱 *Что умею:*\n"
        f"• Открыть твой планер одной кнопкой\n"
        f"• Присылать утреннее и вечернее напоминание\n"
        f"• Делиться мотивационными цитатами\n\n"
        f"🚀 Нажми кнопку ниже чтобы открыть планер!"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def open_planner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📱 Открываю твой планер...",
        reply_markup=get_planner_keyboard()
    )

async def motivation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quote = random.choice(MOTIVATION_QUOTES)
    await update.message.reply_text(
        f"{quote}\n\n_Продолжай двигаться вперёд! 💪_",
        parse_mode="Markdown",
        reply_markup=get_planner_keyboard()
    )

async def remind_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Включить напоминания"""
    chat_id = update.effective_chat.id

    # Удаляем старые задачи если есть
    if "morning_job" in context.chat_data:
        context.chat_data["morning_job"].schedule_removal()
    if "evening_job" in context.chat_data:
        context.chat_data["evening_job"].schedule_removal()

    # Утреннее напоминание в 8:00
    morning_job = context.job_queue.run_daily(
        send_morning,
        time=datetime.strptime("08:00", "%H:%M").time(),
        chat_id=chat_id,
        name=f"morning_{chat_id}"
    )

    # Вечернее напоминание в 20:00
    evening_job = context.job_queue.run_daily(
        send_evening,
        time=datetime.strptime("20:00", "%H:%M").time(),
        chat_id=chat_id,
        name=f"evening_{chat_id}"
    )

    context.chat_data["morning_job"] = morning_job
    context.chat_data["evening_job"] = evening_job

    await update.message.reply_text(
        "✅ *Напоминания включены!*\n\n"
        "🌅 Утром в 8:00 — мотивация на день\n"
        "🌙 Вечером в 20:00 — подвести итоги\n\n"
        "Отключить: /remind\\_off",
        parse_mode="Markdown"
    )

async def remind_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    removed = False
    for job_key in ["morning_job", "evening_job"]:
        if job_key in context.chat_data:
            context.chat_data[job_key].schedule_removal()
            del context.chat_data[job_key]
            removed = True

    if removed:
        await update.message.reply_text("🔕 Напоминания отключены.")
    else:
        await update.message.reply_text("У тебя не было активных напоминаний.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 *Команды бота:*\n\n"
        "/start — приветствие и открыть планер\n"
        "/planner — открыть планер\n"
        "/motivation — случайная мотивационная цитата\n"
        "/remind\\_on — включить напоминания (8:00 и 20:00)\n"
        "/remind\\_off — отключить напоминания\n"
        "/help — это сообщение\n\n"
        "💡 Или просто напиши мне что-нибудь!"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_planner_keyboard())

# ===== АВТОМАТИЧЕСКИЕ СООБЩЕНИЯ =====
async def send_morning(context: ContextTypes.DEFAULT_TYPE):
    quote = random.choice(MORNING_QUOTES)
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=f"{quote}\n\n_Открой планер и задай главную цель дня!_",
        parse_mode="Markdown",
        reply_markup=get_planner_keyboard()
    )

async def send_evening(context: ContextTypes.DEFAULT_TYPE):
    quote = random.choice(EVENING_QUOTES)
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=f"{quote}\n\n_Зайди в планер и отметь что выполнено._",
        parse_mode="Markdown",
        reply_markup=get_planner_keyboard()
    )

# ===== CALLBACK КНОПКИ =====
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "motivation":
        quote = random.choice(MOTIVATION_QUOTES)
        await query.message.reply_text(
            f"{quote}\n\n_Вперёд к целям! 🚀_",
            parse_mode="Markdown",
            reply_markup=get_planner_keyboard()
        )
    elif query.data == "about":
        await query.message.reply_text(
            "📊 *О боте*\n\n"
            "Этот бот создан специально для тебя.\n\n"
            "Планер хранит:\n"
            "• Задачи на день, неделю, месяц и год\n"
            "• Трекер привычек\n"
            "• Арки долгосрочных целей\n"
            "• Список желаний\n"
            "• Систему уровней и XP\n\n"
            "Данные хранятся в облаке Telegram ☁️",
            parse_mode="Markdown",
            reply_markup=get_planner_keyboard()
        )

# ===== ОБЫЧНЫЕ СООБЩЕНИЯ =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if any(w in text for w in ["привет", "хай", "здравствуй", "добрый"]):
        user = update.effective_user.first_name or "друг"
        await update.message.reply_text(
            f"Привет, {user}! 👋 Рад тебя видеть!\nОткрыть планер?",
            reply_markup=get_planner_keyboard()
        )
    elif any(w in text for w in ["мотив", "вдохнов", "цитата"]):
        quote = random.choice(MOTIVATION_QUOTES)
        await update.message.reply_text(
            f"{quote}",
            parse_mode="Markdown",
            reply_markup=get_planner_keyboard()
        )
    elif any(w in text for w in ["план", "задач", "цел"]):
        await update.message.reply_text(
            "📱 Все твои задачи и цели — в планере!",
            reply_markup=get_planner_keyboard()
        )
    else:
        await update.message.reply_text(
            "Открой планер и продолжай двигаться к своим целям! 🚀",
            reply_markup=get_planner_keyboard()
        )

# ===== ЗАПУСК =====
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("planner", open_planner))
    app.add_handler(CommandHandler("motivation", motivation))
    app.add_handler(CommandHandler("remind_on", remind_on))
    app.add_handler(CommandHandler("remind_off", remind_off))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
