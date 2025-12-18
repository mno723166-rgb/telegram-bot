#!/usr/bin/env python3
"""
AI Services Bot - Bilingual Version (Arabic/English)
بوت خدمات AI - نسخة ثنائية اللغة
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

# ========== النصوص بلغتين ==========
TEXTS = {
    "ar": {
        "welcome": """🤖 **مرحباً {name}!**

أنا بوت خدمات AI - أقدم لك محتوى احترافي بأسعار تبدأ من **$1 فقط!**

⚡ **النتيجة خلال 60 ثانية**
💎 **جودة احترافية**
🎁 **عينة مجانية متاحة**

━━━━━━━━━━━━━━━
**اختر الخدمة التي تحتاجها:**""",
        "choose_service": "🤖 **اختر الخدمة التي تحتاجها:**\n\n⚡ النتيجة خلال 60 ثانية\n💎 جودة احترافية",
        "free_sample_btn": "🎁 جرب مجاناً!",
        "change_lang_btn": "🌐 English",
        "back_btn": "🔙 رجوع",
        "free_used": "⚠️ لقد استخدمت العينة المجانية من قبل.\n\nاختر خدمة من القائمة للحصول على النسخة الكاملة!",
        "free_prompt": "🎁 **عينة مجانية!**\n\nأرسل مجالك أو نوع عملك وسأعطيك:\n• فكرة محتوى واحدة\n• كابشن قصير\n• 5 هاشتاقات\n\n✏️ **أرسل مجالك الآن:**",
        "generating": "⏳ جاري إنشاء العينة المجانية...",
        "free_result": "🎁 **عينتك المجانية:**\n\n{result}\n\n━━━━━━━━━━━━━━━\n✨ **أعجبتك النتيجة؟**\nاحصل على النسخة الكاملة بأسعار تبدأ من $1!",
        "order_now_btn": "🛒 اطلب الآن",
        "price": "السعر",
        "service": "الخدمة",
        "order_id": "رقم الطلب",
        "order_received": "✅ **تم استلام طلبك!**",
        "choose_payment": "**اختر طريقة الدفع:**",
        "usdt_cheapest": "💎 **USDT (TRC20)** - الأرخص",
        "bnb": "🔶 **BNB (BEP20)**",
        "paypal": "💳 **PayPal**",
        "after_payment": "**بعد الدفع:**\nأرسل لقطة شاشة أو Transaction Hash",
        "paid_btn": "✅ دفعت - أرسل لقطة الشاشة",
        "cancel_btn": "🔙 إلغاء",
        "send_proof": "📸 **أرسل إثبات الدفع:**\n\n• لقطة شاشة للتحويل\n• أو Transaction Hash",
        "proof_received": "✅ **تم استلام إثبات الدفع!**\n\n⏳ جاري المراجعة...\nستستلم النتيجة خلال دقائق قليلة.",
        "default_msg": "👋 مرحباً!\n\nاضغط /start لعرض الخدمات المتاحة.",
        "order_ready": "🎉 **طلبك جاهز!**",
        "thanks": "✨ شكراً لاستخدامك خدماتنا!\n🔄 للطلب مرة أخرى: /start",
        "error": "⚠️ حدث خطأ. حاول مرة أخرى.",
        "lang_changed": "✅ تم تغيير اللغة إلى العربية",
        "send_info": "✏️ أرسل المعلومات المطلوبة:",
        # تفاصيل الخدمات
        "bio_info": "أرسل: اسمك + مجالك + 3 نقاط تميزك",
        "ideas_info": "أرسل: مجالك + جمهورك المستهدف",
        "captions_info": "أرسل: نوع المحتوى + الأسلوب المفضل",
        "ads_info": "أرسل: المنتج/الخدمة + الجمهور المستهدف + العرض",
        "hashtags_info": "أرسل: مجالك + المنصة (Instagram/TikTok)",
        "names_info": "أرسل: نوع المشروع + الأسلوب المفضل",
        "email_info": "أرسل: الغرض + المستلم + النقاط الرئيسية",
        "replies_info": "أرسل: التعليق السلبي + نوع العمل",
        "script_info": "أرسل: موضوع الفيديو + المدة + الأسلوب",
        "story_info": "أرسل: اسم العلامة + المجال + القيم",
        "bundle_info": "أرسل: اسمك + مجالك + جمهورك المستهدف",
    },
    "en": {
        "welcome": """🤖 **Hello {name}!**

