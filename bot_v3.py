#!/usr/bin/env python3
"""
CV Analysis Bot v3 - Secure Payment System with IPN
نظام دفع آمن عبر NOWPayments مع Webhook + PayPal
"""

import os
import logging
import asyncio
import sqlite3
import secrets
import aiohttp
import threading
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, request, jsonify

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
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
IPN_CALLBACK_URL = os.getenv("IPN_CALLBACK_URL", "https://8080-ivz07sdt1fwj9erfyz17f-bc3ab327.manus-asia.computer/ipn")

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

# Flask app for IPN webhook
flask_app = Flask(__name__)

# Telegram bot instance for sending messages from webhook
telegram_bot = Bot(token=TELEGRAM_TOKEN)

# Database setup
def init_db():
    conn = sqlite3.connect("users.db", check_same_thread=False)
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
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        INSERT INTO orders (order_id, user_id, username, cv_text, amount, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (order_id, user_id, username, cv_text, SERVICE_PRICE, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return order_id

def get_order(order_id):
    conn = sqlite3.connect("users.db", check_same_thread=False)
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

def get_order_by_payment_id(payment_id):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE payment_id = ?", (str(payment_id),))
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
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        UPDATE orders SET payment_method = ?, payment_id = ? WHERE order_id = ?
    """, (payment_method, str(payment_id), order_id))
    conn.commit()
    conn.close()

def mark_order_paid(order_id):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        UPDATE orders SET payment_status = 'paid', paid_at = ? WHERE order_id = ?
    """, (datetime.now().isoformat(), order_id))
    conn.commit()
    conn.close()

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
        "order_description": f"CV Analysis Service",
        "ipn_callback_url": IPN_CALLBACK_URL,
        "success_url": "https://t.me/Aistaruae_bot",
        "cancel_url": "https://t.me/Aistaruae_bot"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{NOWPAYMENTS_API_URL}/invoice",
            headers=headers,
            json=payload
        ) as response:
            response_text = await response.text()
            logger.info(f"NOWPayments Response: {response.status} - {response_text}")
            if response.status == 200:
                data = await response.json()
                return data
            else:
                logger.error(f"NOWPayments Error: {response_text}")
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
def analyze_cv_with_ai_sync(cv_text: str) -> dict:
    """تحليل وتحسين السيرة الذاتية باستخدام AI (sync version)"""
    
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
        analysis_response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=1500
        )
        analysis = analysis_response.choices[0].message.content

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

async def analyze_cv_with_ai(cv_text: str) -> dict:
    """تحليل وتحسين السيرة الذاتية باستخدام AI"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, analyze_cv_with_ai_sync, cv_text)

# Flask IPN Webhook
@flask_app.route('/ipn', methods=['POST'])
def ipn_callback():
    """استقبال إشعارات الدفع من NOWPayments"""
    try:
        data = request.json
        logger.info(f"IPN Received: {data}")
        
        payment_status = data.get("payment_status")
        payment_id = data.get("payment_id")
        order_id = data.get("order_id")
        
        if payment_status in ["finished", "confirmed", "sending"]:
            # Find order
            order = get_order(order_id) if order_id else get_order_by_payment_id(payment_id)
            
            if order and order["payment_status"] != "paid":
                # Mark as paid
                mark_order_paid(order["order_id"])
                
                # Process and send result
                asyncio.run(process_paid_order(order))
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"IPN Error: {e}")
        return jsonify({"status": "error"}), 500

async def process_paid_order(order):
    """معالجة الطلب المدفوع وإرسال النتيجة"""
    try:
        result = await analyze_cv_with_ai(order["cv_text"])
        
        if result:
            await telegram_bot.send_message(
                chat_id=order["user_id"],
                text="✅ **تم تأكيد الدفع!**\n\nجاري تحليل سيرتك الذاتية...",
                parse_mode="Markdown"
            )
            
            await telegram_bot.send_message(
                chat_id=order["user_id"],
                text=f"📊 **تحليل سيرتك الذاتية:**\n\n{result['analysis']}",
                parse_mode="Markdown"
            )
            
            await telegram_bot.send_message(
                chat_id=order["user_id"],
                text=f"✨ **النسخة المحسّنة من سيرتك:**\n\n{result['improved_cv']}",
                parse_mode="Markdown"
            )
            
            await telegram_bot.send_message(
                chat_id=order["user_id"],
                text="✅ **تم!** شكرًا لاستخدامك خدمتنا.\n\n💡 شارك البوت مع أصدقائك!"
            )
    except Exception as e:
        logger.error(f"Process order error: {e}")

@flask_app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة البداية"""
    welcome_message = """🎯 **حلل سيرتك الذاتية في 60 ثانية**

أرسل سيرتك الذاتية (نص أو ملف PDF) واحصل على:
✅ تحليل احترافي كامل
✅ نقاط القوة والضعف
✅ نسخة محسّنة جاهزة للاستخدام

💰 **السعر: $3 فقط**
💳 ادفع بـ USDT أو BTC أو PayPal

📎 أرسل سيرتك الآن للبدء..."""

    await update.message.reply_text(welcome_message, parse_mode="Markdown")

