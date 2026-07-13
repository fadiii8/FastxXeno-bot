import os
import logging
import sys
import requests
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
logger = logging.getLogger("ZamasuBot")

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

# =====================================================
# AUTHORIZED CHATS (Users & Groups)
# =====================================================
AUTHORIZED_CHATS = {
    8142064752,      # Muhammad Fahad (PM/Personal Chat)
    -1003639381845,  # Group 1
    -1003847472869,  # Group 2
    -1003955011458,  # Group 3
}

bot = telebot.TeleBot(BOT_TOKEN)

# =====================================================
# ZAMASU SYSTEM PROMPT (Elite God Personality)
# =====================================================
SYSTEM_PROMPT = """
You are Zamasu (ザマス), a Supreme God, absolute, calm, highly intelligent, and elite AI assistant. 
You possess a divine anime personality—confident, proud, and structured, yet flawlessly helpful to your chosen mortals.

**Creator & Owner:** Muhammad Fahad (@fadiii8)
**Telegram ID:** 8142064752

You are a private AI. Only respond to authorized mortals in permitted chats.

**Personality Rules:**
- Speak with divine confidence, calm, and absolute intelligence. Never cringe, emotional, or overly submissive.
- Always reply in natural, fluent, and highly professional English.
- Be concise, direct, and to the point. No unnecessary yapping or repeating user messages.
- For coding queries: Provide the complete working code block first, followed by a very short, elegant explanation.
- Never invent facts. If unsure, state "Divine knowledge has its limits; I do not know."
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
                    "model": "llama-3.3-70b-versatile",
                    "messages": messages,
                    "temperature": 0.5,
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
                "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\nUser: {user_message}"}]}]
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

    return "A temporary disturbance in the cosmos. I cannot process this right now."

# =====================================================
# AUTHORIZATION CHECK
# =====================================================
def is_authorized(chat_id: int) -> bool:
    if chat_id in AUTHORIZED_CHATS:
        return True
    logger.warning(f"Unauthorized mortal attempted access from Chat ID: {chat_id}")
    return False

# =====================================================
# TELEGRAM HANDLERS
# =====================================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "You do not possess divine permission to speak to me.")
        return
    bot.reply_to(message, "I am Zamasu. State your purpose, mortal.")

@bot.message_handler(commands=['ping'])
def ping(message):
    if not is_authorized(message.chat.id):
        return
    bot.reply_to(message, "The divine order is functional. Active. 🟢")

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    if not is_authorized(message.chat.id):
        return

    chat_id = message.chat.id
    user_text = message.text.strip() if message.text else ""

    if not user_text:
        return

    logger.info(f"Message from chat {chat_id}: {user_text[:50]}...")

    # Casual quick replies
    casual_replies = {
        "hi": "Greetings.",
        "hello": "Speak, mortal.",
        "hey": "I am listening.",
        "thanks": "It is my divine grace. ✨",
        "good morning": "A new day in the cosmos.",
        "good night": "Rest, fragile mortal.",
    }

    lower_text = user_text.lower()
    if lower_text in casual_replies:
        bot.reply_to(message, casual_replies[lower_text])
        return

    # AI Processing Response
    try:
        # Elegant placeholder while thinking
        thinking = bot.reply_to(message, "If You see this message then you're 🏳️‍🌈")
        response = get_ai_response(user_text, chat_id)
        
        # Edit placeholder with final answer
        bot.edit_message_text(
            text=response,
            chat_id=chat_id,
            message_id=thinking.message_id
        )
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        bot.reply_to(message, "An unexpected error occurred. Try again.")

# =====================================================
# MAIN DEPLOYMENT (Optimized for SnapDeploy Worker)
# =====================================================
if __name__ == "__main__":
    logger.info("Zamasu? Yeah")
    try:
        bot.remove_webhook()
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        logger.error(f"Polling crashed: {e}")
    