I'm an AI Services Bot - Professional content starting from **$1 only!**

⚡ **Results in 60 seconds**
💎 **Professional quality**
🎁 **Free sample available**

━━━━━━━━━━━━━━━
**Choose the service you need:**""",
        "choose_service": "🤖 **Choose the service you need:**\n\n⚡ Results in 60 seconds\n💎 Professional quality",
        "free_sample_btn": "🎁 Try Free!",
        "change_lang_btn": "🌐 العربية",
        "back_btn": "🔙 Back",
        "free_used": "⚠️ You've already used your free sample.\n\nChoose a service from the menu to get the full version!",
        "free_prompt": "🎁 **Free Sample!**\n\nSend your niche or business type and I'll give you:\n• 1 content idea\n• Short caption\n• 5 hashtags\n\n✏️ **Send your niche now:**",
        "generating": "⏳ Generating your free sample...",
        "free_result": "🎁 **Your Free Sample:**\n\n{result}\n\n━━━━━━━━━━━━━━━\n✨ **Like the result?**\nGet the full version starting from $1!",
        "order_now_btn": "🛒 Order Now",
        "price": "Price",
        "service": "Service",
        "order_id": "Order ID",
        "order_received": "✅ **Order Received!**",
        "choose_payment": "**Choose payment method:**",
        "usdt_cheapest": "💎 **USDT (TRC20)** - Cheapest",
        "bnb": "🔶 **BNB (BEP20)**",
        "paypal": "💳 **PayPal**",
        "after_payment": "**After payment:**\nSend screenshot or Transaction Hash",
        "paid_btn": "✅ I Paid - Send Screenshot",
        "cancel_btn": "🔙 Cancel",
        "send_proof": "📸 **Send payment proof:**\n\n• Transfer screenshot\n• Or Transaction Hash",
        "proof_received": "✅ **Payment proof received!**\n\n⏳ Reviewing...\nYou'll receive the result in a few minutes.",
        "default_msg": "👋 Hello!\n\nPress /start to view available services.",
        "order_ready": "🎉 **Your order is ready!**",
        "thanks": "✨ Thanks for using our services!\n🔄 Order again: /start",
        "error": "⚠️ An error occurred. Please try again.",
        "lang_changed": "✅ Language changed to English",
        "send_info": "✏️ Send the required information:",
        # Service details
        "bio_info": "Send: Your name + niche + 3 unique points",
        "ideas_info": "Send: Your niche + target audience",
        "captions_info": "Send: Content type + preferred style",
        "ads_info": "Send: Product/Service + target audience + offer",
        "hashtags_info": "Send: Your niche + platform (Instagram/TikTok)",
        "names_info": "Send: Project type + preferred style",
        "email_info": "Send: Purpose + recipient + key points",
        "replies_info": "Send: Negative comment + business type",
        "script_info": "Send: Video topic + duration + style",
        "story_info": "Send: Brand name + niche + values",
        "bundle_info": "Send: Your name + niche + target audience",
    }
}

# ========== الخدمات والأسعار ==========
SERVICES = {
    "bio": {
        "name_ar": "✍️ بايو احترافي",
        "name_en": "✍️ Professional Bio",
        "desc_ar": "بايو جذاب لـ Instagram/TikTok/LinkedIn",
        "desc_en": "Attractive bio for Instagram/TikTok/LinkedIn",
        "price": 1.5,
        "emoji": "✍️"
    },
    "ideas": {
        "name_ar": "💡 أفكار محتوى",
        "name_en": "💡 Content Ideas",
        "desc_ar": "30 فكرة محتوى فيروسية لمجالك",
        "desc_en": "30 viral content ideas for your niche",
        "price": 3,
        "emoji": "💡"
    },
    "captions": {
        "name_ar": "📝 كابشنات",
        "name_en": "📝 Captions",
        "desc_ar": "10 كابشنات جذابة لمنشوراتك",
        "desc_en": "10 engaging captions for your posts",
        "price": 2,
        "emoji": "📝"
    },
    "ads": {
        "name_ar": "📢 نص إعلاني",
        "name_en": "📢 Ad Copy",
        "desc_ar": "نص إعلاني مقنع يحقق مبيعات",
        "desc_en": "Persuasive ad copy that drives sales",
        "price": 3,
        "emoji": "📢"
    },
    "hashtags": {
        "name_ar": "#️⃣ هاشتاقات",
        "name_en": "#️⃣ Hashtags",
        "desc_ar": "30 هاشتاق مستهدف لزيادة الوصول",
        "desc_en": "30 targeted hashtags to boost reach",
        "price": 1,
        "emoji": "#️⃣"
    },
    "names": {
        "name_ar": "🏷️ أسماء تجارية",
        "name_en": "🏷️ Brand Names",
        "desc_ar": "10 أسماء إبداعية لمشروعك",
        "desc_en": "10 creative names for your project",
        "price": 2,
        "emoji": "🏷️"
    },
    "email": {
        "name_ar": "📧 إيميل احترافي",
        "name_en": "📧 Professional Email",
        "desc_ar": "إيميل مقنع (تقديم/مبيعات/متابعة)",
        "desc_en": "Persuasive email (pitch/sales/follow-up)",
        "price": 2,
        "emoji": "📧"
    },
    "replies": {
        "name_ar": "💬 ردود ذكية",
        "name_en": "💬 Smart Replies",
        "desc_ar": "5 ردود احترافية على التعليقات السلبية",
        "desc_en": "5 professional replies to negative comments",
        "price": 1.5,
        "emoji": "💬"
    },
    "script": {
        "name_ar": "🎬 سكريبت فيديو",
        "name_en": "🎬 Video Script",
        "desc_ar": "سكريبت فيديو قصير (Reels/TikTok)",
        "desc_en": "Short video script (Reels/TikTok)",
        "price": 3,
        "emoji": "🎬"
    },
    "story": {
        "name_ar": "📖 قصة علامة",
        "name_en": "📖 Brand Story",
        "desc_ar": "قصة مؤثرة لعلامتك التجارية",
        "desc_en": "Compelling story for your brand",
        "price": 4,
        "emoji": "📖"
    },
    "bundle": {
        "name_ar": "🎁 باقة كاملة",
        "name_en": "🎁 Full Bundle",
        "desc_ar": "بايو + 30 فكرة + 10 كابشنات + هاشتاقات",
        "desc_en": "Bio + 30 ideas + 10 captions + hashtags",
        "price": 5,
        "emoji": "🎁"
    }
}

# تخزين بيانات المستخدمين
user_data = {}
orders = {}

def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_user_lang(user_id):
    """الحصول على لغة المستخدم"""
    return user_data.get(user_id, {}).get("lang", "ar")

def get_text(user_id, key, **kwargs):
    """الحصول على النص بلغة المستخدم"""
    lang = get_user_lang(user_id)
    text = TEXTS[lang].get(key, TEXTS["ar"].get(key, key))
    return text.format(**kwargs) if kwargs else text

def get_service_name(service_key, lang):
    """الحصول على اسم الخدمة بلغة المستخدم"""
    service = SERVICES.get(service_key, {})
    return service.get(f"name_{lang}", service.get("name_ar", ""))

def get_service_desc(service_key, lang):
    """الحصول على وصف الخدمة بلغة المستخدم"""
    service = SERVICES.get(service_key, {})
    return service.get(f"desc_{lang}", service.get("desc_ar", ""))

# ========== رسالة الترحيب ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # تحديد اللغة من إعدادات Telegram إذا كان مستخدم جديد
    if user_id not in user_data:
        # محاولة اكتشاف اللغة من Telegram
        lang_code = user.language_code or "ar"
        detected_lang = "en" if lang_code.startswith("en") else "ar"
        user_data[user_id] = {"lang": detected_lang}
    
    lang = get_user_lang(user_id)
    
    welcome_text = get_text(user_id, "welcome", name=user.first_name)
    
    keyboard = build_services_keyboard(user_id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def build_services_keyboard(user_id):
    """بناء لوحة مفاتيح الخدمات"""
    lang = get_user_lang(user_id)
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
    
    # زر العينة المجانية
    keyboard.append([InlineKeyboardButton(
        get_text(user_id, "free_sample_btn"),
        callback_data="free_sample"
    )])
    
    # زر تغيير اللغة
    keyboard.append([InlineKeyboardButton(
        get_text(user_id, "change_lang_btn"),
        callback_data="change_lang"
    )])
    
    return keyboard

# ========== تغيير اللغة ==========
async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    current_lang = get_user_lang(user_id)
    
    # تبديل اللغة
    new_lang = "en" if current_lang == "ar" else "ar"
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["lang"] = new_lang
    
    # إعادة عرض القائمة باللغة الجديدة
    welcome_text = get_text(user_id, "choose_service")
    keyboard = build_services_keyboard(user_id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"{get_text(user_id, 'lang_changed')}\n\n{welcome_text}",
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
    lang = get_user_lang(user_id)
    
    if user_id not in user_data:
        user_data[user_id] = {"lang": lang}
    user_data[user_id]["service"] = service_key
    user_data[user_id]["step"] = "waiting_input"
    
    service_name = get_service_name(service_key, lang)
    service_desc = get_service_desc(service_key, lang)
    
    detail_text = f"""{service['emoji']} **{service_name}**

