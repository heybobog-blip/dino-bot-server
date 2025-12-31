import threading
import os
import requests # ใช้ตัวนี้ยิงคะแนนแทน (เสถียรกว่า)
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==========================================
# ข้อมูลบอทของคุณ
TOKEN = '8502834547:AAGJnG32qidGishilavggZgjAaHRikB67gU'
GAME_SHORT_NAME = 'zeinju_dino_run'
GAME_URL = 'https://heybobog-blip.github.io/telegram-dino-game/'
# ==========================================

# ตั้งค่า Web Server
app = Flask(__name__)
CORS(app)

# ปิด Log รกๆ
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    return "Bot & Server is Running! (Direct API Version)"

@app.route('/submit_score', methods=['GET'])
def submit_score():
    user_id = request.args.get('id')
    score = request.args.get('score')
    chat_id = request.args.get('chat_id')
    message_id = request.args.get('message_id')
    
    if not user_id or not score:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    try:
        # ใช้วิธียิง API ของ Telegram โดยตรง (แก้ปัญหา Event loop closed ถาวร)
        api_url = f"https://api.telegram.org/bot{TOKEN}/setGameScore"
        params = {
            'user_id': user_id,
            'score': score,
            'force': True
        }
        # ถ้ามี chat_id ให้ส่งไปด้วย
        if chat_id: params['chat_id'] = chat_id
        if message_id: params['message_id'] = message_id
            
        # ยิงข้อมูลไปหา Telegram
        resp = requests.get(api_url, params=params)
        
        if resp.status_code == 200:
            print(f"✅ Score Saved: User={user_id} Score={score}")
            return jsonify({"status": "success", "message": "Score Updated!"}), 200
        else:
            print(f"⚠️ Telegram Error: {resp.text}")
            return jsonify({"status": "error", "message": "Telegram refused"}), 500

    except Exception as e:
        print(f"❌ Server Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ส่วนของบอท (เอาไว้ส่งปุ่มเกม) ---
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_game(GAME_SHORT_NAME)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.game_short_name != GAME_SHORT_NAME:
        await query.answer("ผิดเกมครับ!", show_alert=True)
        return

    msg = query.message
    # แนบข้อมูล chat_id ไปด้วย
    final_url = f"{GAME_URL}?id={query.from_user.id}&chat_id={msg.chat.id}&message_id={msg.message_id}"
    await query.answer(url=final_url)

def run_telegram_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("game", start_game))
    application.add_handler(CallbackQueryHandler(button_callback))
    print("🤖 Bot polling started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # รันบอทใน Thread แยก
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # รัน Web Server
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
