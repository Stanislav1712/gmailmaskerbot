import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)

# ---------------- ЛОГИ ----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------- СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЯ ----------------
user_choices = {}   # {user_id: {"dot": bool, "plus": bool}}
user_count = {}     # {user_id: int}

# ---------------- REPLY КНОПКА СТАРТ ----------------
def start_keyboard():
    keyboard = [["🚀 Старт"]]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

# ---------------- INLINE КЛАВИАТУРЫ ----------------
def options_keyboard(user_id):
    dot = user_choices[user_id]["dot"]
    plus = user_choices[user_id]["plus"]

    keyboard = [
        [
            InlineKeyboardButton(
                f"{'✅' if dot else '⬜'} Точка", callback_data="dot"
            ),
            InlineKeyboardButton(
                f"{'✅' if plus else '⬜'} Плюс", callback_data="plus"
            ),
        ],
        [
            InlineKeyboardButton(
                f"📦 Количество: {user_count[user_id]}",
                callback_data="count"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def count_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data="count_1"),
            InlineKeyboardButton("5", callback_data="count_5"),
            InlineKeyboardButton("10", callback_data="count_10"),
        ],
        [
            InlineKeyboardButton("⬅ Назад", callback_data="back")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------------- /start ----------------
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    user_choices[user_id] = {"dot": False, "plus": False}
    user_count[user_id] = 1

    update.message.reply_text(
        "Привет 👋\nНажми «🚀 Старт», чтобы начать",
        reply_markup=start_keyboard()
    )

# ---------------- НАЖАТИЕ 🚀 СТАРТ ----------------
def start_button(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    user_choices[user_id] = {"dot": False, "plus": False}
    user_count[user_id] = 1

    update.message.reply_text(
        "Выбери способы генерации Gmail-псевдонимов:",
        reply_markup=options_keyboard(user_id)
    )

# ---------------- ОБРАБОТКА INLINE КНОПОК ----------------
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "dot":
        user_choices[user_id]["dot"] = not user_choices[user_id]["dot"]
        query.edit_message_reply_markup(
            reply_markup=options_keyboard(user_id)
        )

    elif data == "plus":
        user_choices[user_id]["plus"] = not user_choices[user_id]["plus"]
        query.edit_message_reply_markup(
            reply_markup=options_keyboard(user_id)
        )

    elif data == "count":
        query.edit_message_text(
            "Выбери количество адресов:",
            reply_markup=count_keyboard()
        )

    elif data.startswith("count_"):
        user_count[user_id] = int(data.split("_")[1])
        query.edit_message_text(
            "Выбери способы генерации Gmail-псевдонимов:",
            reply_markup=options_keyboard(user_id)
        )

    elif data == "back":
        query.edit_message_text(
            "Выбери способы генерации Gmail-псевдонимов:",
            reply_markup=options_keyboard(user_id)
        )

# ---------------- ГЕНЕРАЦИЯ АЛИАСОВ ----------------
def generate_aliases(username, user_id):
    aliases = []
    limit = user_count.get(user_id, 1)

    if user_choices[user_id]["dot"]:
        for i in range(1, len(username)):
            aliases.append(f"{username[:i]}.{username[i:]}@gmail.com")
            if len(aliases) >= limit:
                return aliases

    if user_choices[user_id]["plus"]:
        tags = ["news", "shop", "work", "social", "promo"]
        for tag in tags:
            aliases.append(f"{username}+{tag}@gmail.com")
            if len(aliases) >= limit:
                return aliases

    return aliases[:limit]

# ---------------- ОБРАБОТКА EMAIL ----------------
def handle_email(update: Update, context: CallbackContext):
    text = update.message.text.strip().lower()

    if "@" not in text:
        update.message.reply_text("❌ Введите корректный Gmail")
        return

    username, domain = text.split("@", 1)

    if domain != "gmail.com":
        update.message.reply_text("❌ Только @gmail.com")
        return

    user_id = update.message.from_user.id
    aliases = generate_aliases(username, user_id)

    if not aliases:
        update.message.reply_text("❌ Выберите опции")
        return

    update.message.reply_text(
        "✅ Сгенерированные адреса:\n\n" + "\n".join(aliases)
    )

# ---------------- MAIN ----------------
def main():
    TOKEN = "8525810024:AAG7WQ6OZszZ9gyXc2bg_QuxJefNGQBWciU"

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.regex("^🚀 Старт$"), start_button))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_email))

    updater.start_polling()
    updater.idle()

# ---------------- START ----------------
if __name__ == "__main__":
    main()