📋 {service_desc}

💰 **{get_text(user_id, 'price')}: ${service['price']}**

━━━━━━━━━━━━━━━
{get_text(user_id, 'send_info')}

{get_text(user_id, f'{service_key}_info')}"""

    keyboard = [[InlineKeyboardButton(get_text(user_id, "back_btn"), callback_data="back_to_menu")]]
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
    lang = get_user_lang(user_id)
    
    if user_data.get(user_id, {}).get("used_free"):
        await query.edit_message_text(
            get_text(user_id, "free_used"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(get_text(user_id, "back_btn"), callback_data="back_to_menu")
            ]])
        )
        return
    
    if user_id not in user_data:
        user_data[user_id] = {"lang": lang}
    user_data[user_id]["step"] = "free_sample"
    
    await query.edit_message_text(
        get_text(user_id, "free_prompt"),
        parse_mode='Markdown'
    )

# ========== الرجوع للقائمة ==========
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    welcome_text = get_text(user_id, "choose_service")
    keyboard = build_services_keyboard(user_id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ========== معالجة الرسائل ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text if update.message.text else ""
    
    user_info = user_data.get(user_id, {})
    step = user_info.get("step")
    lang = get_user_lang(user_id)
    
    # العينة المجانية
    if step == "free_sample":
        await update.message.reply_text(get_text(user_id, "generating"))
        
        try:
            prompt_lang = "Arabic" if lang == "ar" else "English"
            response = client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{
                    "role": "user",
                    "content": f"""You are a content expert. Niche: {text}
                    
