#!/usr/bin/env python3
"""
AI Services Bot - Premium Version
تسعيرة مخصصة لكل خدمة
"""

import os
import asyncio
import logging
from datetime import datetime
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from openai import OpenAI

# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/telegram_ai_bot/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# التوكنات
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8533837337:AAEUuNwVb5AFHib3km1DHX_DMZyF7jNU5Qw')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# عناوين الدفع
USDT_ADDRESS = "TFgQpnv2qVMHMojdjUrrzQ8iVB3fDR2HN9"
BNB_ADDRESS = "0x45ed64749a512936d2e7956f84d58f1240e8d2e0"
PAYPAL_LINK = "https://paypal.me/mohammedalderei"

# معرف المشرف
ADMIN_IDS = [507231172]

# OpenAI Client
client = OpenAI()

# ========== الخدمات والأسعار ==========
SERVICES = {
    "bio": {
        "name": "✍️ بايو احترافي",
        "name_en": "Professional Bio",
        "description": "بايو جذاب لـ Instagram/TikTok/LinkedIn",
        "price": 1.5,
        "emoji": "✍️"
    },
    "ideas": {
        "name": "💡 أفكار محتوى",
        "name_en": "Content Ideas",
        "description": "30 فكرة محتوى فيروسية لمجالك",
        "price": 3,
        "emoji": "💡"
    },
    "captions": {
        "name": "📝 كابشنات",
        "name_en": "Captions",
        "description": "10 كابشنات جذابة لمنشوراتك",
        "price": 2,
        "emoji": "📝"
    },
    "ads": {
        "name": "📢 نص إعلاني",
        "name_en": "Ad Copy",
        "description": "نص إعلاني مقنع يحقق مبيعات",
        "price": 3,
        "emoji": "📢"
    },
    "hashtags": {
        "name": "#️⃣ هاشتاقات",
        "name_en": "Hashtags",
        "description": "30 هاشتاق مستهدف لزيادة الوصول",
        "price": 1,
        "emoji": "#️⃣"
    },
    "names": {
        "name": "🏷️ أسماء تجارية",
        "name_en": "Brand Names",
        "description": "10 أسماء إبداعية لمشروعك",
        "price": 2,
        "emoji": "🏷️"
    },
    "email": {
        "name": "📧 إيميل احترافي",
        "name_en": "Professional Email",
        "description": "إيميل مقنع (تقديم/مبيعات/متابعة)",
        "price": 2,
        "emoji": "📧"
    },
    "replies": {
        "name": "💬 ردود ذكية",
        "name_en": "Smart Replies",
        "description": "5 ردود احترافية على التعليقات السلبية",
        "price": 1.5,
        "emoji": "💬"
    },
    "script": {
        "name": "🎬 سكريبت فيديو",
        "name_en": "Video Script",
        "description": "سكريبت فيديو قصير (Reels/TikTok)",
        "price": 3,
        "emoji": "🎬"
    },
    "story": {
        "name": "📖 قصة علامة",
        "name_en": "Brand Story",
        "description": "قصة مؤثرة لعلامتك التجارية",
        "price": 4,
        "emoji": "📖"
    },
    "bundle": {
        "name": "🎁 باقة كاملة",
        "name_en": "Full Bundle",
        "description": "بايو + 30 فكرة + 10 كابشنات + هاشتاقات",
        "price": 5,
        "emoji": "🎁"
    }
}

# تخزين بيانات المستخدمين
user_data = {}
orders = {}

def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# ========== رسالة الترحيب ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    welcome_text = f"""🤖 **مرحباً {user.first_name}!**

أنا بوت خدمات AI - أقدم لك محتوى احترافي بأسعار تبدأ من **$1 فقط!**

⚡ **النتيجة خلال 60 ثانية**
💎 **جودة احترافية**
🎁 **عينة مجانية متاحة**

