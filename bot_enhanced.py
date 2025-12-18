#!/usr/bin/env python3
"""
Enhanced AI Services Bot - Optimized for Sales
Features:
- Urgency messaging
- Social proof
- Free sample to hook users
- Multiple payment options
- Referral system
"""

import os
import asyncio
import logging
import random
import string
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from openai import OpenAI

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('/home/ubuntu/telegram_ai_bot/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8533837337:AAEUuNwVb5AFHib3km1DHX_DMZyF7jNU5Qw')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]

# Payment addresses
USDT_ADDRESS = "TFgQpnv2qVMHMojdjUrrzQ8iVB3fDR2HN9"
BNB_ADDRESS = "0x45ed64749a512936d2e7956f84d58f1240e8d2e0"
PAYPAL_LINK = "https://paypal.me/mohammedalderei"

# Price
PRICE = 2

# OpenAI client
client = OpenAI()

# Storage
user_data = {}
orders = {}
stats = {"views": 0, "started": 0, "samples": 0, "paid": 0, "revenue": 0}

def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Services
SERVICES = {
    "bio": {"name": "✍️ بايو احترافي", "name_en": "Professional Bio", "emoji": "✍️"},
    "ideas": {"name": "💡 30 فكرة محتوى", "name_en": "30 Content Ideas", "emoji": "💡"},
    "caption": {"name": "📝 كابشنات جذابة", "name_en": "Engaging Captions", "emoji": "📝"},
    "reply": {"name": "💬 ردود ذكية", "name_en": "Smart Replies", "emoji": "💬"},
    "brand": {"name": "🏷️ أسماء تجارية", "name_en": "Brand Names", "emoji": "🏷️"},
    "email": {"name": "📧 إيميلات احترافية", "name_en": "Professional Emails", "emoji": "📧"},
    "ad": {"name": "📢 نصوص إعلانية", "name_en": "Ad Copy", "emoji": "📢"},
    "hashtag": {"name": "#️⃣ هاشتاقات", "name_en": "Hashtags", "emoji": "#️⃣"},
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with urgency and social proof"""
    stats["started"] += 1
    user = update.effective_user
    
    # Social proof numbers (dynamic)
    users_today = random.randint(47, 89)
    
    welcome_text = f"""🎯 **مرحباً {user.first_name}!**

🔥 **عرض اليوم فقط: $2 بدلاً من $10!**

✅ {users_today} شخص استخدموا الخدمة اليوم

**خدماتنا:**
✍️ بايو احترافي (Instagram/TikTok/LinkedIn)
💡 30 فكرة محتوى فيروسي
📝 كابشنات جذابة
📢 نصوص إعلانية تبيع
#️⃣ هاشتاقات مستهدفة
🏷️ أسماء تجارية إبداعية
📧 إيميلات احترافية
💬 ردود ذكية

⚡ **النتيجة خلال 60 ثانية!**

🎁 **جرب مجاناً أولاً!**
اضغط الزر أدناه للحصول على عينة مجانية 👇"""

    keyboard = [
        [InlineKeyboardButton("🎁 جرب مجاناً!", callback_data="free_sample")],
        [InlineKeyboardButton("💎 اشتري الآن - $2 فقط!", callback_data="buy_now")],
        [InlineKeyboardButton("📋 قائمة الخدمات", callback_data="services_list")],
    ]
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def free_sample(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Give a free sample to hook the user"""
    query = update.callback_query
    await query.answer()
    stats["samples"] += 1
    
    user_id = query.from_user.id
    
    # Check if user already got free sample
    if user_id in user_data and user_data[user_id].get("got_sample"):
        await query.edit_message_text(
            "⚠️ لقد حصلت على العينة المجانية مسبقاً!\n\n"
            "💎 للحصول على الخدمة الكاملة، اضغط /buy"
        )
        return
    
    await query.edit_message_text("⏳ جاري إنشاء عينة مجانية لك...")
    
    # Generate a short free sample
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a professional content creator. Give a SHORT sample (2-3 lines only) of a professional Instagram bio. Make it impressive but incomplete - hint that the full version has more."},
                {"role": "user", "content": "Create a sample professional bio for a content creator"}
            ],
            max_tokens=100
        )
        sample = response.choices[0].message.content
    except Exception as e:
        sample = "✨ Content Creator | Helping brands grow 📈\n🎯 DM for collabs"
    
    # Mark user as got sample
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["got_sample"] = True
    
    result_text = f"""🎁 **عينتك المجانية:**

{sample}

---

⚡ **هذه مجرد عينة قصيرة!**

النسخة الكاملة تشمل:
✅ 5 خيارات مختلفة
✅ تخصيص حسب مجالك
✅ كلمات مفتاحية محسّنة
✅ دعوة للتفاعل (CTA)

💎 **احصل على النسخة الكاملة الآن - $2 فقط!**"""

    keyboard = [
        [InlineKeyboardButton("💎 اشتري الآن - $2!", callback_data="buy_now")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")],
    ]
    
    await query.message.reply_text(
        result_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show payment options"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    order_id = generate_order_id()
    
    # Store order
    orders[order_id] = {
        "user_id": user_id,
        "status": "pending",
        "created": datetime.now().isoformat()
    }
    
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["current_order"] = order_id
    
    payment_text = f"""💳 **طرق الدفع المتاحة:**

📋 **رقم طلبك:** `{order_id}`
💰 **المبلغ:** $2

---

**1️⃣ USDT (TRC20) - الأسرع:**
```
{USDT_ADDRESS}
```

**2️⃣ BNB (BEP20):**
```
{BNB_ADDRESS}
```

**3️⃣ PayPal:**
{PAYPAL_LINK}/2

---

⚠️ **مهم:** بعد الدفع، اضغط "تأكيد الدفع" وأرسل:
- لقطة شاشة للتحويل
- أو Transaction Hash

✅ ستحصل على الخدمة خلال 60 ثانية من التأكيد!"""

    keyboard = [
        [InlineKeyboardButton("📋 نسخ عنوان USDT", callback_data="copy_usdt")],
        [InlineKeyboardButton("📋 نسخ عنوان BNB", callback_data="copy_bnb")],
        [InlineKeyboardButton("💳 فتح PayPal", url=f"{PAYPAL_LINK}/2")],
        [InlineKeyboardButton("✅ تأكيد الدفع", callback_data=f"confirm_payment_{order_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")],
    ]
    
    await query.edit_message_text(
        payment_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def copy_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send address for easy copying"""
    query = update.callback_query
    await query.answer()
    
    if "usdt" in query.data:
        await query.message.reply_text(f"`{USDT_ADDRESS}`", parse_mode='Markdown')
    elif "bnb" in query.data:
        await query.message.reply_text(f"`{BNB_ADDRESS}`", parse_mode='Markdown')

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment confirmation"""
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.split("_")[-1]
    user_id = query.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["awaiting_proof"] = order_id
    
    await query.edit_message_text(
        f"📤 **أرسل إثبات الدفع الآن:**\n\n"
        f"📋 رقم الطلب: `{order_id}`\n\n"
        f"أرسل:\n"
        f"• لقطة شاشة للتحويل\n"
        f"• أو Transaction Hash\n\n"
        f"⏳ سيتم مراجعة الدفع وتسليم الخدمة خلال دقائق!",
        parse_mode='Markdown'
    )

async def services_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show services list"""
    query = update.callback_query
    await query.answer()
    
    services_text = """📋 **قائمة الخدمات:**

✍️ **بايو احترافي** - $2
بايو مخصص لـ Instagram/TikTok/LinkedIn

💡 **30 فكرة محتوى** - $2
أفكار فيروسية لمجالك

📝 **كابشنات جذابة** - $2
10 كابشنات تزيد التفاعل

📢 **نصوص إعلانية** - $2
نص إعلاني يبيع

#️⃣ **هاشتاقات مستهدفة** - $2
30 هاشتاق لزيادة الوصول

🏷️ **أسماء تجارية** - $2
10 أسماء إبداعية لمشروعك

📧 **إيميلات احترافية** - $2
قوالب إيميل جاهزة

💬 **ردود ذكية** - $2
ردود جاهزة للتعليقات

---

💎 **اختر خدمة واحصل عليها خلال 60 ثانية!**"""

    keyboard = [
        [InlineKeyboardButton("💎 اشتري الآن!", callback_data="buy_now")],
        [InlineKeyboardButton("🎁 جرب مجاناً أولاً", callback_data="free_sample")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")],
    ]
    
    await query.edit_message_text(
        services_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu"""
    query = update.callback_query
    await query.answer()
    
    users_today = random.randint(47, 89)
    
    welcome_text = f"""🎯 **القائمة الرئيسية**

🔥 **عرض اليوم: $2 فقط!**
✅ {users_today} شخص استخدموا الخدمة اليوم

اختر من الخيارات أدناه 👇"""

    keyboard = [
        [InlineKeyboardButton("🎁 جرب مجاناً!", callback_data="free_sample")],
        [InlineKeyboardButton("💎 اشتري الآن - $2!", callback_data="buy_now")],
        [InlineKeyboardButton("📋 قائمة الخدمات", callback_data="services_list")],
    ]
    
    await query.edit_message_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    user_id = update.effective_user.id
    message = update.message
    
    # Check if user is sending payment proof
    if user_id in user_data and user_data[user_id].get("awaiting_proof"):
        order_id = user_data[user_id]["awaiting_proof"]
        
        # Notify admin
        admin_text = f"""💰 **طلب دفع جديد!**

👤 المستخدم: {update.effective_user.first_name} (@{update.effective_user.username or 'N/A'})
🆔 ID: {user_id}
📋 رقم الطلب: {order_id}

للموافقة: `/approve {order_id}`"""
        
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, admin_text, parse_mode='Markdown')
                if message.photo:
                    await context.bot.send_photo(admin_id, message.photo[-1].file_id)
                elif message.text:
                    await context.bot.send_message(admin_id, f"الرسالة: {message.text}")
            except:
                pass
        
        user_data[user_id]["awaiting_proof"] = None
        
        await message.reply_text(
            f"✅ **تم استلام إثبات الدفع!**\n\n"
            f"📋 رقم الطلب: `{order_id}`\n\n"
            f"⏳ جاري المراجعة... ستحصل على الخدمة خلال دقائق!\n\n"
            f"💡 بينما تنتظر، ما هي الخدمة التي تريدها؟\n"
            f"أرسل وصف قصير (مثال: بايو لحساب طبخ)",
            parse_mode='Markdown'
        )
        
        user_data[user_id]["awaiting_request"] = order_id
        return
    
    # Check if user is sending service request
    if user_id in user_data and user_data[user_id].get("awaiting_request"):
        order_id = user_data[user_id]["awaiting_request"]
        orders[order_id]["request"] = message.text
        user_data[user_id]["awaiting_request"] = None
        
        await message.reply_text(
            f"✅ **تم حفظ طلبك!**\n\n"
            f"📝 الطلب: {message.text}\n\n"
            f"⏳ سيتم التسليم فور تأكيد الدفع!"
        )
        return
    
    # Default response
    keyboard = [
        [InlineKeyboardButton("🎁 جرب مجاناً!", callback_data="free_sample")],
        [InlineKeyboardButton("💎 اشتري الآن - $2!", callback_data="buy_now")],
    ]
    
    await message.reply_text(
        "👋 مرحباً!\n\n"
        "اضغط /start للبدء أو اختر من الأزرار أدناه:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to approve payment"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ غير مصرح لك!")
        return
    
    if not context.args:
        # Show pending orders
        pending = [f"• {oid}: User {o['user_id']}" for oid, o in orders.items() if o.get('status') == 'pending']
        if pending:
            await update.message.reply_text(f"📋 **الطلبات المعلقة:**\n\n" + "\n".join(pending), parse_mode='Markdown')
        else:
            await update.message.reply_text("✅ لا توجد طلبات معلقة")
        return
    
    order_id = context.args[0]
    
    if order_id not in orders:
        await update.message.reply_text("❌ رقم الطلب غير موجود!")
        return
    
    order = orders[order_id]
    order["status"] = "approved"
    stats["paid"] += 1
    stats["revenue"] += PRICE
    
    # Get user request
    request = order.get("request", "بايو احترافي")
    
    # Generate content
    await update.message.reply_text(f"⏳ جاري إنشاء المحتوى للطلب {order_id}...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": """You are an expert content creator. Create professional, high-quality content based on the user's request. 
                Provide comprehensive results:
                - If bio: Give 5 different options
                - If ideas: Give 30 unique ideas
                - If captions: Give 10 engaging captions
                - If hashtags: Give 30 targeted hashtags
                - Always be creative and professional
                - Use emojis appropriately
                - Write in Arabic if the request is in Arabic, otherwise in English"""},
                {"role": "user", "content": request}
            ],
            max_tokens=2000
        )
        result = response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        result = "حدث خطأ في إنشاء المحتوى. سيتم التواصل معك قريباً."
    
    # Send to user
    try:
        await context.bot.send_message(
            order["user_id"],
            f"🎉 **تم تأكيد الدفع!**\n\n"
            f"📋 رقم الطلب: `{order_id}`\n\n"
            f"---\n\n"
            f"**نتيجتك:**\n\n{result}\n\n"
            f"---\n\n"
            f"✅ شكراً لاستخدامك خدماتنا!\n"
            f"💡 للطلب مرة أخرى: /start",
            parse_mode='Markdown'
        )
        await update.message.reply_text(f"✅ تم إرسال النتيجة للمستخدم!")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ في الإرسال: {e}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show stats"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ غير مصرح لك!")
        return
    
    await update.message.reply_text(
        f"📊 **الإحصائيات:**\n\n"
        f"👥 بدأوا البوت: {stats['started']}\n"
        f"🎁 طلبوا عينة: {stats['samples']}\n"
        f"💰 دفعوا: {stats['paid']}\n"
        f"💵 الإيرادات: ${stats['revenue']}\n\n"
        f"📋 الطلبات المعلقة: {len([o for o in orders.values() if o.get('status') == 'pending'])}",
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks"""
    query = update.callback_query
    data = query.data
    
    if data == "free_sample":
        await free_sample(update, context)
    elif data == "buy_now":
        await buy_now(update, context)
    elif data == "services_list":
        await services_list(update, context)
    elif data == "main_menu":
        await main_menu(update, context)
    elif data.startswith("copy_"):
        await copy_address(update, context)
    elif data.startswith("confirm_payment_"):
        await confirm_payment(update, context)

def main():
    """Start the bot"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", approve_order))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    logger.info("Enhanced Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
