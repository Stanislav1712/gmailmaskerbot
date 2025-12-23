import logging
import uuid
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    InlineQueryHandler,
)

# ================== НАСТРОЙКИ ==================
TOKEN = "8525810024:AAG7WQ6OZszZ9gyXc2bg_QuxJefNGQBWciU"
ADMIN_ID = 123456789        # ← ВСТАВЬ СВОЙ TELEGRAM ID
FREE_LIMIT = 10

# ================== ЛОГИ ==================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ================== ХРАНИЛИЩА ==================
user_choices = {}
user_count = {}
last_username = {}
last_aliases = {}
user_usage = {}
paid_users = set()

# ================== /start ==================
def start(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    user_choices[uid] = {"dot": False, "plus": False}
    user_count[uid] = 1
    user_usage.setdefault(uid, 0)

    update.message.reply_text(
        "👋 GmailMaskerBot\n\n"
        "✔ Генерация Gmail псевдонимов\n"
        "✔ Inline режим\n"
        "✔ Premium\n\n"
        "Выбери настройки:",
        reply_markup=options_keyboard(uid),
    )

# ================== КЛАВИАТУРЫ ==================
def options_keyboard(uid):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"{'✅' if user_choices[uid]['dot'] else '⬜'} Точка",
                callback_data="dot"
            ),
            InlineKeyboardButton(
                f"{'✅' if user_choices[uid]['plus'] else '⬜'} Плюс",
                callback_data="plus"
            ),
        ],
        [
            InlineKeyboardButton(
                f"📦 Количество: {user_count[uid]}",
                callback_data="count"
            )
        ],
        [
            InlineKeyboardButton("🔁 Ещё", callback_data="regen"),
            InlineKeyboardButton("📋 Копировать", callback_data="copy"),
        ],
        [
            InlineKeyboardButton("💎 Premium", callback_data="premium")
        ]
    ])

def count_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1", callback_data="count_1"),
            InlineKeyboardButton("5", callback_data="count_5"),
            InlineKeyboardButton("10", callback_data="count_10"),
        ],
        [InlineKeyboardButton("⬅ Назад", callback_data="back")]
    ])

# ================== КНОПКИ ==================
def button(update: Update, context: CallbackContext):
    q = update.callback_query
    q.answer()
    uid = q.from_user.id
    d = q.data

    if d in ("dot", "plus"):
        user_choices[uid][d] = not user_choices[uid][d]
        q.edit_message_reply_markup(reply_markup=options_keyboard(uid))

    elif d == "count":
        q.edit_message_text("Выбери количество:", reply_markup=count_keyboard())

    elif d.startswith("count_"):
        user_count[uid] = int(d.split("_")[1])
        q.edit_message_text("Настройки обновлены", reply_markup=options_keyboard(uid))

    elif d == "regen":
        if uid not in last_username:
            q.edit_message_text("❌ Сначала отправь Gmail")
            return
        send_aliases(q, uid)

    elif d == "copy":
        if uid in last_aliases:
            context.bot.send_message(uid, "📋\n" + "\n".join(last_aliases[uid]))

    elif d == "premium":
        q.edit_message_text(
            "💎 Premium\n\n"
            "✔ Без лимитов\n"
            "✔ Полный inline\n\n"
            "Свяжитесь с админом"
        )

# ================== ЛИМИТ ==================
def check_limit(uid):
    return uid in paid_users or user_usage.get(uid, 0) < FREE_LIMIT

# ================== ГЕНЕРАЦИЯ ==================
def generate_aliases(username, uid):
    aliases = []
    limit = user_count[uid]

    if user_choices[uid]["dot"]:
        for i in range(1, len(username)):
            aliases.append(f"{username[:i]}.{username[i:]}@gmail.com")
            if len(aliases) >= limit:
                return aliases

    if user_choices[uid]["plus"]:
        for tag in ["news", "shop", "work", "promo"]:
            aliases.append(f"{username}+{tag}@gmail.com")
            if len(aliases) >= limit:
                return aliases

    return aliases[:limit]

# ================== EMAIL ==================
def handle_email(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    text = update.message.text.lower().strip()

    if not check_limit(uid):
        update.message.reply_text("❌ Лимит исчерпан. Premium 💎")
        return

    if not text.endswith("@gmail.com"):
        update.message.reply_text("❌ Только @gmail.com")
        return

    last_username[uid] = text.split("@")[0]
    send_aliases(update.message, uid)

def send_aliases(target, uid):
    aliases = generate_aliases(last_username[uid], uid)
    last_aliases[uid] = aliases
    user_usage[uid] += 1

    target.reply_text(
        "✅ Результат:\n\n" + "\n".join(aliases),
        reply_markup=options_keyboard(uid),
    )

# ================== INLINE ==================
def inline_query(update: Update, context: CallbackContext):
    q = update.inline_query.query.lower().strip()
    results = []

    if q.endswith("@gmail.com"):
        username = q.split("@")[0]
        aliases = [f"{username}+inline@gmail.com"]

        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="Gmail alias",
                input_message_content=InputTextMessageContent("\n".join(aliases)),
            )
        )

    update.inline_query.answer(results, cache_time=1)

# ================== 👑 АДМИН-ПАНЕЛЬ ==================
def admin(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("⛔ Доступ запрещён")
        return

    update.message.reply_text(
        "👑 Админ-панель\n\n"
        f"👥 Пользователей: {len(user_usage)}\n"
        f"💎 Premium: {len(paid_users)}\n\n"
        "Команды:\n"
        "/addpremium ID\n"
        "/delpremium ID\n"
        "/stats"
    )

def add_premium(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    uid = int(context.args[0])
    paid_users.add(uid)
    update.message.reply_text(f"✅ Premium выдан {uid}")

def del_premium(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    uid = int(context.args[0])
    paid_users.discard(uid)
    update.message.reply_text(f"❌ Premium удалён {uid}")

def stats(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    update.message.reply_text(
        f"📊 Статистика\n\n"
        f"Пользователей: {len(user_usage)}\n"
        f"Premium: {len(paid_users)}"
    )

# ================== MAIN ==================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin))
    dp.add_handler(CommandHandler("addpremium", add_premium))
    dp.add_handler(CommandHandler("delpremium", del_premium))
    dp.add_handler(CommandHandler("stats", stats))

    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_email))
    dp.add_handler(InlineQueryHandler(inline_query))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
