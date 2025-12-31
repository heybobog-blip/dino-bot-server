import threading
import os
import requests
import logging
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==========================================
# 🛑 ข้อมูลบอท
TOKEN = '8502834547:AAGJnG32qidGishilavggZgjAaHRikB67gU'
GAME_SHORT_NAME = 'zeinju_dino_run'  # ⚠️ ต้องตรงกับใน BotFather เป๊ะๆ
GAME_URL = 'https://heybobog-blip.github.io/telegram-dino-game/'
# ==========================================

# ตั้งค่า Web Server
app = Flask(__name__)
CORS(app)

# ลด Log รกๆ
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    return "Bot & Game Server is Running!"

@app.route('/submit_score', methods=['GET'])
def submit_score():
    user_id = request.args.get('id')
    score = request.args.get('score')
    chat_id = request.args.get('chat_id')
    message_id = request.args.get('message_id')
    
    if not user_id or not score:
        return jsonify({"status": "error", "msg": "Missing params"}), 400

    try:
        api_url = f"https://api.telegram.org/bot{TOKEN}/setGameScore"
        params = {'user_id': user_id, 'score': score, 'force': True}
        if chat_id: params['chat_id'] = chat_id
        if message_id: params['message_id'] = message_id
            
        # ยิง request ไป Telegram
        resp = requests.get(api_url, params=params)
        print(f"✅ Score Update: {score} | Telegram Resp: {resp.text}")
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"❌ Error submit_score: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ส่วนของบอท Telegram ---

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"👉 Command /game received from {update.effective_user.first_name}")
    # ส่งเกมออกไป
    try:
        await update.message.reply_game(GAME_SHORT_NAME)
    except Exception as e:
        print(f"❌ Error sending game: {e}")
        await update.message.reply_text(f"เกิดข้อผิดพลาด: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # Debug ดูว่าปุ่มส่งอะไรมา
    print(f"🔘 Button Clicked! Game Name: '{query.game_short_name}'")
    
    # เช็คว่าชื่อเกมตรงไหม
    if query.game_short_name != GAME_SHORT_NAME:
        print(f"❌ Mismatch: Code='{GAME_SHORT_NAME}' vs Button='{query.game_short_name}'")
        await query.answer(f"Error: Game name mismatch!", show_alert=True)
        return

    # สร้าง URL
    # ดึงค่า chat_id และ message_id แบบปลอดภัย
    c_id = query.message.chat.id if query.message else ""
    m_id = query.message.message_id if query.message else ""
    
    final_url = f"{GAME_URL}?id={query.from_user.id}&chat_id={c_id}&message_id={m_id}"
    print(f"🚀 Opening URL: {final_url}")
    
    # สั่งให้ Telegram เปิด Browser (จุดสำคัญที่ทำให้ยุบหรือไม่ยุบ)
    try:
        await query.answer(url=final_url)
    except Exception as e:
        print(f"❌ FAILED to open game url: {e}")
        # ถ้าเปิดไม่ได้ ให้แจ้งเตือน user
        try:
            await query.answer(text="ไม่สามารถเปิดเกมได้ กรุณาลองใหม่", show_alert=True)
        except:
            pass

# ฟังก์ชันรันบอท (แยก Thread)
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("game", start_game))
    app_bot.add_handler(CommandHandler("start", start_game))
    app_bot.add_handler(CallbackQueryHandler(button_callback))
    
    print("🤖 Bot Polling Started...")
    app_bot.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # รันบอทใน Thread แยก (Background)
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    
    # รัน Flask เป็น Main Thread (เพื่อให้ Render จับ Port ได้ถูกต้อง)
    port = int(os.environ.get('PORT', 10000))
    print(f"🌍 Web Server running on port {port}")
    app.run(host='0.0.0.0', port=port)
