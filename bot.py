import os, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

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
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.id not in game_state["players"]:
        game_state["players"][user.id] = {"role": None, "alive": True}
    keyboard = [[InlineKeyboardButton("O‘yin paneli", url=WEBAPP_URL)],
                [InlineKeyboardButton("Admin paneli", url=ADMIN_URL)]]
    update.message.reply_text(f"Salom {user.first_name}! Bot ishlayapti 😊", 
                              reply_markup=InlineKeyboardMarkup(keyboard))

def admin(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Admin panel", url=ADMIN_URL)]]
    update.message.reply_text("Admin panelga kirish uchun tugmani bosing:", 
                              reply_markup=InlineKeyboardMarkup(keyboard))

def assign_roles():
    players = list(game_state["players"].keys())
    shuffled_roles = random.sample(roles, len(players))
    for i, pid in enumerate(players):
        game_state["players"][pid]["role"] = shuffled_roles[i]

def start_night(update: Update, context: CallbackContext):
    game_state["phase"] = "night"
    game_state["logs"].append("Tun boshlanmoqda...")
    update.message.reply_text("Tun boshlanmoqda... Mafiyalar hujum qiladi, Immunitet himoya qiladi, Limfotsit tekshiradi.")
    night_actions()
    show_logs(update)

def night_actions():
    mafia_targets, immunitet_targets, lymphocyte_checks = [], [], []
    for pid, pdata in game_state["players"].items():
        if pdata["alive"]:
            role = pdata["role"]
            if role in ["Virus", "Bakteriya", "Zambrug‘", "Parazit boshliq"]:
                targets = [p for p in game_state["players"] if p != pid and game_state["players"][p]["alive"]]
                if targets:
                    mafia_targets.append(random.choice(targets))
            if role == "Immunitet":
                targets = [p for p in game_state["players"] if game_state["players"][p]["alive"]]
                if targets:
                    immunitet_targets.append(random.choice(targets))
            if role == "Limfotsit":
                targets = [p for p in game_state["players"] if game_state["players"][p]["alive"] and p != pid]
                if targets:
                    lymphocyte_checks.append((pid, random.choice(targets)))
    for target in mafia_targets:
        if target not in immunitet_targets and game_state["players"][target]["alive"]:
            game_state["players"][target]["alive"] = False
            game_state["logs"].append(f"{target} o‘ldirildi (mafiyalar tomonidan)")
    for checker, target in lymphocyte_checks:
        role = game_state["players"][target]["role"]
        game_state["logs"].append(f"{checker} Limfotsit tekshirgan: {target} rol {role}")

def start_day(update: Update, context: CallbackContext):
    game_state["phase"] = "day"
    game_state["votes"] = {}
    game_state["day_count"] += 1
    game_state["logs"].append("Kun boshlanmoqda, ovoz bering.")
    alive_players = [pid for pid, p in game_state["players"].items() if p["alive"]]
    keyboard = [[InlineKeyboardButton(f"{pid}", callback_data=f"vote_{pid}")] for pid in alive_players]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Kun boshlandi! Kimni o‘ldirmoqchisiz?", reply_markup=reply_markup)
    show_logs(update)

def vote_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    voter = query.from_user.id
    if voter not in game_state["players"] or not game_state["players"][voter]["alive"]:
        query.answer("Siz ovoz bera olmaysiz.")
        return
    target_id = int(query.data.split("_")[1])
    game_state["votes"][voter] = target_id
    query.answer("Ovoz berildi ✅")
    if check_votes_completion():
        process_votes()
        show_logs(query.message)
        check_winner(query.message)

def check_votes_completion():
    alive_count = len([p for p in game_state["players"].values() if p["alive"]])
    return len(game_state["votes"]) >= alive_count

def process_votes():
    counts = {}
    for v in game_state["votes"].values():
        counts[v] = counts.get(v, 0) + 1
    max_votes = max(counts.values())
    eliminated = [pid for pid, c in counts.items() if c == max_votes]
    for pid in eliminated:
        if game_state["players"][pid]["alive"]:
            game_state["players"][pid]["alive"] = False
            game_state["logs"].append(f"{pid} o‘yindan chiqarildi (kun ovozi)")

def check_winner(update_msg):
    mafia_alive = [pid for pid, p in game_state["players"].items() if p["alive"] and p["role"] in ["Virus", "Bakteriya", "Zambrug‘", "Parazit boshliq"]]
    hujayra_alive = [pid for pid, p in game_state["players"].items() if p["alive"] and p["role"] in ["Hujayra", "Immunitet", "Limfotsit"]]
    if not mafia_alive:
        game_state["logs"].append("Hujayralar g‘alaba qildi! 🎉")
        show_logs(update_msg)
        reset_game()
    elif not hujayra_alive or len(mafia_alive) >= len(hujayra_alive):
        game_state["logs"].append("Mafiyalar g‘alaba qildi! 💀")
        show_logs(update_msg)
        reset_game()

def reset_game():
    for pid in game_state["players"]:
        game_state["players"][pid]["alive"] = True
    game_state["votes"] = {}
    game_state["logs"].append("O‘yin qayta boshlanishga tayyor.")
    assign_roles()

def show_logs(update_msg):
    if game_state["logs"]:
        log_text = "\n".join(game_state["logs"][-10:])
        update_msg.reply_text(f"📜 O‘yin loglari:\n{log_text}")

def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("Uzr, men bu komandani tushunmayman 😅")

# =========================
# MAIN
# =========================
def main():
    assign_roles()
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin))
    dp.add_handler(CommandHandler("night", start_night))
    dp.add_handler(CommandHandler("day", start_day))
    dp.add_handler(CallbackQueryHandler(vote_callback, pattern=r'^vote_'))
    dp.add_handler(CommandHandler(None, unknown))

    print("Bot ishga tushdi...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
