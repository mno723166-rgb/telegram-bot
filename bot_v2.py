#!/usr/bin/env python3
"""
CV Analysis Bot v2 - Secure Payment System
نظام دفع آمن عبر NOWPayments + PayPal
لا يمكن الحصول على الخدمة بدون دفع حقيقي
"""

import os
import logging
import asyncio
import sqlite3
import hashlib
import secrets
import aiohttp
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
NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY")
SERVICE_PRICE = float(os.getenv("SERVICE_PRICE", "3"))

# NOWPayments API
NOWPAYMENTS_API_URL = "https://api.nowpayments.io/v1"

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
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id INTEGER,
            username TEXT,
            cv_text TEXT,
            payment_method TEXT,
            payment_id TEXT,
            payment_status TEXT DEFAULT 'pending',
            amount REAL,
            created_at TEXT,
            paid_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def create_order(user_id, username, cv_text):
    """إنشاء طلب جديد بمعرف فريد"""
    order_id = secrets.token_hex(8)
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO orders (order_id, user_id, username, cv_text, amount, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (order_id, user_id, username, cv_text, SERVICE_PRICE, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return order_id

def get_order(order_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return {
            "order_id": result[0],
            "user_id": result[1],
            "username": result[2],
            "cv_text": result[3],
            "payment_method": result[4],
            "payment_id": result[5],
            "payment_status": result[6],
            "amount": result[7],
            "created_at": result[8],
            "paid_at": result[9]
        }
    return None

def update_order_payment(order_id, payment_method, payment_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        UPDATE orders SET payment_method = ?, payment_id = ? WHERE order_id = ?
    """, (payment_method, payment_id, order_id))
    conn.commit()
    conn.close()

def mark_order_paid(order_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        UPDATE orders SET payment_status = 'paid', paid_at = ? WHERE order_id = ?
    """, (datetime.now().isoformat(), order_id))
    conn.commit()
    conn.close()

def get_pending_order_by_user(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        SELECT order_id FROM orders 
        WHERE user_id = ? AND payment_status = 'pending' 
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# NOWPayments Integration
async def create_nowpayments_invoice(order_id: str, amount: float) -> dict:
    """إنشاء فاتورة دفع عبر NOWPayments"""
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "price_amount": amount,
        "price_currency": "usd",
        "order_id": order_id,
        "order_description": f"CV Analysis - Order {order_id}",
        "ipn_callback_url": "",  # Will be handled by polling
        "success_url": "",
        "cancel_url": ""
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{NOWPAYMENTS_API_URL}/invoice",
            headers=headers,
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                error = await response.text()
                logger.error(f"NOWPayments Error: {error}")
                return None

async def check_payment_status(payment_id: str) -> str:
    """التحقق من حالة الدفع"""
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{NOWPAYMENTS_API_URL}/payment/{payment_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("payment_status", "unknown")
            return "unknown"

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
    
    # Create order
    order_id = create_order(user.id, user.username, cv_text)
    
    # Store order_id in context for later use
    context.user_data["current_order"] = order_id
    
    await update.message.reply_text("✅ تم استلام سيرتك الذاتية!\n\n⏳ جاري إنشاء رابط الدفع...")
    
    # Create NOWPayments invoice
    invoice = await create_nowpayments_invoice(order_id, SERVICE_PRICE)
    
    if invoice and invoice.get("invoice_url"):
        update_order_payment(order_id, "crypto", invoice.get("id"))
        
        keyboard = [
            [InlineKeyboardButton("💎 ادفع بالعملات الرقمية", url=invoice["invoice_url"])],
            [InlineKeyboardButton("💳 ادفع بـ PayPal", url=f"{PAYPAL_LINK}")],
            [InlineKeyboardButton(f"🔄 تحقق من الدفع (الطلب: {order_id[:8]})", callback_data=f"check_{order_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"💰 **الدفع مطلوب: ${SERVICE_PRICE}**\n\n"
            f"🔢 رقم الطلب: `{order_id}`\n\n"
            "اختر طريقة الدفع:\n"
            "• **العملات الرقمية**: USDT, BTC, ETH, وغيرها\n"
            "• **PayPal**: دفع سريع\n\n"
            "⚠️ بعد الدفع، اضغط **تحقق من الدفع** للحصول على التحليل.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        # Fallback to PayPal only
        keyboard = [
            [InlineKeyboardButton("💳 ادفع بـ PayPal", url=f"{PAYPAL_LINK}")],
            [InlineKeyboardButton(f"🔄 تحقق من الدفع (الطلب: {order_id[:8]})", callback_data=f"check_{order_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"💰 **الدفع مطلوب: ${SERVICE_PRICE}**\n\n"
            f"🔢 رقم الطلب: `{order_id}`\n\n"
            "اضغط للدفع عبر PayPal، ثم اضغط **تحقق من الدفع**.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
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
        
        # Create order
        order_id = create_order(user.id, user.username, cv_text)
        context.user_data["current_order"] = order_id
        
        await update.message.reply_text("✅ تم استلام سيرتك الذاتية!\n\n⏳ جاري إنشاء رابط الدفع...")
        
        # Create NOWPayments invoice
        invoice = await create_nowpayments_invoice(order_id, SERVICE_PRICE)
        
        if invoice and invoice.get("invoice_url"):
            update_order_payment(order_id, "crypto", invoice.get("id"))
            
            keyboard = [
                [InlineKeyboardButton("💎 ادفع بالعملات الرقمية", url=invoice["invoice_url"])],
                [InlineKeyboardButton("💳 ادفع بـ PayPal", url=f"{PAYPAL_LINK}")],
                [InlineKeyboardButton(f"🔄 تحقق من الدفع", callback_data=f"check_{order_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"💰 **الدفع مطلوب: ${SERVICE_PRICE}**\n\n"
                f"🔢 رقم الطلب: `{order_id}`\n\n"
                "اختر طريقة الدفع:\n"
                "• **العملات الرقمية**: USDT, BTC, ETH, وغيرها\n"
                "• **PayPal**: دفع سريع\n\n"
                "⚠️ بعد الدفع، اضغط **تحقق من الدفع** للحصول على التحليل.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            keyboard = [
                [InlineKeyboardButton("💳 ادفع بـ PayPal", url=f"{PAYPAL_LINK}")],
                [InlineKeyboardButton(f"🔄 تحقق من الدفع", callback_data=f"check_{order_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"💰 **الدفع مطلوب: ${SERVICE_PRICE}**\n\n"
                f"🔢 رقم الطلب: `{order_id}`\n\n"
                "اضغط للدفع عبر PayPal، ثم اضغط **تحقق من الدفع**.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
    except Exception as e:
        logger.error(f"PDF Error: {e}")
        await update.message.reply_text("⚠️ حدث خطأ. الرجاء إرسال السيرة كنص مباشرة.")

async def handle_payment_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق من الدفع"""
    query = update.callback_query
    await query.answer()
    
    # Extract order_id from callback data
    callback_data = query.data
    if not callback_data.startswith("check_"):
        return
    
    order_id = callback_data.replace("check_", "")
    order = get_order(order_id)
    
    if not order:
        await query.edit_message_text("⚠️ لم نجد هذا الطلب. الرجاء إرسال سيرتك مرة أخرى.")
        return
    
    if order["payment_status"] == "paid":
        await query.edit_message_text("✅ تم معالجة هذا الطلب مسبقًا.")
        return
    
    user = update.effective_user
    
    # Check NOWPayments status if payment_id exists
    payment_confirmed = False
    
    if order["payment_id"]:
        status = await check_payment_status(order["payment_id"])
        logger.info(f"Payment status for {order_id}: {status}")
        
        if status in ["finished", "confirmed", "sending", "partially_paid"]:
            payment_confirmed = True
    
    if payment_confirmed:
        await query.edit_message_text("✅ تم تأكيد الدفع!\n\n⏳ جاري تحليل سيرتك الذاتية...")
        
        # Mark as paid
        mark_order_paid(order_id)
        
        # Analyze CV
        result = await analyze_cv_with_ai(order["cv_text"])
        
        if not result:
            await context.bot.send_message(
                chat_id=user.id,
                text="⚠️ حدث خطأ في التحليل. سنتواصل معك قريبًا."
            )
            return
        
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
    else:
        keyboard = [
            [InlineKeyboardButton("💎 ادفع بالعملات الرقمية", callback_data=f"crypto_{order_id}")],
            [InlineKeyboardButton("💳 ادفع بـ PayPal", url=f"{PAYPAL_LINK}")],
            [InlineKeyboardButton("🔄 تحقق مرة أخرى", callback_data=f"check_{order_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⏳ **لم نتمكن من تأكيد الدفع بعد.**\n\n"
            "إذا دفعت بالعملات الرقمية، انتظر 1-2 دقيقة للتأكيد.\n"
            "إذا دفعت بـ PayPal، تأكد من إتمام العملية.\n\n"
            "ثم اضغط **تحقق مرة أخرى**.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def handle_crypto_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعادة إنشاء رابط الدفع بالعملات الرقمية"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    if not callback_data.startswith("crypto_"):
        return
    
    order_id = callback_data.replace("crypto_", "")
    order = get_order(order_id)
    
    if not order:
        await query.edit_message_text("⚠️ لم نجد هذا الطلب. الرجاء إرسال سيرتك مرة أخرى.")
        return
    
    # Create new invoice
    invoice = await create_nowpayments_invoice(order_id, SERVICE_PRICE)
    
    if invoice and invoice.get("invoice_url"):
        update_order_payment(order_id, "crypto", invoice.get("id"))
        
        keyboard = [
            [InlineKeyboardButton("💎 افتح صفحة الدفع", url=invoice["invoice_url"])],
            [InlineKeyboardButton("🔄 تحقق من الدفع", callback_data=f"check_{order_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "💎 **الدفع بالعملات الرقمية**\n\n"
            "اضغط الزر أدناه لفتح صفحة الدفع.\n"
            "يمكنك الدفع بـ USDT, BTC, ETH, وغيرها.\n\n"
            "بعد الدفع، اضغط **تحقق من الدفع**.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text("⚠️ حدث خطأ. الرجاء المحاولة لاحقًا أو استخدام PayPal.")

# Admin command to manually approve payment (for PayPal)
async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر المشرف للموافقة على الدفع يدويًا"""
    # Add your admin user ID here
    ADMIN_IDS = []  # Add your Telegram user ID
    
    user = update.effective_user
    if ADMIN_IDS and user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text("استخدم: /approve <order_id>")
        return
    
    order_id = context.args[0]
    order = get_order(order_id)
    
    if not order:
        await update.message.reply_text("❌ الطلب غير موجود")
        return
    
    if order["payment_status"] == "paid":
        await update.message.reply_text("✅ الطلب مدفوع مسبقًا")
        return
    
    # Mark as paid
    mark_order_paid(order_id)
    
    # Analyze and send
    result = await analyze_cv_with_ai(order["cv_text"])
    
    if result:
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=f"📊 **تحليل سيرتك الذاتية:**\n\n{result['analysis']}",
            parse_mode="Markdown"
        )
        
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=f"✨ **النسخة المحسّنة من سيرتك:**\n\n{result['improved_cv']}",
            parse_mode="Markdown"
        )
        
        await context.bot.send_message(
            chat_id=order["user_id"],
            text="✅ **تم!** شكرًا لاستخدامك خدمتنا."
        )
    
    await update.message.reply_text(f"✅ تمت الموافقة على الطلب {order_id}")

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
    application.add_handler(CommandHandler("approve", admin_approve))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_cv))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    application.add_handler(CallbackQueryHandler(handle_payment_check, pattern="^check_"))
    application.add_handler(CallbackQueryHandler(handle_crypto_payment, pattern="^crypto_"))
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("🚀 Bot v2 started with secure payment!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