async def handle_text_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال السيرة الذاتية كنص"""
    user = update.effective_user
    cv_text = update.message.text
    
    if len(cv_text) < 100:
        await update.message.reply_text("⚠️ الرجاء إرسال سيرتك الذاتية الكاملة (نص أو ملف PDF)")
        return
    
    order_id = create_order(user.id, user.username, cv_text)
    context.user_data["current_order"] = order_id
    
    await update.message.reply_text("✅ تم استلام سيرتك الذاتية!\n\n⏳ جاري إنشاء رابط الدفع...")
    
    invoice = await create_nowpayments_invoice(order_id, SERVICE_PRICE)
    
    if invoice and invoice.get("invoice_url"):
        invoice_id = invoice.get("id")
        update_order_payment(order_id, "crypto", invoice_id)
        
        keyboard = [
            [InlineKeyboardButton("💎 ادفع بالعملات الرقمية (USDT/BTC)", url=invoice["invoice_url"])],
            [InlineKeyboardButton("💳 ادفع بـ PayPal ($3)", url=PAYPAL_LINK)],
            [InlineKeyboardButton("🔄 تحققت من الدفع", callback_data=f"check_{order_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"💰 **طلب رقم:** `{order_id[:8]}`\n"
            f"💵 **المبلغ:** ${SERVICE_PRICE}\n\n"
            "**اختر طريقة الدفع:**\n\n"
            "💎 **العملات الرقمية** - تأكيد تلقائي فوري\n"
            "💳 **PayPal** - تأكيد يدوي\n\n"
            "⚠️ بعد الدفع بـ PayPal، أرسل لقطة شاشة للتأكيد",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        # Fallback - PayPal only
        keyboard = [
            [InlineKeyboardButton("💳 ادفع بـ PayPal ($3)", url=PAYPAL_LINK)],
            [InlineKeyboardButton("📸 أرسلت الدفع - تأكيد", callback_data=f"paypal_{order_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"💰 **طلب رقم:** `{order_id[:8]}`\n"
            f"💵 **المبلغ:** ${SERVICE_PRICE}\n\n"
            "💳 ادفع عبر PayPal ثم أرسل لقطة شاشة للتأكيد",
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
        file = await context.bot.get_file(document.file_id)
        file_path = f"/tmp/cv_{user.id}.pdf"
        await file.download_to_drive(file_path)
        
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            cv_text = ""
            for page in reader.pages:
                cv_text += page.extract_text() + "\n"
        
        if len(cv_text.strip()) < 50:
            await update.message.reply_text("⚠️ لم نتمكن من قراءة الملف. الرجاء إرسال السيرة كنص.")
            return
        
        order_id = create_order(user.id, user.username, cv_text)
        context.user_data["current_order"] = order_id
        
        await update.message.reply_text("✅ تم استلام سيرتك الذاتية!\n\n⏳ جاري إنشاء رابط الدفع...")
        
        invoice = await create_nowpayments_invoice(order_id, SERVICE_PRICE)
        
        if invoice and invoice.get("invoice_url"):
            invoice_id = invoice.get("id")
            update_order_payment(order_id, "crypto", invoice_id)
            
            keyboard = [
                [InlineKeyboardButton("💎 ادفع بالعملات الرقمية (USDT/BTC)", url=invoice["invoice_url"])],
                [InlineKeyboardButton("💳 ادفع بـ PayPal ($3)", url=PAYPAL_LINK)],
                [InlineKeyboardButton("🔄 تحققت من الدفع", callback_data=f"check_{order_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"💰 **طلب رقم:** `{order_id[:8]}`\n"
                f"💵 **المبلغ:** ${SERVICE_PRICE}\n\n"
                "**اختر طريقة الدفع:**\n\n"
                "💎 **العملات الرقمية** - تأكيد تلقائي فوري\n"
                "💳 **PayPal** - تأكيد يدوي\n\n"
                "⚠️ بعد الدفع بـ PayPal، أرسل لقطة شاشة للتأكيد",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            keyboard = [
                [InlineKeyboardButton("💳 ادفع بـ PayPal ($3)", url=PAYPAL_LINK)],
                [InlineKeyboardButton("📸 أرسلت الدفع - تأكيد", callback_data=f"paypal_{order_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"💰 **طلب رقم:** `{order_id[:8]}`\n"
                f"💵 **المبلغ:** ${SERVICE_PRICE}\n\n"
                "💳 ادفع عبر PayPal ثم أرسل لقطة شاشة للتأكيد",
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
    
    callback_data = query.data
    
    if callback_data.startswith("check_"):
        order_id = callback_data.replace("check_", "")
    elif callback_data.startswith("paypal_"):
        order_id = callback_data.replace("paypal_", "")
        await query.edit_message_text(
            "📸 **للتأكيد من دفع PayPal:**\n\n"
            "أرسل لقطة شاشة لإيصال الدفع\n"
            f"مع ذكر رقم الطلب: `{order_id[:8]}`\n\n"
            "سيتم مراجعة الدفع وإرسال التحليل خلال دقائق.",
            parse_mode="Markdown"
        )
        return
    else:
        return
    
    order = get_order(order_id)
    
    if not order:
        await query.edit_message_text("⚠️ لم نجد هذا الطلب. الرجاء إرسال سيرتك مرة أخرى.")
        return
    
    if order["payment_status"] == "paid":
        await query.edit_message_text("✅ تم معالجة هذا الطلب مسبقًا.")
        return
    
    user = update.effective_user
    payment_confirmed = False
    
    if order["payment_id"]:
        status = await check_payment_status(order["payment_id"])
        logger.info(f"Payment status for {order_id}: {status}")
        
        if status in ["finished", "confirmed", "sending", "partially_paid"]:
            payment_confirmed = True
    
    if payment_confirmed:
        await query.edit_message_text("✅ تم تأكيد الدفع!\n\n⏳ جاري تحليل سيرتك الذاتية...")
        
        mark_order_paid(order_id)
        
        result = await analyze_cv_with_ai(order["cv_text"])
        
        if not result:
            await context.bot.send_message(
                chat_id=user.id,
                text="⚠️ حدث خطأ في التحليل. سنتواصل معك قريبًا."
            )
            return
        
        await context.bot.send_message(
            chat_id=user.id,
            text=f"📊 **تحليل سيرتك الذاتية:**\n\n{result['analysis']}",
            parse_mode="Markdown"
        )
        
        await context.bot.send_message(
            chat_id=user.id,
            text=f"✨ **النسخة المحسّنة من سيرتك:**\n\n{result['improved_cv']}",
            parse_mode="Markdown"
        )
        
        await context.bot.send_message(
            chat_id=user.id,
            text="✅ **تم!** شكرًا لاستخدامك خدمتنا.\n\n💡 شارك البوت مع أصدقائك!"
        )
    else:
        keyboard = [
            [InlineKeyboardButton("🔄 تحقق مرة أخرى", callback_data=f"check_{order_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⏳ **لم نتمكن من تأكيد الدفع بعد.**\n\n"
            "• إذا دفعت بالعملات الرقمية، انتظر 1-3 دقائق للتأكيد\n"
            "• إذا دفعت بـ PayPal، أرسل لقطة شاشة للإيصال\n\n"
            "ثم اضغط **تحقق مرة أخرى**",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال لقطة شاشة للدفع"""
    user = update.effective_user
    
    # Get the latest pending order for this user
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        SELECT order_id FROM orders 
        WHERE user_id = ? AND payment_status = 'pending' 
        ORDER BY created_at DESC LIMIT 1
    """, (user.id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        order_id = result[0]
        await update.message.reply_text(
            f"📸 تم استلام لقطة الشاشة!\n\n"
            f"رقم الطلب: `{order_id[:8]}`\n\n"
            "⏳ جاري مراجعة الدفع...\n"
            "سيتم إرسال التحليل خلال دقائق.",
            parse_mode="Markdown"
        )
        
        # Log for admin review
        logger.info(f"PayPal payment screenshot received for order {order_id} from user {user.id}")
    else:
        await update.message.reply_text(
            "⚠️ لم نجد طلب معلق لك.\n"
            "الرجاء إرسال سيرتك الذاتية أولاً."
        )

# Admin command
async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر المشرف للموافقة على الدفع"""
    ADMIN_IDS = []  # Add your Telegram user ID
    
    user = update.effective_user
    if ADMIN_IDS and user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text("استخدم: /approve <order_id>")
        return
    
    order_id = context.args[0]
    
    # Try to find order by partial ID
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT order_id FROM orders WHERE order_id LIKE ?", (f"{order_id}%",))
    result = c.fetchone()
    conn.close()
    
    if not result:
        await update.message.reply_text("❌ الطلب غير موجود")
        return
    
    full_order_id = result[0]
    order = get_order(full_order_id)
    
    if order["payment_status"] == "paid":
        await update.message.reply_text("✅ الطلب مدفوع مسبقًا")
        return
    
    mark_order_paid(full_order_id)
    
    result = await analyze_cv_with_ai(order["cv_text"])
    
    if result:
        await context.bot.send_message(
            chat_id=order["user_id"],
            text="✅ **تم تأكيد الدفع!**",
            parse_mode="Markdown"
        )
        
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
    
    await update.message.reply_text(f"✅ تمت الموافقة على الطلب {full_order_id[:8]}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأخطاء"""
    logger.error(f"Error: {context.error}")

def run_flask():
    """تشغيل Flask في thread منفصل"""
    flask_app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

def main():
    """تشغيل البوت"""
    init_db()
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 Flask IPN server started on port 8080")
    
    # Create Telegram application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", admin_approve))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_cv))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(handle_payment_check, pattern="^(check_|paypal_)"))
    application.add_error_handler(error_handler)
    
    logger.info("🚀 Bot v3 started with secure payment + IPN!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