━━━━━━━━━━━━━━━
**اختر الخدمة التي تحتاجها:**"""

    keyboard = []
    
    # صف الخدمات (2 في كل صف)
    services_list = list(SERVICES.items())
    for i in range(0, len(services_list), 2):
        row = []
        for j in range(2):
            if i + j < len(services_list):
                key, service = services_list[i + j]
                row.append(InlineKeyboardButton(
                    f"{service['emoji']} ${service['price']}",
                    callback_data=f"service_{key}"
                ))
        keyboard.append(row)
    
    # زر العينة المجانية
    keyboard.append([InlineKeyboardButton("🎁 جرب مجاناً!", callback_data="free_sample")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ========== عرض تفاصيل الخدمة ==========
async def show_service_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    service_key = query.data.replace("service_", "")
    service = SERVICES.get(service_key)
    
    if not service:
        return
    
    user_id = query.from_user.id
    user_data[user_id] = {"service": service_key, "step": "waiting_input"}
    
    detail_text = f"""{service['emoji']} **{service['name']}**

📋 {service['description']}

💰 **السعر: ${service['price']}**

━━━━━━━━━━━━━━━
**أرسل المعلومات المطلوبة:**"""

    # تحديد المعلومات المطلوبة حسب الخدمة
    if service_key == "bio":
        detail_text += "\n\n✏️ أرسل: اسمك + مجالك + 3 نقاط تميزك"
    elif service_key == "ideas":
        detail_text += "\n\n✏️ أرسل: مجالك + جمهورك المستهدف"
    elif service_key == "captions":
        detail_text += "\n\n✏️ أرسل: نوع المحتوى + الأسلوب المفضل"
    elif service_key == "ads":
        detail_text += "\n\n✏️ أرسل: المنتج/الخدمة + الجمهور المستهدف + العرض"
    elif service_key == "hashtags":
        detail_text += "\n\n✏️ أرسل: مجالك + المنصة (Instagram/TikTok)"
    elif service_key == "names":
        detail_text += "\n\n✏️ أرسل: نوع المشروع + الأسلوب المفضل"
    elif service_key == "email":
        detail_text += "\n\n✏️ أرسل: الغرض + المستلم + النقاط الرئيسية"
    elif service_key == "replies":
        detail_text += "\n\n✏️ أرسل: التعليق السلبي + نوع العمل"
    elif service_key == "script":
        detail_text += "\n\n✏️ أرسل: موضوع الفيديو + المدة + الأسلوب"
    elif service_key == "story":
        detail_text += "\n\n✏️ أرسل: اسم العلامة + المجال + القيم"
    elif service_key == "bundle":
        detail_text += "\n\n✏️ أرسل: اسمك + مجالك + جمهورك المستهدف"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        detail_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ========== العينة المجانية ==========
async def free_sample(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # التحقق من استخدام العينة المجانية
    if user_data.get(user_id, {}).get("used_free"):
        await query.edit_message_text(
            "⚠️ لقد استخدمت العينة المجانية من قبل.\n\n"
            "اختر خدمة من القائمة للحصول على النسخة الكاملة!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_menu")
            ]])
        )
        return
    
    user_data[user_id] = {"step": "free_sample"}
    
    await query.edit_message_text(
        "🎁 **عينة مجانية!**\n\n"
        "أرسل مجالك أو نوع عملك وسأعطيك:\n"
        "• فكرة محتوى واحدة\n"
        "• كابشن قصير\n"
        "• 5 هاشتاقات\n\n"
        "✏️ **أرسل مجالك الآن:**",
        parse_mode='Markdown'
    )

# ========== الرجوع للقائمة ==========
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # إعادة عرض القائمة الرئيسية
    welcome_text = """🤖 **اختر الخدمة التي تحتاجها:**