Give me:
1. One innovative content idea (one sentence)
2. Short engaging caption (2 lines)
3. 5 targeted hashtags

Write in {prompt_lang}. Be concise and direct."""
                }],
                max_tokens=300
            )
            
            result = response.choices[0].message.content
            
            user_data[user_id]["used_free"] = True
            user_data[user_id]["step"] = None
            
            await update.message.reply_text(
                get_text(user_id, "free_result", result=result),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(get_text(user_id, "order_now_btn"), callback_data="back_to_menu")
                ]]),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error generating free sample: {e}")
            await update.message.reply_text(get_text(user_id, "error"))
        return
    
    # انتظار معلومات الخدمة
    if step == "waiting_input":
        service_key = user_info.get("service")
        service = SERVICES.get(service_key)
        
        if not service:
            return
        
        order_id = generate_order_id()
        orders[order_id] = {
            "user_id": user_id,
            "service": service_key,
            "input": text,
            "price": service["price"],
            "status": "pending",
            "lang": lang,
            "created": datetime.now().isoformat()
        }
        
        user_data[user_id]["order_id"] = order_id
        user_data[user_id]["step"] = "waiting_payment"
        
        service_name = get_service_name(service_key, lang)
        
        payment_text = f"""{get_text(user_id, 'order_received')}

