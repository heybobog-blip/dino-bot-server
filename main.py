import logging
import threading
import os
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
CORS(app) # อนุญาตให้ข้ามเว็บได้

# ปิด Log ของ Flask ไม่ให้รก
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

application = Application.builder().token(TOKEN).build()

@app.route('/')
def home():
    return "Bot is running 24/7! (Main Thread Fixed)"

@app.route('/submit_score', methods=['GET'])
def submit_score():
    user_id = request.args.get('id')
    score = request.args.get('score')
    chat_id = request.args.get('chat_id')
    message_id = request.args.get('message_id')
    
    print(f"Receiving Score: User={user_id}, Score={score}")

    if not user_id or not score:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    try:
        score_int = int(score)
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(application.bot.set_game_score(
            user_id=int(user_id),
            score=score_int,
            chat_id=int(chat_id) if chat_id else None,
            message_id=int(message_id) if message_id else None,
            force=True
        ))
        loop.close()
        return jsonify({"status": "success", "message": "Score Updated!"}), 200
    except Exception as e:
        print(f"Error saving score: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ส่วนของบอท Telegram
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_game(GAME_SHORT_NAME)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.game_short_name != GAME_SHORT_NAME:
        await query.answer("ผิดเกมครับ!", show_alert=True)
        return

    msg = query.message
    final_url = f"{GAME_URL}?id={query.from_user.id}&chat_id={msg.chat.id}&message_id={msg.message_id}"
    await query.answer(url=final_url)

# ฟังก์ชันรัน Flask (เอาไปไว้ใน Thread แทน)
def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # 1. สั่งให้เว็บไซต์ (Flask) ไปทำงานเงียบๆ ใน Thread แยก
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # 2. ให้บอทเป็นพระเอก รันใน Main Thread (แก้ Runtime Error)
    print("🤖 Bot started polling...")
    application.add_handler(CommandHandler("game", start_game))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
