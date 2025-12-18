#!/usr/bin/env python3
"""
CV Analysis Bot - Black-Ops AI Service
Telegram Bot لتحليل وتحسين السيرة الذاتية تلقائيًا
"""

import os
import logging
import asyncio
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PAYPAL_LINK = os.getenv("PAYPAL_LINK")
SERVICE_PRICE = os.getenv("SERVICE_PRICE", "3")

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI()

# Database setup
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            cv_text TEXT,
            paid INTEGER DEFAULT 0,
            created_at TEXT,
            paid_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_user_cv(user_id, username, cv_text):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO users (user_id, username, cv_text, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, cv_text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_user_cv(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT cv_text FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def mark_user_paid(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        UPDATE users SET paid = 1, paid_at = ? WHERE user_id = ?
    """, (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

# AI Analysis Function
async def analyze_cv_with_ai(cv_text: str) -> dict:
    """تحليل وتحسين السيرة الذاتية باستخدام AI"""
    
    analysis_prompt = f"""أنت خبير موارد بشرية محترف. حلل السيرة الذاتية التالية وقدم:

1. **تقييم عام** (من 10)
2. **نقاط القوة** (3-5 نقاط)
3. **نقاط الضعف** (3-5 نقاط)
4. **توصيات فورية للتحسين** (5 توصيات محددة)
5. **كلمات مفتاحية مقترحة** للـ ATS

السيرة الذاتية:
{cv_text}

قدم التحليل بشكل مختصر ومباشر وعملي."""

    improvement_prompt = f"""أعد كتابة السيرة الذاتية التالية بشكل احترافي ومحسّن:
- استخدم أفعال قوية
- أضف أرقام وإنجازات محددة
- حسّن التنسيق
- أضف كلمات مفتاحية للـ ATS

السيرة الذاتية الأصلية:
{cv_text}

اكتب النسخة المحسّنة فقط، بدون شرح."""

    try:
        # Get analysis
        analysis_response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=1500
        )
        analysis = analysis_response.choices[0].message.content

        # Get improved version
        improvement_response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": improvement_prompt}],
            max_tokens=2000
        )
        improved_cv = improvement_response.choices[0].message.content

        return {
            "analysis": analysis,
            "improved_cv": improved_cv
        }
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return None

# Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة البداية"""
    welcome_message = """🎯 **حلل سيرتك الذاتية في 60 ثانية**

أرسل سيرتك الذاتية (نص أو ملف PDF) واحصل على:
✅ تحليل احترافي كامل
✅ نقاط القوة والضعف
✅ نسخة محسّنة جاهزة للاستخدام

💰 **السعر: $3 فقط**

📎 أرسل سيرتك الآن للبدء..."""

    await update.message.reply_text(welcome_message, parse_mode="Markdown")

async def handle_text_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال السيرة الذاتية كنص"""
    user = update.effective_user
    cv_text = update.message.text
    
    # Ignore short messages
    if len(cv_text) < 100:
        await update.message.reply_text("⚠️ الرجاء إرسال سيرتك الذاتية الكاملة (نص أو ملف PDF)")
        return
    
    # Save CV
    save_user_cv(user.id, user.username, cv_text)
    
    # Send payment button
    keyboard = [[InlineKeyboardButton(
        f"💳 ادفع ${SERVICE_PRICE} واحصل على التحليل",
        url=f"{PAYPAL_LINK}"
    )]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    keyboard2 = [[InlineKeyboardButton(
        "✅ دفعت - أرسل التحليل",
        callback_data="paid_confirm"
    )]]
    reply_markup2 = InlineKeyboardMarkup(keyboard2)
    
    await update.message.reply_text(
        "✅ **تم استلام سيرتك الذاتية!**\n\n"
        f"💰 ادفع ${SERVICE_PRICE} عبر PayPal للحصول على:\n"
        "• تحليل احترافي كامل\n"
        "• نسخة محسّنة من سيرتك\n\n"
        "👇 اضغط للدفع:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(
        "بعد الدفع، اضغط الزر أدناه:",
        reply_markup=reply_markup2
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال ملف PDF"""
    user = update.effective_user
    document = update.message.document
    
    if document.mime_type != "application/pdf":
        await update.message.reply_text("⚠️ الرجاء إرسال ملف PDF أو نص السيرة الذاتية مباشرة")
        return
    
    await update.message.reply_text("📄 جاري قراءة الملف...")
    
    try:
        # Download file
        file = await context.bot.get_file(document.file_id)
        file_path = f"/tmp/cv_{user.id}.pdf"
        await file.download_to_drive(file_path)
        
        # Extract text from PDF
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            cv_text = ""
            for page in reader.pages:
                cv_text += page.extract_text() + "\n"
        
        if len(cv_text.strip()) < 50:
            await update.message.reply_text("⚠️ لم نتمكن من قراءة الملف. الرجاء إرسال السيرة كنص.")
            return
        
        # Save CV
        save_user_cv(user.id, user.username, cv_text)
        
        # Send payment button
        keyboard = [[InlineKeyboardButton(
            f"💳 ادفع ${SERVICE_PRICE} واحصل على التحليل",
            url=f"{PAYPAL_LINK}"
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        keyboard2 = [[InlineKeyboardButton(
            "✅ دفعت - أرسل التحليل",
            callback_data="paid_confirm"
        )]]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        
        await update.message.reply_text(
            "✅ **تم استلام سيرتك الذاتية!**\n\n"
            f"💰 ادفع ${SERVICE_PRICE} عبر PayPal للحصول على:\n"
            "• تحليل احترافي كامل\n"
            "• نسخة محسّنة من سيرتك\n\n"
            "👇 اضغط للدفع:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(
            "بعد الدفع، اضغط الزر أدناه:",
            reply_markup=reply_markup2
        )
        
    except Exception as e:
        logger.error(f"PDF Error: {e}")
        await update.message.reply_text("⚠️ حدث خطأ. الرجاء إرسال السيرة كنص مباشرة.")

async def handle_payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأكيد الدفع وإرسال التحليل"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    cv_text = get_user_cv(user.id)
    
    if not cv_text:
        await query.edit_message_text("⚠️ لم نجد سيرتك الذاتية. الرجاء إرسالها مرة أخرى.")
        return
    
    await query.edit_message_text("⏳ جاري تحليل سيرتك الذاتية... (60 ثانية)")
    
    # Analyze CV
    result = await analyze_cv_with_ai(cv_text)
    
    if not result:
        await context.bot.send_message(
            chat_id=user.id,
            text="⚠️ حدث خطأ في التحليل. سنتواصل معك قريبًا."
        )
        return
    
    # Mark as paid
    mark_user_paid(user.id)
    
    # Send analysis
    await context.bot.send_message(
        chat_id=user.id,
        text=f"📊 **تحليل سيرتك الذاتية:**\n\n{result['analysis']}",
        parse_mode="Markdown"
    )
    
    # Send improved CV
    await context.bot.send_message(
        chat_id=user.id,
        text=f"✨ **النسخة المحسّنة من سيرتك:**\n\n{result['improved_cv']}",
        parse_mode="Markdown"
    )
    
    # Final message
    await context.bot.send_message(
        chat_id=user.id,
        text="✅ **تم!** شكرًا لاستخدامك خدمتنا.\n\n"
             "💡 شارك البوت مع أصدقائك الباحثين عن عمل!"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأخطاء"""
    logger.error(f"Error: {context.error}")

def main():
    """تشغيل البوت"""
    # Initialize database
    init_db()
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_cv))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    application.add_handler(CallbackQueryHandler(handle_payment_confirmation, pattern="^paid_confirm$"))
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("🚀 Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