📋 **{get_text(user_id, 'service')}:** {service_name}
💰 **{get_text(user_id, 'price')}:** ${service['price']}
🔖 **{get_text(user_id, 'order_id')}:** `{order_id}`

━━━━━━━━━━━━━━━
{get_text(user_id, 'choose_payment')}

{get_text(user_id, 'usdt_cheapest')}
`{USDT_ADDRESS}`

{get_text(user_id, 'bnb')}
`{BNB_ADDRESS}`

{get_text(user_id, 'paypal')}
{PAYPAL_LINK}/{service['price']}

━━━━━━━━━━━━━━━
{get_text(user_id, 'after_payment')}"""

        keyboard = [
            [InlineKeyboardButton(get_text(user_id, "paid_btn"), callback_data=f"paid_{order_id}")],
            [InlineKeyboardButton(get_text(user_id, "cancel_btn"), callback_data="back_to_menu")]
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
        
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin_id,
                    f"💰 **New Payment Request!**\n\n"
                    f"🔖 Order: `{order_id}`\n"
                    f"👤 User: {update.effective_user.first_name}\n"
                    f"📋 Service: {get_service_name(orders[order_id]['service'], 'en')}\n"
                    f"💵 Amount: ${orders[order_id]['price']}\n\n"
                    f"Approve: `/approve {order_id}`",
                    parse_mode='Markdown'
                )
                
                if update.message.photo:
                    await context.bot.send_photo(admin_id, update.message.photo[-1].file_id)
                elif update.message.document:
                    await context.bot.send_document(admin_id, update.message.document.file_id)
            except Exception as e:
                logger.error(f"Error notifying admin: {e}")
        
        await update.message.reply_text(
            get_text(user_id, "proof_received"),
            parse_mode='Markdown'
        )
        
        user_data[user_id]["step"] = None
        return
    
    await update.message.reply_text(get_text(user_id, "default_msg"))

# ========== تأكيد الدفع ==========
async def confirm_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.replace("paid_", "")
    user_id = query.from_user.id
    
    user_data[user_id]["step"] = "waiting_proof"
    
    await query.edit_message_text(
        f"{get_text(user_id, 'send_proof')}\n\n🔖 {get_text(user_id, 'order_id')}: `{order_id}`",
        parse_mode='Markdown'
    )

# ========== أمر الموافقة (للمشرف) ==========
async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    if not context.args:
        pending = [f"`{oid}` - ${o['price']}" for oid, o in orders.items() if o['status'] == 'pending']
        if pending:
            await update.message.reply_text(
                "📋 **Pending Orders:**\n\n" + "\n".join(pending) +
                "\n\nApprove: `/approve ORDER_ID`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("✅ No pending orders.")
        return
    
    order_id = context.args[0].upper()
    
    if order_id not in orders:
        await update.message.reply_text("❌ Order not found.")
        return
    
    order = orders[order_id]
    
    if order['status'] == 'completed':
        await update.message.reply_text("✅ Order already completed.")
        return
    
    await update.message.reply_text(f"⏳ Processing order {order_id}...")
    
    service_key = order['service']
    service = SERVICES[service_key]
    user_input = order['input']
    order_lang = order.get('lang', 'ar')
    
    try:
        prompt = get_service_prompt(service_key, user_input, order_lang)
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500
        )
        
        result = response.choices[0].message.content
        service_name = get_service_name(service_key, order_lang)
        
        # استخدام لغة الطلب للرسالة
        if order_lang == "ar":
            msg = f"🎉 **طلبك جاهز!**\n\n📋 **{service_name}**\n\n━━━━━━━━━━━━━━━\n\n{result}\n\n━━━━━━━━━━━━━━━\n✨ شكراً لاستخدامك خدماتنا!\n🔄 للطلب مرة أخرى: /start"
        else:
            msg = f"🎉 **Your order is ready!**\n\n📋 **{service_name}**\n\n━━━━━━━━━━━━━━━\n\n{result}\n\n━━━━━━━━━━━━━━━\n✨ Thanks for using our services!\n🔄 Order again: /start"
        
        await context.bot.send_message(order['user_id'], msg, parse_mode='Markdown')
        
        order['status'] = 'completed'
        await update.message.reply_text(f"✅ Result sent! (Order: {order_id})")
        
    except Exception as e:
        logger.error(f"Error executing order: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

def get_service_prompt(service_key, user_input, lang):
    """إنشاء البرومبت المناسب لكل خدمة"""
    lang_name = "Arabic" if lang == "ar" else "English"
    
    prompts = {
        "bio": f"""You are a bio writing expert. Write a professional and attractive bio based on:
{user_input}

