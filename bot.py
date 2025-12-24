import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# ---------------- СОСТОЯНИЕ ----------------
user_choices = {}
user_count = {}

# ---------------- /start ----------------
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_choices[user_id] = {"dot": False, "plus": False}
    user_count[user_id] = 1

    update.message.reply_text(
        "Привет 👋\nВыбери способы генерации Gmail-псевдонимов:",
        reply_markup=options_keyboard(user_id),
    )

# ---------------- КЛАВИАТУРЫ ----------------
def options_keyboard(user_id):
    dot = user_choices[user_id]["dot"]
    plus = user_choices[user_id]["plus"]

    keyboard = [
        [
            InlineKeyboardButton(f"{'✅' if dot else '⬜'} Точка", callback_data="dot"),
            InlineKeyboardButton(f"{'✅' if plus else '⬜'} Плюс", callback_data="plus"),
        ],
        [
            InlineKeyboardButton("📦 Количество адресов", callback_data="count")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def count_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1", callback_data="count_1"),
            InlineKeyboardButton("5", callback_data="count_5"),
            InlineKeyboardButton("10", callback_data="count_10"),
        ],
        [
            InlineKeyboardButton("⬅ Назад", callback_data="back")
        ],
    ])

# ---------------- КНОПКИ ----------------
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "dot":
        user_choices[user_id]["dot"] = not user_choices[user_id]["dot"]
        query.edit_message_reply_markup(reply_markup=options_keyboard(user_id))

    elif data == "plus":
        user_choices[user_id]["plus"] = not user_choices[user_id]["plus"]
        query.edit_message_reply_markup(reply_markup=options_keyboard(user_id))

    elif data == "count":
        query.edit_message_text("Выбери количество адресов:", reply_markup=count_keyboard())

    elif data.startswith("count_"):
        user_count[user_id] = int(data.split("_")[1])
        query.edit_message_text(
            f"Количество: {user_count[user_id]}\n\n"
            "Теперь отправь Gmail-адрес (example@gmail.com)"
        )

    elif data == "back":
        query.edit_message_text(
            "Выбери способы генерации Gmail-псевдонимов:",
            reply_markup=options_keyboard(user_id),
        )

# ---------------- ГЕНЕРАЦИЯ ----------------
def generate_aliases(username, user_id):
    aliases = []
    limit = user_count.get(user_id, 1)

    if user_choices[user_id]["dot"]:
        for i in range(1, len(username)):
            aliases.append(f"{username[:i]}.{username[i:]}@gmail.com")
            if len(aliases) >= limit:
                return aliases

    if user_choices[user_id]["plus"]:
        tags = ["news", "shop", "work", "promo", "social"]
        for tag in tags:
            aliases.append(f"{username}+{tag}@gmail.com")
            if len(aliases) >= limit:
                return aliases

    return aliases[:limit]

# ---------------- EMAIL ----------------
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
        update.message.reply_text("❌ Выберите хотя бы одну опцию")
        return

    update.message.reply_text("✅ Сгенерировано:\n\n" + "\n".join(aliases))

# ---------------- MAIN ----------------
def main():
    TOKEN = os.getenv("BOT_TOKEN")

    if not TOKEN:
        raise RuntimeError("❌ BOT_TOKEN не задан")

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_email))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
