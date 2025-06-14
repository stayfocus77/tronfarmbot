import os
import sqlite3
import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- Configuration ---
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))
ACTIVATION_FEE = 20
BONUS_WELCOME = 5
MIN_WITHDRAWAL = 100
WITHDRAW_FEE = 10
INVESTMENT_RETURN = 1.27

TRON_ADDRESS = "TWjPQeufhqoERTCm3yc4GcL78zCj4kgtvV"

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
    activation_date TEXT,
    bonus_20_given INTEGER DEFAULT 0
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

    keyboard = [
        ["💰 Investir", "📊 Mon solde"],
        ["🔓 Activer mon compte", "💸 Retirer mes gains"],
        ["📈 Tableau de bord", "👥 Mon affiliation"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "💎 Bienvenue sur TronFarmBot !\n\n"
        "🚀 Investissez vos TRX et récoltez des profits jusqu’à +27% par mois 📈\n"
        "🎁 Bonus de bienvenue de 5 TRX offert 🎉\n"
        "🔒 Simple, rapide, 100% automatisé via la blockchain TRON 🔗\n\n"
        "🌟 Commencez aujourd’hui et faites travailler votre crypto pour vous ! 🚀",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if text == "🔓 Activer mon compte":
        await update.message.reply_text(
            f"🔐 Pour activer votre compte, veuillez envoyer {ACTIVATION_FEE} TRX à l'adresse suivante :\n\n"
            f"{TRON_ADDRESS}\n\n"
            "Une fois le paiement effectué, votre compte sera activé sous 24h."
        )

    elif text == "💰 Investir":
        c.execute("SELECT activation_paid FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
        if not user or not user[0]:
            await update.message.reply_text("⚠ Vous devez d'abord activer votre compte avant d'investir.")
            return
        await update.message.reply_text("Veuillez utiliser la commande /invest montant pour investir.")

    elif text == "📊 Mon solde":
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
        if user:
            await update.message.reply_text(f"Votre solde est de {user[0]} TRX.")
        else:
            await update.message.reply_text("Veuillez d'abord vous inscrire avec /start")

    elif text == "💸 Retirer mes gains":
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

    elif text == "📈 Tableau de bord":
        c.execute("SELECT balance, invested, activation_date FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
        if user:
            balance, invested, activation_date = user
            await update.message.reply_text(
                f"📈 Tableau de bord :\n\n"
                f"- Total investi : {invested} TRX\n"
                f"- Solde actuel : {balance} TRX\n"
                f"- Date d'activation : {activation_date if activation_date else 'Non activé'}"
            )
        else:
            await update.message.reply_text("Aucune information trouvée.")

    elif text == "👥 Mon affiliation":
        c.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
        total_referrals = c.fetchone()[0]

        await update.message.reply_text(
            f"👥 Vous avez {total_referrals} filleuls actifs."
        )

async d


