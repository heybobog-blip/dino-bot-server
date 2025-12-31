import threading
import os
import logging
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==========================================
# 🛑 ข้อมูลบอท (ใส่ Token ใหม่ให้แล้วครับ)
TOKEN = '7721044180:AAGQ-HFdwfaG6QfZd9bkbo5ZRgSMflNDTW4' 
GAME_SHORT_NAME = 'zeinju_dino_run'
GAME_URL = 'https://heybobog-blip.github.io/telegram-dino-game/'
# ==========================================

# ตั้งค่า Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# --- ส่วนของ Web Server (Flask) ---
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "✅ Game Bot is Running!", 200

@app.route('/submit_score', methods=['GET'])
def submit_score():
    user_id = request.args.get('id')
    score = request.args.get('score')
    chat_id = request.args.get('chat_id')
    message_id = request.args.get('message_id')
    
    if not user_id or not score:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    import requests
    try:
        # ยิงคะแนนกลับไปที่ Telegram
        api_url = f"https://api.telegram.org/bot{TOKEN}/setGameScore"
        params = {'user_id': user_id, 'score': score, 'force': True}
        if chat_id: params['chat_id'] = chat_id
        if message_id: params['message_id'] = message_id
            
        resp = requests.get(api_url, params=params)
        logger.info(f"Score Saved: User={user_id} Score={score} Resp={resp.status_code}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error saving score: {e}")
        return jsonify({"status": "error"}), 500

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    try:
        # สำคัญ: ต้องเป็น debug=False, use_reloader=False เพื่อไม่ให้สร้าง thread ซ้อน
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Flask Error: {e}")

# --- ส่วนของบอท Telegram ---

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Command /game user: {update.effective_user.first_name}")
    try:
        await update.message.reply_game(GAME_SHORT_NAME)
    except Exception as e:
        await update.message.reply_text("⚠️ Error: เกมนี้ยังไม่ได้สร้างใน BotFather หรือชื่อผิด")
        logger.error(f"Game Error: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if query.game_short_name != GAME_SHORT_NAME:
        await query.answer(f"Wrong Game! Expect: {GAME_SHORT_NAME}", show_alert=True)
        return

    c_id = query.message.chat.id if query.message else ""
    m_id = query.message.message_id if query.message else ""
    final_url = f"{GAME_URL}?id={query.from_user.id}&chat_id={c_id}&message_id={m_id}"
    
    logger.info(f"Opening Game for {query.from_user.first_name}")
    await query.answer(url=final_url)

def main():
    # 1. รัน Web Server (Flask) ใน Thread รอง
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # 2. รัน Bot ใน Main Thread
    logger.info("🤖 New Bot Starting...")
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("game", start_game))
    application.add_handler(CommandHandler("start", start_game))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Fatal Error: {e}")
