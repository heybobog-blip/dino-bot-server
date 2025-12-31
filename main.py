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
# 🛑 ตั้งค่า TOKEN และชื่อเกม (ต้องตรงเป๊ะ)
TOKEN = '8502834547:AAGJnG32qidGishilavggZgjAaHRikB67gU'
GAME_SHORT_NAME = 'zeinju_dino_run'  
GAME_URL = 'https://heybobog-blip.github.io/telegram-dino-game/'
# ==========================================

# ตั้งค่า Web Server
app = Flask(__name__)
CORS(app)

# ปิด Log สีแดงๆ ที่ไม่จำเป็น
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    return "Bot & Game Server is Running! (Fixed Version)"

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
        print(f"✅ บันทึกคะแนน: {score}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"❌ Error submit_score: {e}")
        return jsonify({"status": "error"}), 500

# --- ส่วนของบอท Telegram ---

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"👉 มีคำสั่งเล่นเกมจาก: {update.effective_user.first_name}")
    await update.message.reply_game(GAME_SHORT_NAME)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    print(f"🔘 กดปุ่มเกม: '{query.game_short_name}'")
    
    # 1. เช็คชื่อเกม
    if query.game_short_name != GAME_SHORT_NAME:
        await query.answer(f"ชื่อเกมผิด! ตั้งค่าเป็น {GAME_SHORT_NAME}", show_alert=True)
        return

    # 2. สร้างลิ้งก์ (ดึง chat_id แบบปลอดภัย)
    c_id = query.message.chat.id if query.message else ""
    m_id = query.message.message_id if query.message else ""
    final_url = f"{GAME_URL}?id={query.from_user.id}&chat_id={c_id}&message_id={m_id}"
    
    # 3. ส่งคำสั่งเปิดเกม (ใส่ try-except กันจอยุบ)
    try:
        print(f"🚀 กำลังเปิด: {final_url}")
        await query.answer(url=final_url)
    except Exception as e:
        print(f"❌ เปิดเกมไม่ได้ Error: {e}")
        await query.answer("เกิดข้อผิดพลาดในการเปิดเกม ลองใหม่อีกครั้ง", show_alert=True)

# รันบอท (แยก Thread เพื่อไม่ให้ตีกับ Web Server)
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("game", start_game))
    app_bot.add_handler(CommandHandler("start", start_game))
    app_bot.add_handler(CallbackQueryHandler(button_callback))
    
    print("🤖 Bot Ready (Polling)...")
    app_bot.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # สั่งรันบอทเป็น Background
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    
    # สั่งรัน Web Server เป็นตัวหลัก
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
