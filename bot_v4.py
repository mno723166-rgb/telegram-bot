#!/usr/bin/env python3
"""
CV Analysis Bot v4 - Simple Direct Crypto Payment
نظام دفع مباشر وبسيط - USDT (TRC20) و BNB (BEP20)
"""

import os
import logging
import sqlite3
import secrets
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
SERVICE_PRICE = 3  # $3

# Wallet Addresses
USDT_TRC20_ADDRESS = "TFgQpnv2qVMHMojdjUrrzQ8iVB3fDR2HN9"
BNB_BEP20_ADDRESS = "0x45ed64749a512936d2e7956f84d58f1240e8d2e0"

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
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id INTEGER,
            username TEXT,
            cv_text TEXT,
            payment_method TEXT,
            payment_status TEXT DEFAULT 'pending',
            amount REAL,
            created_at TEXT,
            paid_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def create_order(user_id, username, cv_text):
    order_id = secrets.token_hex(4).upper()  # Short ID like "A1B2C3D4"
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
    c.execute("SELECT * FROM orders WHERE order_id = ? OR order_id LIKE ?", (order_id, f"{order_id}%"))
    result = c.fetchone()
    conn.close()
    if result:
        return {
            "order_id": result[0],
            "user_id": result[1],
            "username": result[2],
            "cv_text": result[3],
            "payment_method": result[4],
            "payment_status": result[5],
            "amount": result[6],
            "created_at": result[7],
            "paid_at": result[8]
        }
    return None

def mark_order_paid(order_id):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        UPDATE orders SET payment_status = 'paid', paid_at = ? WHERE order_id = ?
    """, (datetime.now().isoformat(), order_id))
    conn.commit()
    conn.close()

def get_pending_order(user_id):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        SELECT order_id FROM orders 
        WHERE user_id = ? AND payment_status = 'pending' 
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# AI Analysis Function
async def analyze_cv_with_ai(cv_text: str) -> dict:
    """تحليل وتحسين السيرة الذاتية"""
    
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

# Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة البداية"""
    welcome_message = """🎯 **حلل سيرتك الذاتية في 60 ثانية**

أرسل سيرتك الذاتية واحصل على:
✅ تحليل احترافي كامل
✅ نقاط القوة والضعف
✅ نسخة محسّنة جاهزة

💰 **السعر: $3 فقط**
💎 ادفع بـ USDT أو BNB

📎 **أرسل سيرتك الآن...**"""

    await update.message.reply_text(welcome_message, parse_mode="Markdown")

async def handle_text_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال السيرة الذاتية"""
    user = update.effective_user
    cv_text = update.message.text
    
    if len(cv_text) < 100:
        await update.message.reply_text("⚠️ أرسل سيرتك الذاتية الكاملة")
        return
    
    order_id = create_order(user.id, user.username, cv_text)
    
    # Payment message with wallet addresses
    payment_message = f"""✅ **تم استلام سيرتك!**

💰 **المبلغ: $3**
🔢 **رقم الطلب: `{order_id}`**

━━━━━━━━━━━━━━━

💎 **ادفع بـ USDT (TRC20):**
```
{USDT_TRC20_ADDRESS}
```

🟡 **أو ادفع بـ BNB (BEP20):**
```
{BNB_BEP20_ADDRESS}
```

━━━━━━━━━━━━━━━