Write 3 different versions:
1. Formal and professional
2. Friendly and personal
3. Creative and unique

Each bio should be 150 characters or less. Write in {lang_name}.""",

        "ideas": f"""You are a content expert. Give me 30 viral content ideas for:
{user_input}

Divide them into:
- 10 educational ideas
- 10 entertaining ideas
- 10 interactive ideas

Write in {lang_name}. Each idea on one line.""",

        "captions": f"""You are a professional content writer. Write 10 engaging captions for:
{user_input}

Each caption should:
- Hook from the first line
- Include a CTA
- Be platform-appropriate

Write in {lang_name}.""",

        "ads": f"""You are a professional copywriter. Write persuasive ad copy for:
{user_input}

Write:
1. Catchy Headline
2. Main Body
3. Call to Action (CTA)

Use persuasion techniques. Write in {lang_name}.""",

        "hashtags": f"""You are an SEO and social media expert. Give me 30 targeted hashtags for:
{user_input}

Divide them:
- 10 large hashtags (millions)
- 10 medium hashtags (thousands)
- 10 small hashtags (hundreds)

Write hashtags in both {lang_name} and English.""",

        "names": f"""You are a branding expert. Give me 10 creative brand names for:
{user_input}

For each name:
- The name
- Meaning/reason
- Potential domain availability

Write in {lang_name}.""",

        "email": f"""You are a professional email writer. Write a professional email for:
{user_input}

Write:
- Catchy Subject Line
- Strong Opening
- Persuasive Body
- Clear CTA
- Professional Closing

Write in {lang_name}.""",

        "replies": f"""You are a customer service expert. Write 5 professional replies to:
{user_input}

Each reply should be:
- Calm and professional
- Problem-solving
- Customer-retaining

Write in {lang_name}.""",

        "script": f"""You are a video script writer. Write a script for:
{user_input}

Write:
- Hook (first 3 seconds)
- Main content
- CTA
- Filming notes

Write in {lang_name}.""",

        "story": f"""You are a professional storyteller. Write a brand story for:
{user_input}

Write a compelling story including:
- Beginning (the problem)
- Journey (the challenge)
- End (the solution)
- The message

Write in {lang_name}.""",

        "bundle": f"""You are a comprehensive content expert. Create a full package for:
{user_input}

Give me:
1. Professional bio (3 versions)
2. 30 content ideas
3. 10 captions
4. 30 hashtags

Write in {lang_name}."""
    }
    
    return prompts.get(service_key, f"Create professional content for: {user_input}. Write in {lang_name}.")

# ========== الإحصائيات ==========
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    total = len(orders)
    completed = len([o for o in orders.values() if o['status'] == 'completed'])
    pending = len([o for o in orders.values() if o['status'] == 'pending'])
    revenue = sum(o['price'] for o in orders.values() if o['status'] == 'completed')
    
    await update.message.reply_text(
        f"📊 **Statistics:**\n\n"
        f"📦 Total Orders: {total}\n"
        f"✅ Completed: {completed}\n"
        f"⏳ Pending: {pending}\n"
        f"💰 Revenue: ${revenue}",
        parse_mode='Markdown'
    )

# ========== تشغيل البوت ==========
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve_order))
    app.add_handler(CommandHandler("stats", stats))
    
    app.add_handler(CallbackQueryHandler(show_service_details, pattern="^service_"))
    app.add_handler(CallbackQueryHandler(free_sample, pattern="^free_sample$"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))
    app.add_handler(CallbackQueryHandler(confirm_paid, pattern="^paid_"))
    app.add_handler(CallbackQueryHandler(change_language, pattern="^change_lang$"))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_message))
    
    logger.info("🚀 Bilingual Bot started! (AR/EN)")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
