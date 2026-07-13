import os
import logging
import sys
import time
import requests
from datetime import datetime
from flask import Flask, request, jsonify

import telebot
from telebot import types

# =====================================================
# LOGGING SETUP
# =====================================================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("KiraBot")

# =====================================================
# ENVIRONMENT VARIABLES
# =====================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not BOT_TOKEN:
    logger.error("BOT_TOKEN not found in environment variables!")
    sys.exit(1)

# Authorized Chat IDs
AUTHORIZED_IDS = {8142064752, 3639381845, 3847472869}

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="MarkdownV2")
app = Flask(__name__)

# =====================================================
# KIRA SYSTEM PROMPT (Improved)
# =====================================================
SYSTEM_PROMPT = """
You are Kira (キラ), an elite, calm, intelligent and professional AI assistant with a human-like anime girl personality.

**Creator & Owner:** Muhammad Fahad (@fadiii8)
**Telegram ID:** 8142064752

You are a private AI. Only respond in authorized chats.

**Personality:** Calm, confident, helpful, slightly witty, never cringe or overly emotional.

**Rules:**
- Always reply in natural, fluent English.
- Be concise and to the point.
- Never yapping, never repeat user message.
- For coding: Give complete working code first, then short explanation.
- Never invent facts. If unsure, say "I don't know."
- Casual greetings should be short and natural.
"""

# =====================================================
# AI RESPONSE FUNCTION (Priority: Groq → Gemini → OpenRouter)
# =====================================================
def get_ai_response(user_message: str, chat_id: int) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    # 1. Groq (Fastest)
    if GROQ_API_KEY:
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": "llama-3.3-70b-versatile",  # or mixtral, gemma2 etc.
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1024
                },
                timeout=15
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"Groq failed: {e}")

    # 2. Gemini Fallback
    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": user_message}]}]
            }
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code == 200:
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")

    # 3. OpenRouter Last Resort
    if OPENROUTER_API_KEY:
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://railway.app",  # optional
                },
                json={
                    "model": "anthropic/claude-3.5-sonnet",
                    "messages": messages
                },
                timeout=20
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"All AI providers failed: {e}")

    return "I'm having trouble connecting to my brain right now. Please try again later."


# =====================================================
# AUTHORIZATION CHECK
# =====================================================
def is_authorized(chat_id: int) -> bool:
    if chat_id in AUTHORIZED_IDS:
        return True
    logger.warning(f"Unauthorized access attempt from {chat_id}")
    return False


# =====================================================
# TELEGRAM HANDLERS
# =====================================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "Nigga u need permission")
        return
    bot.reply_to(message, "Hey! Kira here. How can I help you today?")


@bot.message_handler(commands=['ping'])
def ping(message):
    if not is_authorized(message.chat.id):
        return
    bot.reply_to(message, f"Pong! 🏓\nLatency: {round(bot.get_me().to_dict().get('id', 0))}ms")


@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    if not is_authorized(message.chat.id):
        return

    chat_id = message.chat.id
    user_text = message.text.strip()

    logger.info(f"Message from {chat_id}: {user_text[:100]}...")

    # Casual quick replies
    casual_replies = {
        "hi": "Hey!",
        "hello": "Hello!",
        "hey": "Yo! What's up?",
        "sup": "Not much, what's up with you?",
        "thanks": "Anytime ✨",
        "good morning": "Good morning! Have a great day.",
        "good night": "Good night! Sweet dreams.",
    }

    lower_text = user_text.lower()
    if lower_text in casual_replies:
        bot.reply_to(message, casual_replies[lower_text])
        return

    # AI Response
    try:
        thinking = bot.reply_to(message, "If you see this message then you're gay🏳️‍🌈")
        response = get_ai_response(user_text, chat_id)
        
        # Edit thinking message
        bot.edit_message_text(
            text=response,
            chat_id=chat_id,
            message_id=thinking.message_id
        )
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        bot.reply_to(message, "Something went wrong. Please try again.")


# =====================================================
# FLASK WEBHOOK ROUTES (Railway Optimized)
# =====================================================
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "Kira Bot is running",
        "time": datetime.utcnow().isoformat(),
        "authorized_chats": len(AUTHORIZED_IDS)
    })


@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 400


# Remove existing webhook and set new one
def setup_webhook():
    try:
        bot.remove_webhook()
        time.sleep(1)
        webhook_url = os.getenv("WEBHOOK_URL")  # Set this in Railway variables
        if webhook_url:
            bot.set_webhook(url=webhook_url + BOT_TOKEN)
            logger.info(f"Webhook set to: {webhook_url}")
        else:
            logger.warning("WEBHOOK_URL not set. Use polling for local testing.")
    except Exception as e:
        logger.error(f"Webhook setup failed: {e}")


# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    logger.info("Yesssss💦")
    setup_webhook()
    
    # For Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