⚠️ **بعد الدفع:**
أرسل لقطة شاشة أو hash التحويل"""

    keyboard = [
        [InlineKeyboardButton("📋 نسخ عنوان USDT", callback_data=f"copy_usdt_{order_id}")],
        [InlineKeyboardButton("📋 نسخ عنوان BNB", callback_data=f"copy_bnb_{order_id}")],
        [InlineKeyboardButton("💳 PayPal ($3)", url=PAYPAL_LINK)],
        [InlineKeyboardButton("✅ أرسلت الدفع", callback_data=f"sent_{order_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        payment_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال ملف PDF"""
    user = update.effective_user
    document = update.message.document
    
    if document.mime_type != "application/pdf":
        await update.message.reply_text("⚠️ أرسل ملف PDF أو نص السيرة مباشرة")
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
            await update.message.reply_text("⚠️ لم نتمكن من قراءة الملف. أرسل السيرة كنص.")
            return
        
        order_id = create_order(user.id, user.username, cv_text)
        
        payment_message = f"""✅ **تم استلام سيرتك!**

💰 **المبلغ: $3**
🔢 **رقم الطلب: `{order_id}`**

━━━━━━━━━━━━━━━

💎 **ادفع بـ USDT (TRC20):**
```
{USDT_TRC20_ADDRESS}
```

🟡 **أو ادفع بـ BNB (BEP20):**
```
{BNB_BEP20_ADDRESS}
```

━━━━━━━━━━━━━━━

⚠️ **بعد الدفع:**
أرسل لقطة شاشة أو hash التحويل"""

        keyboard = [
            [InlineKeyboardButton("📋 نسخ عنوان USDT", callback_data=f"copy_usdt_{order_id}")],
            [InlineKeyboardButton("📋 نسخ عنوان BNB", callback_data=f"copy_bnb_{order_id}")],
            [InlineKeyboardButton("💳 PayPal ($3)", url=PAYPAL_LINK)],
            [InlineKeyboardButton("✅ أرسلت الدفع", callback_data=f"sent_{order_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            payment_message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"PDF Error: {e}")
        await update.message.reply_text("⚠️ خطأ. أرسل السيرة كنص.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأزرار"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("copy_usdt_"):
        await query.answer(f"📋 عنوان USDT:\n{USDT_TRC20_ADDRESS}", show_alert=True)
        
    elif data.startswith("copy_bnb_"):
        await query.answer(f"📋 عنوان BNB:\n{BNB_BEP20_ADDRESS}", show_alert=True)
        
    elif data.startswith("sent_"):
        order_id = data.replace("sent_", "")
        await query.edit_message_text(
            f"📸 **أرسل إثبات الدفع:**\n\n"
            f"• لقطة شاشة للتحويل\n"
            f"• أو hash/TXID التحويل\n\n"
            f"🔢 رقم طلبك: `{order_id}`\n\n"
            f"سيتم إرسال التحليل فور التأكيد ✅",
            parse_mode="Markdown"
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال لقطة شاشة الدفع"""
    user = update.effective_user
    order_id = get_pending_order(user.id)
    
    if order_id:
        await update.message.reply_text(
            f"✅ **تم استلام إثبات الدفع!**\n\n"
            f"🔢 رقم الطلب: `{order_id}`\n\n"
            f"⏳ جاري التحقق...\n"
            f"سيتم إرسال التحليل خلال دقائق.",
            parse_mode="Markdown"
        )
        logger.info(f"Payment proof received for order {order_id} from user {user.id}")
    else:
        await update.message.reply_text("⚠️ أرسل سيرتك الذاتية أولاً")

async def handle_tx_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال hash التحويل"""
    user = update.effective_user
    text = update.message.text
    
    # Check if it looks like a transaction hash
    if len(text) >= 60 and text.replace("0x", "").isalnum():
        order_id = get_pending_order(user.id)
        
        if order_id:
            await update.message.reply_text(
                f"✅ **تم استلام hash التحويل!**\n\n"
                f"🔢 رقم الطلب: `{order_id}`\n"
                f"📝 Hash: `{text[:20]}...`\n\n"
                f"⏳ جاري التحقق...\n"
                f"سيتم إرسال التحليل خلال دقائق.",
                parse_mode="Markdown"
            )
            logger.info(f"TX hash received for order {order_id}: {text}")
            return True
    return False

# Admin Commands
async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الموافقة على الدفع"""
    ADMIN_IDS = []  # Add your Telegram user ID here
    
    user = update.effective_user
    if ADMIN_IDS and user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        # List pending orders
        conn = sqlite3.connect("users.db", check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT order_id, user_id, created_at FROM orders WHERE payment_status = 'pending' ORDER BY created_at DESC LIMIT 10")
        orders = c.fetchall()
        conn.close()
        
        if orders:
            msg = "📋 **الطلبات المعلقة:**\n\n"
            for o in orders:
                msg += f"• `{o[0]}` - User: {o[1]}\n"
            msg += f"\n✅ للموافقة: `/approve ORDER_ID`"
        else:
            msg = "✅ لا توجد طلبات معلقة"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
        return
    
    order_id = context.args[0].upper()
    order = get_order(order_id)
    
    if not order:
        await update.message.reply_text("❌ الطلب غير موجود")
        return
    
    if order["payment_status"] == "paid":
        await update.message.reply_text("✅ الطلب مدفوع مسبقًا")
        return
    
    await update.message.reply_text(f"⏳ جاري معالجة الطلب {order['order_id']}...")
    
    mark_order_paid(order["order_id"])
    
    result = await analyze_cv_with_ai(order["cv_text"])
    
    if result:
        await context.bot.send_message(
            chat_id=order["user_id"],
            text="✅ **تم تأكيد الدفع!**\n\n⏳ جاري تحليل سيرتك...",
            parse_mode="Markdown"
        )
        
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=f"📊 **تحليل سيرتك الذاتية:**\n\n{result['analysis']}",
            parse_mode="Markdown"
        )
        
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=f"✨ **النسخة المحسّنة:**\n\n{result['improved_cv']}",
            parse_mode="Markdown"
        )
        
        await context.bot.send_message(
            chat_id=order["user_id"],
            text="✅ **تم!** شكرًا لاستخدامك خدمتنا 🙏"
        )
        
        await update.message.reply_text(f"✅ تم إرسال التحليل للطلب {order['order_id']}")
    else:
        await update.message.reply_text("❌ خطأ في التحليل")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات"""
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM orders")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM orders WHERE payment_status = 'paid'")
    paid = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM orders WHERE payment_status = 'pending'")
    pending = c.fetchone()[0]
    
    c.execute("SELECT SUM(amount) FROM orders WHERE payment_status = 'paid'")
    revenue = c.fetchone()[0] or 0
    
    conn.close()
    
    await update.message.reply_text(
        f"📊 **الإحصائيات:**\n\n"
        f"📝 إجمالي الطلبات: {total}\n"
        f"✅ المدفوعة: {paid}\n"
        f"⏳ المعلقة: {pending}\n"
        f"💰 الإيرادات: ${revenue}",
        parse_mode="Markdown"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")

def main():
    init_db()
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", admin_approve))
    application.add_handler(CommandHandler("stats", admin_stats))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Text handler - check for TX hash first, then CV
    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await handle_tx_hash(update, context):
            await handle_text_cv(update, context)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error_handler)
    
    logger.info("🚀 Bot v4 started - Direct Crypto Payment!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
