import threading
import os
import requests
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==========================================
# 🛑 ข้อมูลบอท
TOKEN = '8502834547:AAGJnG32qidGishilavggZgjAaHRikB67gU'
GAME_SHORT_NAME = 'zeinju_dino_run'
GAME_URL = 'https://heybobog-blip.github.io/telegram-dino-game/'
# ==========================================

# ตั้งค่า Web Server
app = Flask(__name__)
CORS(app)

# ลด Log
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    return "Bot is Running! (Thread Fixed)"

@app.route('/submit_score', methods=['GET'])
def submit_score():
    user_id = request.args.get('id')
    score = request.args.get('score')
    chat_id = request.args.get('chat_id')
    message_id = request.args.get('message_id')
    
    if not user_id or not score:
        return jsonify({"status": "error"}), 400

    try:
        api_url = f"https://api.telegram.org/bot{TOKEN}/setGameScore"
        params = {'user_id': user_id, 'score': score, 'force': True}
        if chat_id: params['chat_id'] = chat_id
        if message_id: params['message_id'] = message_id
            
        requests.get(api_url, params=params)
        print(f"✅ Score Saved: {score}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error"}), 500

# --- ส่วนของบอท Telegram ---

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"👉 Command /game user: {update.effective_user.first_name}")
    await update.message.reply_game(GAME_SHORT_NAME)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    print(f"🔘 Button: {query.game_short_name}")
    
    if query.game_short_name != GAME_SHORT_NAME:
        await query.answer(f"Wrong Game! Expect: {GAME_SHORT_NAME}", show_alert=True)
        return

    c_id = query.message.chat.id if query.message else ""
    m_id = query.message.message_id if query.message else ""
    final_url = f"{GAME_URL}?id={query.from_user.id}&chat_id={c_id}&message_id={m_id}"
    
    try:
        await query.answer(url=final_url)
        print(f"🚀 Open URL: Success")
    except Exception as e:
        print(f"❌ Open URL Failed: {e}")
        await query.answer("Error opening game", show_alert=True)

# ฟังก์ชันรัน Flask (เอาไปไว้ Thread แยก)
def run_flask():
    port = int(os.environ.get('PORT', 10000))
    # ปิด debug mode เพื่อไม่ให้มันแย่ง main thread
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    # 1. สั่งรัน Web Server ใน Background Thread (เป็นตัวรอง)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # 2. สั่งรันบอทใน Main Thread (เป็นตัวหลัก - แก้ Error set_wakeup_fd)
    print("🤖 Bot Starting in Main Thread...")
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("game", start_game))
    app_bot.add_handler(CommandHandler("start", start_game))
    app_bot.add_handler(CallbackQueryHandler(button_callback))
    
    # คำสั่งนี้ต้องอยู่บรรทัดสุดท้ายของ main
    app_bot.run_polling(allowed_updates=Update.ALL_TYPES)
