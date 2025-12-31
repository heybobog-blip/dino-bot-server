import logging
import threading
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==========================================
# ข้อมูลบอทของคุณ
TOKEN = '8502834547:AAGJnG32qidGishilavggZgjAaHRikB67gU'
GAME_SHORT_NAME = 'zeinju_dino_run'
GAME_URL = 'https://heybobog-blip.github.io/telegram-dino-game/'
# ==========================================

# ส่วนของ Web Server (Flask) เพื่อให้ Render รู้ว่าบอททำงานอยู่ และไว้รับคะแนน
app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

@app.route('/')
def home():
    return "Bot is running 24/7!"

@app.route('/submit_score', methods=['GET'])
def submit_score():
    # รับค่าจากเกม
    user_id = request.args.get('id')
    score = request.args.get('score')
    chat_id = request.args.get('chat_id')
    message_id = request.args.get('message_id')
    
    if not user_id or not score:
        return "Missing data", 400

    try:
        # แปลงคะแนนเป็นตัวเลข
        score_int = int(score)
        
        # ส่งคะแนนเข้า Telegram High Score Board
        # (ต้องใช้เทคนิค async loop ใน thread แยก ซึ่งซับซ้อน แต่เราใช้วิธีเรียกผ่าน API ตรงๆ ได้)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # อัปเดตคะแนน
        loop.run_until_complete(application.bot.set_game_score(
            user_id=int(user_id),
            score=score_int,
            chat_id=int(chat_id) if chat_id else None,
            message_id=int(message_id) if message_id else None,
            inline_message_id=None,
            force=True
        ))
        loop.close()
        return "Score Updated!", 200
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}", 500

# ส่วนของบอท Telegram
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_game(GAME_SHORT_NAME)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.game_short_name != GAME_SHORT_NAME:
        await query.answer("ผิดเกมครับ!", show_alert=True)
        return

    # สร้างลิงก์เกมที่แนบข้อมูล Chat ID ไปด้วย เพื่อให้ส่งคะแนนกลับถูกที่
    # เราต้องแนบ chat_id และ message_id ของตัวเกมที่เด้งขึ้นมา
    msg = query.message
    final_url = f"{GAME_URL}?id={query.from_user.id}&chat_id={msg.chat.id}&message_id={msg.message_id}"
    
    await query.answer(url=final_url)

def run_telegram_bot():
    print("🤖 Bot started...")
    application.add_handler(CommandHandler("game", start_game))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling()

if __name__ == '__main__':
    # รันบอทในอีก Thread นึง
    t = threading.Thread(target=run_telegram_bot)
    t.start()
    
    # รัน Web Server ใน Thread หลัก
    print("🌍 Web Server started...")
    app.run(host='0.0.0.0', port=10000)