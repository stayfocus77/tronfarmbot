import os
import sqlite3
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Configuration ---
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))
ACTIVATION_FEE = 20
BONUS_WELCOME = 5
REFERRAL_BONUS = 4
MIN_WITHDRAWAL = 100
WITHDRAW_FEE = 10
INVESTMENT_RETURN = 1.27

# --- Base de données ---
conn = sqlite3.connect("tronfarm.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referrer_id INTEGER,
    balance REAL DEFAULT 0,
    invested REAL DEFAULT 0,
    activation_paid INTEGER DEFAULT 0,
    activation_date TEXT
)
""")
conn.commit()

# --- Logique principale ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()

    if not user:
        referrer_id = int(args[0]) if args else None
        c.execute("INSERT INTO users (user_id, referrer_id, balance) VALUES (?, ?, ?)", (user_id, referrer_id, BONUS_WELCOME))
        conn.commit()
        await update.message.reply_text(
            "🚀 Bienvenue sur TronFarmBot !\n\n"
            "🎁 Vous recevez immédiatement 5 TRX de bonus de bienvenue.\n"
            "💼 Activez votre compte en versant 20 TRX pour accéder à nos investissements avec 27% de rendement mensuel.\n"
            "🤝 Invitez vos amis et gagnez 4 TRX pour chaque activation par parrainage.\n\n"
            "✅ Pour activer votre compte, veuillez envoyer 20 TRX comme indiqué.\n\n"
            "Nous vous souhaitons d’excellents profits avec TronFarmBot 🚀"
        )
    else:
        await update.message.reply_text("Vous êtes déjà inscrit sur TronFarmBot !")

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    c.execute("SELECT activation_paid FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()

    if user and user[0]:
        await update.message.reply_text("Votre compte est déjà activé.")
        return

    c.execute("UPDATE users SET activation_paid = 1, activation_date = ? WHERE user_id = ?", (str(datetime.date.today()), user_id))
    conn.commit()

    c.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
    ref = c.fetchone()[0]
    if ref:
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (REFERRAL_BONUS, ref))
        conn.commit()

    await update.message.reply_text("Activation réussie ! Vous pouvez maintenant investir.")

async def invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    c.execute("SELECT activation_paid FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()

    if not user or not user[0]:
        await update.message.reply_text("Vous devez d'abord activer votre compte.")
        return

    try:
        amount = float(context.args[0])
        profit = round(amount * INVESTMENT_RETURN, 2)
        c.execute("UPDATE users SET invested = invested + ?, balance = balance + ? WHERE user_id = ?", (amount, profit, user_id))
        conn.commit()
        await update.message.reply_text(f"Investissement de {amount} TRX enregistré. Vous recevrez {profit} TRX après 30 jours.")
    except:
        await update.message.reply_text("Utilisation : /invest montant")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()

    if user:
        await update.message.reply_text(f"Votre solde est de {user[0]} TRX.")
    else:
        await update.message.reply_text("Veuillez d'abord vous inscrire avec /start")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()

    if not user:
        await update.message.reply_text("Veuillez d'abord vous inscrire.")
        return

    balance = user[0]
    if balance < MIN_WITHDRAWAL:
        await update.message.reply_text(f"Montant insuffisant. Minimum de retrait: {MIN_WITHDRAWAL} TRX.")
        return

    withdraw_amount = balance - WITHDRAW_FEE
    c.execute("UPDATE users SET balance = 0 WHERE user_id = ?", (user_id,))
    conn.commit()

    await update.message.reply_text(f"Retrait de {withdraw_amount} TRX validé après déduction des frais de {WITHDRAW_FEE} TRX.")

# --- Lancement du bot Telegram avec Webhook ---

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("activate", activate))
app.add_handler(CommandHandler("invest", invest))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("withdraw", withdraw))

print("Bot en cours de fonctionnement avec Webhook...")

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path="webhook",
    webhook_url=WEBHOOK_URL
)
