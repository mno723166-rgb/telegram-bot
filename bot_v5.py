#!/usr/bin/env python3
"""
CV Analysis Bot v5 - All Payment Options
USDT/BNB مباشر + NOWPayments + PayPal
"""

import os
import logging
import sqlite3
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

load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PAYPAL_LINK = os.getenv("PAYPAL_LINK")
NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY")
SERVICE_PRICE = 3
NOWPAYMENTS_PRICE = 5  # Minimum for NOWPayments

# Wallet Addresses
USDT_TRC20_ADDRESS = "TFgQpnv2qVMHMojdjUrrzQ8iVB3fDR2HN9"
BNB_BEP20_ADDRESS = "0x45ed64749a512936d2e7956f84d58f1240e8d2e0"

# NOWPayments API
NOWPAYMENTS_API_URL = "https://api.nowpayments.io/v1"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

client = OpenAI()

# Database
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

def create_order(user_id, username, cv_text, amount=SERVICE_PRICE):
    order_id = secrets.token_hex(4).upper()
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        INSERT INTO orders (order_id, user_id, username, cv_text, amount, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (order_id, user_id, username, cv_text, amount, datetime.now().isoformat()))
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
            "order_id": result[0], "user_id": result[1], "username": result[2],
            "cv_text": result[3], "payment_method": result[4], "payment_id": result[5],
            "payment_status": result[6], "amount": result[7], "created_at": result[8], "paid_at": result[9]
        }
    return None

def update_order_payment(order_id, payment_method, payment_id, amount=None):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    if amount:
        c.execute("UPDATE orders SET payment_method=?, payment_id=?, amount=? WHERE order_id=?",
                  (payment_method, str(payment_id), amount, order_id))
    else:
        c.execute("UPDATE orders SET payment_method=?, payment_id=? WHERE order_id=?",
                  (payment_method, str(payment_id), order_id))
    conn.commit()
    conn.close()

def mark_order_paid(order_id):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("UPDATE orders SET payment_status='paid', paid_at=? WHERE order_id=?",
              (datetime.now().isoformat(), order_id))
    conn.commit()
    conn.close()

def get_pending_order(user_id):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT order_id FROM orders WHERE user_id=? AND payment_status='pending' ORDER BY created_at DESC LIMIT 1", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# NOWPayments
async def create_nowpayments_invoice(order_id: str, amount: float) -> dict:
    headers = {"x-api-key": NOWPAYMENTS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "price_amount": amount,
        "price_currency": "usd",
        "order_id": order_id,
        "order_description": "CV Analysis Service",
        "ipn_callback_url": "https://example.com/ipn",
        "success_url": "https://t.me/Aistaruae_bot",
        "cancel_url": "https://t.me/Aistaruae_bot"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{NOWPAYMENTS_API_URL}/invoice", headers=headers, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"NOWPayments Error: {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"NOWPayments Exception: {e}")
        return None

async def check_nowpayments_status(payment_id: str) -> str:
    headers = {"x-api-key": NOWPAYMENTS_API_KEY}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{NOWPAYMENTS_API_URL}/payment/{payment_id}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("payment_status", "unknown")
    except:
        pass
    return "unknown"

# AI Analysis
async def analyze_cv_with_ai(cv_text: str) -> dict:
    analysis_prompt = f"""أنت خبير موارد بشرية. حلل السيرة الذاتية:

1. **تقييم عام** (من 10)
2. **نقاط القوة** (3-5 نقاط)
3. **نقاط الضعف** (3-5 نقاط)
4. **توصيات للتحسين** (5 توصيات)
5. **كلمات مفتاحية ATS**

السيرة:
{cv_text}

تحليل مختصر ومباشر."""

    improvement_prompt = f"""أعد كتابة السيرة بشكل احترافي:
- أفعال قوية
- أرقام وإنجازات
- كلمات ATS

السيرة الأصلية:
{cv_text}

النسخة المحسّنة فقط:"""

    try:
        analysis = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=1500
        ).choices[0].message.content

        improved = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": improvement_prompt}],
            max_tokens=2000
        ).choices[0].message.content

        return {"analysis": analysis, "improved_cv": improved}
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return None

# Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 **حلل سيرتك الذاتية في 60 ثانية**\n\n"
        "✅ تحليل احترافي كامل\n"
        "✅ نقاط القوة والضعف\n"
        "✅ نسخة محسّنة جاهزة\n\n"
        "💰 **السعر: $3-5**\n\n"
        "📎 **أرسل سيرتك الآن...**",
        parse_mode="Markdown"
    )