⚡ النتيجة خلال 60 ثانية
💎 جودة احترافية"""

    keyboard = []
    services_list = list(SERVICES.items())
    for i in range(0, len(services_list), 2):
        row = []
        for j in range(2):
            if i + j < len(services_list):
                key, service = services_list[i + j]
                row.append(InlineKeyboardButton(
                    f"{service['emoji']} ${service['price']}",
                    callback_data=f"service_{key}"
                ))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🎁 جرب مجاناً!", callback_data="free_sample")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ========== معالجة الرسائل ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    user_info = user_data.get(user_id, {})
    step = user_info.get("step")
    
    # العينة المجانية
    if step == "free_sample":
        await update.message.reply_text("⏳ جاري إنشاء العينة المجانية...")
        
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{
                    "role": "user",
                    "content": f"""أنت خبير محتوى. المجال: {text}
                    
أعطني:
1. فكرة محتوى واحدة مبتكرة (جملة واحدة)
2. كابشن قصير جذاب (سطرين)
3. 5 هاشتاقات مستهدفة

اكتب بالعربية. كن مختصراً ومباشراً."""
                }],
                max_tokens=300
            )
            
            result = response.choices[0].message.content
            
            user_data[user_id]["used_free"] = True
            user_data[user_id]["step"] = None
            
            await update.message.reply_text(
                f"🎁 **عينتك المجانية:**\n\n{result}\n\n"
                "━━━━━━━━━━━━━━━\n"
                "✨ **أعجبتك النتيجة؟**\n"
                "احصل على النسخة الكاملة بأسعار تبدأ من $1!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🛒 اطلب الآن", callback_data="back_to_menu")
                ]]),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error generating free sample: {e}")
            await update.message.reply_text("⚠️ حدث خطأ. حاول مرة أخرى.")
        return
    
    # انتظار معلومات الخدمة
    if step == "waiting_input":
        service_key = user_info.get("service")
        service = SERVICES.get(service_key)
        
        if not service:
            return
        
        # حفظ المعلومات وإنشاء طلب
        order_id = generate_order_id()
        orders[order_id] = {
            "user_id": user_id,
            "service": service_key,
            "input": text,
            "price": service["price"],
            "status": "pending",
            "created": datetime.now().isoformat()
        }
        
        user_data[user_id]["order_id"] = order_id
        user_data[user_id]["step"] = "waiting_payment"
        
        # عرض خيارات الدفع
        payment_text = f"""✅ **تم استلام طلبك!**

📋 **الخدمة:** {service['name']}
💰 **السعر:** ${service['price']}
🔖 **رقم الطلب:** `{order_id}`

━━━━━━━━━━━━━━━
**اختر طريقة الدفع:**

💎 **USDT (TRC20)** - الأرخص
`{USDT_ADDRESS}`

🔶 **BNB (BEP20)**
`{BNB_ADDRESS}`

💳 **PayPal**
{PAYPAL_LINK}/{service['price']}

