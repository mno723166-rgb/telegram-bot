#!/usr/bin/env python3
"""
🚀 AI Services Bot - Multiple AI Services in One Bot
خدمات AI متعددة - سعر موحد $2
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
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler
)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PAYPAL_LINK = os.getenv("PAYPAL_LINK", "https://paypal.me/mohammedalderei/2")
PRICE = 2

# Wallets
USDT_TRC20 = "TFgQpnv2qVMHMojdjUrrzQ8iVB3fDR2HN9"
BNB_BEP20 = "0x45ed64749a512936d2e7956f84d58f1240e8d2e0"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI()

# Services
SERVICES = {
    "bio": {
        "name": "✍️ بايو احترافي",
        "desc": "بايو انستغرام/تيك توك/لينكدإن جذاب",
        "prompt": "اكتب 5 نسخ مختلفة من بايو احترافي وجذاب لـ {platform} للشخص التالي: {input}. اجعلها قصيرة وجذابة ومؤثرة مع إيموجي مناسبة."
    },
    "content": {
        "name": "💡 أفكار محتوى",
        "desc": "30 فكرة محتوى فيروسي لمنشئي المحتوى",
        "prompt": "اقترح 30 فكرة محتوى فيروسي وجذاب لمنشئ محتوى في مجال: {input}. اجعل الأفكار متنوعة بين فيديوهات قصيرة، ريلز، تيك توك، وبوستات. أضف وصف قصير لكل فكرة."
    },
    "caption": {
        "name": "📝 كابشن جذاب",
        "desc": "10 كابشنات احترافية لمنشوراتك",
        "prompt": "اكتب 10 كابشنات مختلفة وجذابة لمنشور عن: {input}. اجعلها متنوعة بين الفكاهية والملهمة والتفاعلية مع هاشتاقات مناسبة."
    },
    "reply": {
        "name": "💬 ردود ذكية",
        "desc": "ردود احترافية للتعليقات والرسائل",
        "prompt": "اكتب 10 ردود مختلفة واحترافية على هذه الرسالة/التعليق: {input}. اجعل الردود متنوعة بين الودية والمهنية والذكية."
    },
    "name": {
        "name": "🏷️ اسم تجاري/يوزرنيم",
        "desc": "أسماء إبداعية لمشروعك أو حسابك",
        "prompt": "اقترح 20 اسم إبداعي ومميز لـ: {input}. اجعلها سهلة النطق والتذكر ومتاحة كيوزرنيم. قدم أسماء عربية وإنجليزية."
    },
    "email": {
        "name": "📧 إيميل احترافي",
        "desc": "رسائل بريد إلكتروني مقنعة",
        "prompt": "اكتب 3 نسخ مختلفة من إيميل احترافي لـ: {input}. اجعلها مقنعة ومهنية مع موضوع جذاب."
    },
    "ad": {
        "name": "📢 نص إعلاني",
        "desc": "نصوص إعلانية تبيع",
        "prompt": "اكتب 5 نصوص إعلانية مختلفة لـ: {input}. استخدم تقنيات الإقناع والـ AIDA. اجعلها قصيرة وجذابة ومحفزة للشراء."
    },
    "hashtag": {
        "name": "#️⃣ هاشتاقات",
        "desc": "هاشتاقات مستهدفة لزيادة الوصول",
        "prompt": "اقترح 50 هاشتاق مناسب ومستهدف لمحتوى عن: {input}. قسمها إلى: شائعة، متوسطة، ومتخصصة. بالعربي والإنجليزي."
    }
}

# Database
def init_db():
    conn = sqlite3.connect("services.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY, user_id INTEGER, username TEXT,
        service TEXT, input_text TEXT, payment_status TEXT DEFAULT 'pending',
        created_at TEXT, paid_at TEXT
    )""")
    conn.commit()
    conn.close()

def create_order(user_id, username, service, input_text):
    order_id = secrets.token_hex(4).upper()
    conn = sqlite3.connect("services.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)",
              (order_id, user_id, username, service, input_text, 'pending', datetime.now().isoformat(), None))
    conn.commit()
    conn.close()
    return order_id

def get_order(order_id):
    conn = sqlite3.connect("services.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE order_id=? OR order_id LIKE ?", (order_id, f"{order_id}%"))
    r = c.fetchone()
    conn.close()
    return {"order_id": r[0], "user_id": r[1], "username": r[2], "service": r[3],
            "input_text": r[4], "payment_status": r[5]} if r else None

def mark_paid(order_id):
    conn = sqlite3.connect("services.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("UPDATE orders SET payment_status='paid', paid_at=? WHERE order_id=?",
              (datetime.now().isoformat(), order_id))
    conn.commit()
    conn.close()

def get_pending(user_id):
    conn = sqlite3.connect("services.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT order_id FROM orders WHERE user_id=? AND payment_status='pending' ORDER BY created_at DESC LIMIT 1", (user_id,))
    r = c.fetchone()
    conn.close()
    return r[0] if r else None

