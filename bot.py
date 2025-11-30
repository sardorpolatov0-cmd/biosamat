import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TELEGRAM_TOKEN") or "8037037647:AAFCjEBuLj0bA55ffGWViQqNefpU2pV1_LA"
WEBAPP_URL = "https://your-vercel-url/index.html"
ADMIN_URL = "https://your-vercel-url/admin.html"

roles = ["Virus", "Bakteriya", "Zambrug‘", "Parazit boshliq", "Hujayra", "Hujayra", "Immunitet", "Limfotsit"]

game_state = {
    "players": {},  # user_id: {role, alive}
    "phase": "waiting",
    "votes": {},
    "logs": [],
    "day_count": 0
}

# =========================
# BOT FUNCTIONS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in game_state["players"]:
        game_state["players"][user.id] = {"role": None, "alive": True}
    keyboard = [
        [InlineKeyboardButton("O‘yin paneli", url=WEBAPP_URL)],
        [InlineKeyboardButton("Admin paneli", url=ADMIN_URL)]
    ]
    await update.message.reply_text(f"Salom {user.first_name}! Bot ishlayapti 😊",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Admin panel", url=ADMIN_URL)]]
    await update.message.reply_text("Admin panelga kirish uchun tugmani bosing:",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

def assign_roles():
    players = list(game_state["players"].keys())
    shuffled_roles = random.sample(roles, len(players))
    for i, pid in enumerate(players):
        game_state["players"][pid]["role"] = shuffled_roles[i]

# Tun fazasi (night), kun fazasi (day) va ovoz berish (vote) funksiyalarini qo‘shish mumkin
# Misol uchun placeholder:
async def start_night(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game_state["phase"] = "night"
    await update.message.reply_text("Tunda harakatlar amalga oshiriladi...")

async def start_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game_state["phase"] = "day"
    game_state["day_count"] += 1
    await update.message.reply_text(f"Kun boshlanmoqda! {game_state['day_count']}-kun")

async def vote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Ovoz berildi: {query.data}")

# =========================
# MAIN
# =========================
def main():
    assign_roles()
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("night", start_night))
    app.add_handler(CommandHandler("day", start_day))
    app.add_handler(CallbackQueryHandler(vote_callback, pattern=r'^vote_'))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