━━━━━━━━━━━━━━━
**بعد الدفع:**
أرسل لقطة شاشة أو Transaction Hash"""

        keyboard = [
            [InlineKeyboardButton("✅ دفعت - أرسل لقطة الشاشة", callback_data=f"paid_{order_id}")],
            [InlineKeyboardButton("🔙 إلغاء", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            payment_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # انتظار إثبات الدفع
    if step == "waiting_proof":
        order_id = user_info.get("order_id")
        
        # إرسال إشعار للمشرف
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin_id,
                    f"💰 **طلب دفع جديد!**\n\n"
                    f"🔖 رقم الطلب: `{order_id}`\n"
                    f"👤 المستخدم: {update.effective_user.first_name}\n"
                    f"📋 الخدمة: {SERVICES[orders[order_id]['service']]['name']}\n"
                    f"💵 المبلغ: ${orders[order_id]['price']}\n\n"
                    f"للموافقة: `/approve {order_id}`",
                    parse_mode='Markdown'
                )
                
                # إرسال الصورة إذا كانت موجودة
                if update.message.photo:
                    await context.bot.send_photo(admin_id, update.message.photo[-1].file_id)
                elif update.message.document:
                    await context.bot.send_document(admin_id, update.message.document.file_id)
            except Exception as e:
                logger.error(f"Error notifying admin: {e}")
        
        await update.message.reply_text(
            "✅ **تم استلام إثبات الدفع!**\n\n"
            "⏳ جاري المراجعة...\n"
            "ستستلم النتيجة خلال دقائق قليلة.",
            parse_mode='Markdown'
        )
        
        user_data[user_id]["step"] = None
        return
    
    # رسالة افتراضية
    await update.message.reply_text(
        "👋 مرحباً!\n\nاضغط /start لعرض الخدمات المتاحة."
    )

# ========== تأكيد الدفع ==========
async def confirm_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.replace("paid_", "")
    user_id = query.from_user.id
    
    user_data[user_id]["step"] = "waiting_proof"
    
    await query.edit_message_text(
        "📸 **أرسل إثبات الدفع:**\n\n"
        "• لقطة شاشة للتحويل\n"
        "• أو Transaction Hash\n\n"
        f"🔖 رقم طلبك: `{order_id}`",
        parse_mode='Markdown'
    )

# ========== أمر الموافقة (للمشرف) ==========
async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    if not context.args:
        # عرض الطلبات المعلقة
        pending = [f"`{oid}` - ${o['price']}" for oid, o in orders.items() if o['status'] == 'pending']
        if pending:
            await update.message.reply_text(
                "📋 **الطلبات المعلقة:**\n\n" + "\n".join(pending) +
                "\n\nللموافقة: `/approve ORDER_ID`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("✅ لا توجد طلبات معلقة.")
        return
    
    order_id = context.args[0].upper()
    
    if order_id not in orders:
        await update.message.reply_text("❌ رقم الطلب غير موجود.")
        return
    
    order = orders[order_id]
    
    if order['status'] == 'completed':
        await update.message.reply_text("✅ هذا الطلب مكتمل بالفعل.")
        return
    
    # تنفيذ الخدمة
    await update.message.reply_text(f"⏳ جاري تنفيذ الطلب {order_id}...")
    
    service_key = order['service']
    service = SERVICES[service_key]
    user_input = order['input']
    
    try:
        # إنشاء المحتوى
        prompt = get_service_prompt(service_key, user_input)
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500
        )
        
        result = response.choices[0].message.content
        
        # إرسال النتيجة للمستخدم
        await context.bot.send_message(
            order['user_id'],
            f"🎉 **طلبك جاهز!**\n\n"
            f"📋 **{service['name']}**\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"{result}\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"✨ شكراً لاستخدامك خدماتنا!\n"
            f"🔄 للطلب مرة أخرى: /start",
            parse_mode='Markdown'
        )
        
        order['status'] = 'completed'
        
        await update.message.reply_text(f"✅ تم إرسال النتيجة للمستخدم! (الطلب: {order_id})")
        
    except Exception as e:
        logger.error(f"Error executing order: {e}")
        await update.message.reply_text(f"❌ خطأ في تنفيذ الطلب: {e}")

def get_service_prompt(service_key, user_input):
    """إنشاء البرومبت المناسب لكل خدمة"""
    
    prompts = {
        "bio": f"""أنت خبير في كتابة البايو. اكتب بايو احترافي وجذاب بناءً على:
{user_input}

اكتب 3 نسخ مختلفة:
1. رسمي واحترافي
2. ودود وشخصي
3. إبداعي ومميز

كل بايو يجب أن يكون 150 حرف أو أقل. اكتب بالعربية.""",

        "ideas": f"""أنت خبير محتوى. أعطني 30 فكرة محتوى فيروسية لـ:
{user_input}

قسّمها إلى:
- 10 أفكار تعليمية
- 10 أفكار ترفيهية
- 10 أفكار تفاعلية