async def handle_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cv_text = update.message.text
    
    if len(cv_text) < 100:
        await update.message.reply_text("⚠️ أرسل سيرتك الذاتية الكاملة")
        return
    
    order_id = create_order(user.id, user.username, cv_text)
    context.user_data["order_id"] = order_id
    
    keyboard = [
        [InlineKeyboardButton("💎 USDT/BNB مباشر ($3)", callback_data=f"direct_{order_id}")],
        [InlineKeyboardButton("🌐 NOWPayments - 100+ عملة ($5)", callback_data=f"nowpay_{order_id}")],
        [InlineKeyboardButton("💳 PayPal ($3)", url=PAYPAL_LINK)],
    ]
    
    await update.message.reply_text(
        f"✅ **تم استلام سيرتك!**\n\n"
        f"🔢 رقم الطلب: `{order_id}`\n\n"
        f"**اختر طريقة الدفع:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    doc = update.message.document
    
    if doc.mime_type != "application/pdf":
        await update.message.reply_text("⚠️ أرسل PDF أو نص")
        return
    
    await update.message.reply_text("📄 جاري القراءة...")
    
    try:
        file = await context.bot.get_file(doc.file_id)
        path = f"/tmp/cv_{user.id}.pdf"
        await file.download_to_drive(path)
        
        import PyPDF2
        with open(path, "rb") as f:
            cv_text = "".join([p.extract_text() for p in PyPDF2.PdfReader(f).pages])
        
        if len(cv_text) < 50:
            await update.message.reply_text("⚠️ لم نتمكن من القراءة. أرسل نص.")
            return
        
        order_id = create_order(user.id, user.username, cv_text)
        context.user_data["order_id"] = order_id
        
        keyboard = [
            [InlineKeyboardButton("💎 USDT/BNB مباشر ($3)", callback_data=f"direct_{order_id}")],
            [InlineKeyboardButton("🌐 NOWPayments - 100+ عملة ($5)", callback_data=f"nowpay_{order_id}")],
            [InlineKeyboardButton("💳 PayPal ($3)", url=PAYPAL_LINK)],
        ]
        
        await update.message.reply_text(
            f"✅ **تم استلام سيرتك!**\n\n"
            f"🔢 رقم الطلب: `{order_id}`\n\n"
            f"**اختر طريقة الدفع:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"PDF Error: {e}")
        await update.message.reply_text("⚠️ خطأ. أرسل نص.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("direct_"):
        order_id = data.replace("direct_", "")
        
        msg = f"""💎 **الدفع المباشر - $3**

🔢 رقم الطلب: `{order_id}`

━━━━━━━━━━━━━━━

**USDT (TRC20):**
```
{USDT_TRC20_ADDRESS}
```

**BNB (BEP20):**
```
{BNB_BEP20_ADDRESS}
```

━━━━━━━━━━━━━━━

⚠️ بعد الدفع، أرسل:
• لقطة شاشة
• أو hash التحويل"""

        keyboard = [[InlineKeyboardButton("✅ أرسلت الدفع", callback_data=f"sent_{order_id}")],
                    [InlineKeyboardButton("🔙 رجوع", callback_data=f"back_{order_id}")]]
        
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    elif data.startswith("nowpay_"):
        order_id = data.replace("nowpay_", "")
        
        await query.edit_message_text("⏳ جاري إنشاء رابط الدفع...")
        
        invoice = await create_nowpayments_invoice(order_id, NOWPAYMENTS_PRICE)
        
        if invoice and invoice.get("invoice_url"):
            update_order_payment(order_id, "nowpayments", invoice.get("id"), NOWPAYMENTS_PRICE)
            
            keyboard = [
                [InlineKeyboardButton("💳 افتح صفحة الدفع", url=invoice["invoice_url"])],
                [InlineKeyboardButton("🔄 تحقق من الدفع", callback_data=f"check_{order_id}")],
                [InlineKeyboardButton("🔙 رجوع", callback_data=f"back_{order_id}")]
            ]
            
            await query.edit_message_text(
                f"🌐 **NOWPayments - $5**\n\n"
                f"🔢 رقم الطلب: `{order_id}`\n\n"
                f"ادفع بأي عملة: USDT, BTC, ETH, BNB, LTC...\n\n"
                f"اضغط الزر لفتح صفحة الدفع 👇",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data=f"back_{order_id}")]]
            await query.edit_message_text(
                "⚠️ خطأ في إنشاء الفاتورة.\n\nاستخدم الدفع المباشر أو PayPal.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif data.startswith("check_"):
        order_id = data.replace("check_", "")
        order = get_order(order_id)
        
        if not order:
            await query.answer("❌ الطلب غير موجود", show_alert=True)
            return
        
        if order["payment_status"] == "paid":
            await query.answer("✅ تم معالجة الطلب", show_alert=True)
            return
        
        if order["payment_id"]:
            status = await check_nowpayments_status(order["payment_id"])
            
            if status in ["finished", "confirmed", "sending"]:
                await query.edit_message_text("✅ تم تأكيد الدفع!\n\n⏳ جاري التحليل...")
                
                mark_order_paid(order_id)
                result = await analyze_cv_with_ai(order["cv_text"])
                
                if result:
                    await context.bot.send_message(order["user_id"],
                        f"📊 **التحليل:**\n\n{result['analysis']}", parse_mode="Markdown")
                    await context.bot.send_message(order["user_id"],
                        f"✨ **النسخة المحسّنة:**\n\n{result['improved_cv']}", parse_mode="Markdown")
                    await context.bot.send_message(order["user_id"], "✅ تم! شكرًا 🙏")
                return
        
        keyboard = [[InlineKeyboardButton("🔄 تحقق مرة أخرى", callback_data=f"check_{order_id}")]]
        await query.edit_message_text(
            "⏳ لم يتم تأكيد الدفع بعد.\n\nانتظر 1-3 دقائق ثم تحقق مرة أخرى.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("sent_"):
        order_id = data.replace("sent_", "")
        await query.edit_message_text(
            f"📸 **أرسل إثبات الدفع:**\n\n"
            f"• لقطة شاشة\n"
            f"• أو hash التحويل\n\n"
            f"🔢 رقم الطلب: `{order_id}`",
            parse_mode="Markdown"
        )
    
    elif data.startswith("back_"):
        order_id = data.replace("back_", "")
        keyboard = [
            [InlineKeyboardButton("💎 USDT/BNB مباشر ($3)", callback_data=f"direct_{order_id}")],
            [InlineKeyboardButton("🌐 NOWPayments - 100+ عملة ($5)", callback_data=f"nowpay_{order_id}")],
            [InlineKeyboardButton("💳 PayPal ($3)", url=PAYPAL_LINK)],
        ]
        await query.edit_message_text(
            f"🔢 رقم الطلب: `{order_id}`\n\n**اختر طريقة الدفع:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    order_id = get_pending_order(user.id)
    
    if order_id:
        await update.message.reply_text(
            f"✅ تم استلام الإثبات!\n\n🔢 `{order_id}`\n\n⏳ جاري التحقق...",
            parse_mode="Markdown"
        )
        logger.info(f"Payment proof: order {order_id}, user {user.id}")
    else:
        await update.message.reply_text("⚠️ أرسل سيرتك أولاً")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    
    # Check if TX hash
    if len(text) >= 60 and text.replace("0x", "").isalnum():
        order_id = get_pending_order(user.id)
        if order_id:
            await update.message.reply_text(
                f"✅ تم استلام Hash!\n\n🔢 `{order_id}`\n\n⏳ جاري التحقق...",
                parse_mode="Markdown"
            )
            logger.info(f"TX hash: order {order_id}, hash {text[:20]}...")
            return
    
    # Otherwise treat as CV
    await handle_cv(update, context)

# Admin
async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        conn = sqlite3.connect("users.db", check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT order_id, user_id, amount FROM orders WHERE payment_status='pending' ORDER BY created_at DESC LIMIT 10")
        orders = c.fetchall()
        conn.close()
        
        if orders:
            msg = "📋 **الطلبات المعلقة:**\n\n"
            for o in orders:
                msg += f"• `{o[0]}` - ${o[2]}\n"
            msg += "\n`/approve ORDER_ID`"
        else:
            msg = "✅ لا طلبات معلقة"
        await update.message.reply_text(msg, parse_mode="Markdown")
        return
    
    order_id = context.args[0].upper()
    order = get_order(order_id)
    
    if not order:
        await update.message.reply_text("❌ غير موجود")
        return
    
    if order["payment_status"] == "paid":
        await update.message.reply_text("✅ مدفوع مسبقًا")
        return
    
    await update.message.reply_text(f"⏳ معالجة {order['order_id']}...")
    
    mark_order_paid(order["order_id"])
    result = await analyze_cv_with_ai(order["cv_text"])
    
    if result:
        await context.bot.send_message(order["user_id"], "✅ تم تأكيد الدفع!", parse_mode="Markdown")
        await context.bot.send_message(order["user_id"],
            f"📊 **التحليل:**\n\n{result['analysis']}", parse_mode="Markdown")
        await context.bot.send_message(order["user_id"],
            f"✨ **النسخة المحسّنة:**\n\n{result['improved_cv']}", parse_mode="Markdown")
        await context.bot.send_message(order["user_id"], "✅ تم! شكرًا 🙏")
        await update.message.reply_text(f"✅ تم إرسال التحليل")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE payment_status='paid'")
    paid = c.fetchone()[0]
    c.execute("SELECT SUM(amount) FROM orders WHERE payment_status='paid'")
    revenue = c.fetchone()[0] or 0
    conn.close()
    
    await update.message.reply_text(
        f"📊 **الإحصائيات:**\n\n"
        f"📝 الطلبات: {total}\n"
        f"✅ المدفوعة: {paid}\n"
        f"💰 الإيرادات: ${revenue}",
        parse_mode="Markdown"
    )

def main():
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", admin_approve))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("🚀 Bot v5 - All Payment Options!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