# AI
async def generate_content(service_key, input_text, platform=""):
    service = SERVICES[service_key]
    prompt = service["prompt"].format(input=input_text, platform=platform)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return None

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for key, svc in SERVICES.items():
        keyboard.append([InlineKeyboardButton(f"{svc['name']} - ${PRICE}", callback_data=f"svc_{key}")])
    
    await update.message.reply_text(
        "🤖 **خدمات AI فورية**\n\n"
        f"💰 كل خدمة بـ **${PRICE} فقط**\n"
        "⚡ النتيجة خلال 60 ثانية\n\n"
        "**اختر الخدمة:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("svc_"):
        service_key = data.replace("svc_", "")
        context.user_data["service"] = service_key
        service = SERVICES[service_key]
        
        if service_key == "bio":
            keyboard = [
                [InlineKeyboardButton("Instagram", callback_data="platform_Instagram")],
                [InlineKeyboardButton("TikTok", callback_data="platform_TikTok")],
                [InlineKeyboardButton("LinkedIn", callback_data="platform_LinkedIn")],
                [InlineKeyboardButton("Twitter/X", callback_data="platform_Twitter")],
            ]
            await query.edit_message_text(
                f"**{service['name']}**\n\nاختر المنصة:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"**{service['name']}**\n\n{service['desc']}\n\n"
                f"📝 أرسل التفاصيل المطلوبة:",
                parse_mode="Markdown"
            )
    
    elif data.startswith("platform_"):
        platform = data.replace("platform_", "")
        context.user_data["platform"] = platform
        await query.edit_message_text(
            f"**بايو {platform}**\n\n"
            "📝 أرسل معلومات عنك:\n"
            "• ماذا تفعل؟\n"
            "• ما تخصصك؟\n"
            "• ما الذي يميزك؟",
            parse_mode="Markdown"
        )
    
    elif data.startswith("pay_"):
        order_id = data.replace("pay_", "")
        
        msg = f"""💳 **الدفع - ${PRICE}**

🔢 رقم الطلب: `{order_id}`

━━━━━━━━━━━━━━━

**USDT (TRC20):**
`{USDT_TRC20}`

**BNB (BEP20):**
`{BNB_BEP20}`

━━━━━━━━━━━━━━━

⚠️ بعد الدفع أرسل:
• لقطة شاشة
• أو hash التحويل"""

        keyboard = [
            [InlineKeyboardButton("💳 PayPal", url=PAYPAL_LINK)],
            [InlineKeyboardButton("✅ دفعت", callback_data=f"paid_{order_id}")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    elif data.startswith("paid_"):
        order_id = data.replace("paid_", "")
        await query.edit_message_text(
            f"📸 أرسل إثبات الدفع\n\n🔢 `{order_id}`",
            parse_mode="Markdown"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    
    # Check if TX hash
    if len(text) >= 60 and text.replace("0x", "").isalnum():
        order_id = get_pending(user.id)
        if order_id:
            await update.message.reply_text(f"✅ تم استلام Hash!\n🔢 `{order_id}`\n⏳ جاري التحقق...", parse_mode="Markdown")
            logger.info(f"TX: {order_id} - {text[:20]}")
            return
    
    # Check if service selected
    service_key = context.user_data.get("service")
    if not service_key:
        await start(update, context)
        return
    
    platform = context.user_data.get("platform", "")
    order_id = create_order(user.id, user.username, service_key, text)
    context.user_data["order_id"] = order_id
    
    keyboard = [[InlineKeyboardButton(f"💳 ادفع ${PRICE} واحصل على النتيجة", callback_data=f"pay_{order_id}")]]
    
    await update.message.reply_text(
        f"✅ تم!\n\n🔢 رقم الطلب: `{order_id}`\n\n"
        f"اضغط للدفع والحصول على النتيجة فورًا 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Clear service selection
    context.user_data.pop("service", None)
    context.user_data.pop("platform", None)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    order_id = get_pending(user.id)
    if order_id:
        await update.message.reply_text(f"✅ تم استلام الإثبات!\n🔢 `{order_id}`\n⏳ جاري التحقق...", parse_mode="Markdown")
        logger.info(f"Photo proof: {order_id} from {user.id}")

# Admin
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        conn = sqlite3.connect("services.db", check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT order_id, service, user_id FROM orders WHERE payment_status='pending' ORDER BY created_at DESC LIMIT 15")
        orders = c.fetchall()
        conn.close()
        
        if orders:
            msg = "📋 **الطلبات:**\n\n"
            for o in orders:
                msg += f"• `{o[0]}` - {SERVICES.get(o[1], {}).get('name', o[1])}\n"
            msg += "\n`/approve ID`"
        else:
            msg = "✅ لا طلبات"
        await update.message.reply_text(msg, parse_mode="Markdown")
        return
    
    order_id = context.args[0].upper()
    order = get_order(order_id)
    
    if not order:
        await update.message.reply_text("❌ غير موجود")
        return
    
    if order["payment_status"] == "paid":
        await update.message.reply_text("✅ مدفوع")
        return
    
    await update.message.reply_text(f"⏳ معالجة {order['order_id']}...")
    
    mark_paid(order["order_id"])
    
    platform = ""
    if order["service"] == "bio":
        platform = "Instagram"
    
    result = await generate_content(order["service"], order["input_text"], platform)
    
    if result:
        await context.bot.send_message(order["user_id"], "✅ **تم الدفع!**", parse_mode="Markdown")
        
        # Split if too long
        if len(result) > 4000:
            parts = [result[i:i+4000] for i in range(0, len(result), 4000)]
            for part in parts:
                await context.bot.send_message(order["user_id"], part)
        else:
            await context.bot.send_message(order["user_id"], f"🎁 **النتيجة:**\n\n{result}", parse_mode="Markdown")
        
        await context.bot.send_message(order["user_id"], "✅ شكرًا! شارك البوت مع أصدقائك 🙏")
        await update.message.reply_text("✅ تم الإرسال")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("services.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE payment_status='paid'")
    paid = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(
        f"📊 **الإحصائيات:**\n\n"
        f"📝 الطلبات: {total}\n"
        f"✅ المدفوعة: {paid}\n"
        f"💰 الإيرادات: ${paid * PRICE}",
        parse_mode="Markdown"
    )

def main():
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("🚀 Multi-Service AI Bot Started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