اكتب بالعربية. كل فكرة في سطر واحد.""",

        "captions": f"""أنت كاتب محتوى محترف. اكتب 10 كابشنات جذابة لـ:
{user_input}

كل كابشن يجب أن يكون:
- جذاب من أول سطر
- يحتوي على CTA
- مناسب للمنصة

اكتب بالعربية.""",

        "ads": f"""أنت copywriter محترف. اكتب نص إعلاني مقنع لـ:
{user_input}

اكتب:
1. عنوان جذاب (Headline)
2. النص الرئيسي (Body)
3. دعوة للعمل (CTA)

استخدم تقنيات الإقناع. اكتب بالعربية.""",

        "hashtags": f"""أنت خبير SEO ومنصات التواصل. أعطني 30 هاشتاق مستهدف لـ:
{user_input}

قسّمها:
- 10 هاشتاقات كبيرة (ملايين)
- 10 هاشتاقات متوسطة (آلاف)
- 10 هاشتاقات صغيرة (مئات)

اكتب الهاشتاقات بالعربية والإنجليزية.""",

        "names": f"""أنت خبير branding. أعطني 10 أسماء تجارية إبداعية لـ:
{user_input}

لكل اسم:
- الاسم
- المعنى/السبب
- توفر الدومين المحتمل

اكتب بالعربية.""",

        "email": f"""أنت كاتب إيميلات محترف. اكتب إيميل احترافي لـ:
{user_input}

اكتب:
- Subject Line جذاب
- Opening قوي
- Body مقنع
- CTA واضح
- Closing احترافي

اكتب بالعربية.""",

        "replies": f"""أنت خبير خدمة عملاء. اكتب 5 ردود احترافية على:
{user_input}

كل رد يجب أن يكون:
- هادئ ومحترف
- يحل المشكلة
- يحافظ على العميل

اكتب بالعربية.""",

        "script": f"""أنت كاتب سكريبتات فيديو. اكتب سكريبت لـ:
{user_input}

اكتب:
- Hook (أول 3 ثواني)
- المحتوى الرئيسي
- CTA
- ملاحظات للتصوير

اكتب بالعربية.""",

        "story": f"""أنت storyteller محترف. اكتب قصة علامة تجارية لـ:
{user_input}

اكتب قصة مؤثرة تتضمن:
- البداية (المشكلة)
- الرحلة (التحدي)
- النهاية (الحل)
- الرسالة

اكتب بالعربية.""",

        "bundle": f"""أنت خبير محتوى شامل. أنشئ حزمة كاملة لـ:
{user_input}

أعطني:
1. بايو احترافي (3 نسخ)
2. 30 فكرة محتوى
3. 10 كابشنات
4. 30 هاشتاق

اكتب بالعربية."""
    }
    
    return prompts.get(service_key, f"أنشئ محتوى احترافي لـ: {user_input}")

# ========== الإحصائيات ==========
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    total = len(orders)
    completed = len([o for o in orders.values() if o['status'] == 'completed'])
    pending = len([o for o in orders.values() if o['status'] == 'pending'])
    revenue = sum(o['price'] for o in orders.values() if o['status'] == 'completed')
    
    await update.message.reply_text(
        f"📊 **الإحصائيات:**\n\n"
        f"📦 إجمالي الطلبات: {total}\n"
        f"✅ مكتملة: {completed}\n"
        f"⏳ معلقة: {pending}\n"
        f"💰 الإيرادات: ${revenue}",
        parse_mode='Markdown'
    )

# ========== تشغيل البوت ==========
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve_order))
    app.add_handler(CommandHandler("stats", stats))
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(show_service_details, pattern="^service_"))
    app.add_handler(CallbackQueryHandler(free_sample, pattern="^free_sample$"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))
    app.add_handler(CallbackQueryHandler(confirm_paid, pattern="^paid_"))
    
    # الرسائل
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_message))
    
    logger.info("🚀 Premium Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
