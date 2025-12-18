#!/usr/bin/env python3
"""
AI Services Bot - Sales Optimized Version
بوت محسّن للمبيعات مع تجربة مستخدم احترافية
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/telegram_ai_bot/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8533837337:AAEUuNwVb5AFHib3km1DHX_DMZyF7jNU5Qw')
client = OpenAI()

# عناوين الدفع
USDT_ADDRESS = "TFgQpnv2qVMHMojdjUrrzQ8iVB3fDR2HN9"
BNB_ADDRESS = "0x45ed64749a512936d2e7956f84d58f1240e8d2e0"
PAYPAL_LINK = "https://paypal.me/mohammedalderei"

ADMIN_IDS = [507231172]

# ========== النصوص بلغتين ==========
TEXTS = {
    "ar": {
        "welcome": """🚀 **مرحباً {name}!**

🔥 **عرض خاص - اليوم فقط!**

أحصل على محتوى AI احترافي بأسعار لا تُصدق!

✅ نتيجة فورية خلال 60 ثانية
✅ جودة احترافية مضمونة
✅ أسعار تبدأ من $1 فقط!

👥 **+{users} مستخدم سعيد**

━━━━━━━━━━━━━━━""",
        "select_category": "📂 **اختر الفئة:**",
        "content_cat": "📱 محتوى سوشيال",
        "business_cat": "💼 أعمال وتسويق",
        "writing_cat": "✍️ كتابة احترافية",
        "bundle_cat": "🎁 باقات مخفضة",
        "free_btn": "🎁 عينة مجانية",
        "lang_btn_en": "🌐 English",
        "lang_btn_ar": "🌐 العربية",
        "back": "🔙 رجوع",
        "order_btn": "🛒 اطلب الآن",
        "popular": "🔥 الأكثر طلباً",
        "discount": "خصم",
        "limited": "⏰ عرض محدود!",
        "users_bought": "👥 {n} شخص اشترى هذه الخدمة",
        "instant": "⚡ تسليم فوري",
        "guarantee": "✅ ضمان الجودة",
        "price_label": "💰 السعر",
        "was_price": "كان",
        "now_price": "الآن",
        "order_received": """✅ **تم استلام طلبك!**

📋 الخدمة: {service}
💰 السعر: ${price}
🔖 رقم الطلب: `{order_id}`

━━━━━━━━━━━━━━━
💳 **ادفع الآن واستلم فوراً:**""",
        "pay_usdt": "💎 USDT (TRC20) - الأسرع",
        "pay_bnb": "🔶 BNB (BEP20)",
        "pay_paypal": "💳 PayPal",
        "copy_address": "📋 انسخ العنوان:",
        "after_pay": "✅ بعد الدفع، أرسل:\n• لقطة شاشة\n• أو Transaction Hash",
        "paid_btn": "✅ دفعت",
        "proof_prompt": "📸 أرسل إثبات الدفع الآن:",
        "proof_received": """✅ **تم استلام الإثبات!**

⏳ جاري التحقق والتنفيذ...
📬 ستستلم النتيجة خلال دقائق!""",
        "generating": "⏳ جاري إنشاء المحتوى بالذكاء الاصطناعي...",
        "result_ready": """🎉 **طلبك جاهز!**

{result}

━━━━━━━━━━━━━━━
⭐ **هل أعجبتك النتيجة؟**
شاركها مع أصدقائك!

🔄 للطلب مرة أخرى: /start""",
        "free_used": "⚠️ استخدمت العينة المجانية.\n\n🛒 اطلب النسخة الكاملة الآن!",
        "free_prompt": """🎁 **عينة مجانية!**

أرسل مجالك وسأعطيك:
• فكرة محتوى
• كابشن قصير
• 5 هاشتاقات

✏️ أرسل مجالك:""",
        "free_result": """🎁 **عينتك المجانية:**

{result}

━━━━━━━━━━━━━━━
🔥 **أعجبتك؟ النسخة الكاملة أفضل 10x!**

احصل على 30 فكرة + 10 كابشنات + 30 هاشتاق بـ $3 فقط!""",
        "error": "⚠️ حدث خطأ. حاول مرة أخرى.",
        "lang_changed": "✅ تم تغيير اللغة",
    },
    "en": {
        "welcome": """🚀 **Hello {name}!**

🔥 **Special Offer - Today Only!**

Get professional AI content at unbelievable prices!

✅ Instant results in 60 seconds
✅ Professional quality guaranteed
✅ Prices starting from $1 only!

👥 **+{users} happy users**

━━━━━━━━━━━━━━━""",
        "select_category": "📂 **Select Category:**",
        "content_cat": "📱 Social Content",
        "business_cat": "💼 Business & Marketing",
        "writing_cat": "✍️ Professional Writing",
        "bundle_cat": "🎁 Discounted Bundles",
        "free_btn": "🎁 Free Sample",
        "lang_btn_en": "🌐 English",
        "lang_btn_ar": "🌐 العربية",
        "back": "🔙 Back",
        "order_btn": "🛒 Order Now",
        "popular": "🔥 Most Popular",
        "discount": "OFF",
        "limited": "⏰ Limited Offer!",
        "users_bought": "👥 {n} people bought this",
        "instant": "⚡ Instant Delivery",
        "guarantee": "✅ Quality Guarantee",
        "price_label": "💰 Price",
        "was_price": "Was",
        "now_price": "Now",
        "order_received": """✅ **Order Received!**

📋 Service: {service}
💰 Price: ${price}
🔖 Order ID: `{order_id}`

━━━━━━━━━━━━━━━
💳 **Pay now and receive instantly:**""",
        "pay_usdt": "💎 USDT (TRC20) - Fastest",
        "pay_bnb": "🔶 BNB (BEP20)",
        "pay_paypal": "💳 PayPal",
        "copy_address": "📋 Copy Address:",
        "after_pay": "✅ After payment, send:\n• Screenshot\n• Or Transaction Hash",
        "paid_btn": "✅ I Paid",
        "proof_prompt": "📸 Send payment proof now:",
        "proof_received": """✅ **Proof Received!**

⏳ Verifying and processing...
📬 You'll receive the result in minutes!""",
        "generating": "⏳ Generating AI content...",
        "result_ready": """🎉 **Your order is ready!**

{result}

━━━━━━━━━━━━━━━
⭐ **Like the result?**
Share it with friends!

🔄 Order again: /start""",
        "free_used": "⚠️ You've used your free sample.\n\n🛒 Order the full version now!",
        "free_prompt": """🎁 **Free Sample!**

Send your niche and I'll give you:
• 1 content idea
• Short caption
• 5 hashtags

✏️ Send your niche:""",
        "free_result": """🎁 **Your Free Sample:**

{result}

━━━━━━━━━━━━━━━
🔥 **Like it? Full version is 10x better!**

Get 30 ideas + 10 captions + 30 hashtags for only $3!""",
        "error": "⚠️ An error occurred. Please try again.",
        "lang_changed": "✅ Language changed",
    }
}

# ========== الخدمات مقسمة بفئات ==========
CATEGORIES = {
    "content": {
        "name_ar": "📱 محتوى سوشيال",
        "name_en": "📱 Social Content",
        "services": ["ideas", "captions", "hashtags", "script"]
    },
    "business": {
        "name_ar": "💼 أعمال وتسويق",
        "name_en": "💼 Business & Marketing",
        "services": ["ads", "names", "email", "story"]
    },
    "writing": {
        "name_ar": "✍️ كتابة احترافية",
        "name_en": "✍️ Professional Writing",
        "services": ["bio", "replies"]
    },
    "bundles": {
        "name_ar": "🎁 باقات مخفضة",
        "name_en": "🎁 Discounted Bundles",
        "services": ["starter", "pro", "ultimate"]
    }
}

SERVICES = {
    # محتوى سوشيال
    "ideas": {
        "name_ar": "💡 30 فكرة محتوى",
        "name_en": "💡 30 Content Ideas",
        "desc_ar": "أفكار فيروسية لمجالك",
        "desc_en": "Viral ideas for your niche",
        "price": 3,
        "old_price": 5,
        "buyers": 847,
        "popular": True
    },
    "captions": {
        "name_ar": "📝 10 كابشنات",
        "name_en": "📝 10 Captions",
        "desc_ar": "كابشنات جذابة ومقنعة",
        "desc_en": "Engaging & persuasive captions",
        "price": 2,
        "old_price": 4,
        "buyers": 623
    },
    "hashtags": {
        "name_ar": "#️⃣ 30 هاشتاق",
        "name_en": "#️⃣ 30 Hashtags",
        "desc_ar": "هاشتاقات مستهدفة للوصول",
        "desc_en": "Targeted hashtags for reach",
        "price": 1,
        "old_price": 2,
        "buyers": 1205
    },
    "script": {
        "name_ar": "🎬 سكريبت فيديو",
        "name_en": "🎬 Video Script",
        "desc_ar": "سكريبت Reels/TikTok",
        "desc_en": "Reels/TikTok script",
        "price": 3,
        "old_price": 5,
        "buyers": 412
    },
    # أعمال وتسويق
    "ads": {
        "name_ar": "📢 نص إعلاني",
        "name_en": "📢 Ad Copy",
        "desc_ar": "إعلان يحقق مبيعات",
        "desc_en": "Sales-driving ad copy",
        "price": 3,
        "old_price": 6,
        "buyers": 534,
        "popular": True
    },
    "names": {
        "name_ar": "🏷️ 10 أسماء تجارية",
        "name_en": "🏷️ 10 Brand Names",
        "desc_ar": "أسماء إبداعية لمشروعك",
        "desc_en": "Creative names for your project",
        "price": 2,
        "old_price": 4,
        "buyers": 389
    },
    "email": {
        "name_ar": "📧 إيميل احترافي",
        "name_en": "📧 Professional Email",
        "desc_ar": "إيميل مقنع",
        "desc_en": "Persuasive email",
        "price": 2,
        "old_price": 3,
        "buyers": 267
    },
    "story": {
        "name_ar": "📖 قصة علامة",
        "name_en": "📖 Brand Story",
        "desc_ar": "قصة مؤثرة لعلامتك",
        "desc_en": "Compelling brand story",
        "price": 4,
        "old_price": 7,
        "buyers": 198
    },
    # كتابة احترافية
    "bio": {
        "name_ar": "✍️ بايو احترافي",
        "name_en": "✍️ Professional Bio",
        "desc_ar": "3 نسخ مختلفة",
        "desc_en": "3 different versions",
        "price": 1.5,
        "old_price": 3,
        "buyers": 956
    },
    "replies": {
        "name_ar": "💬 5 ردود ذكية",
        "name_en": "💬 5 Smart Replies",
        "desc_ar": "ردود على التعليقات السلبية",
        "desc_en": "Replies to negative comments",
        "price": 1.5,
        "old_price": 3,
        "buyers": 321
    },
    # باقات
    "starter": {
        "name_ar": "🌟 باقة المبتدئ",
        "name_en": "🌟 Starter Pack",
        "desc_ar": "بايو + 10 أفكار + 15 هاشتاق",
        "desc_en": "Bio + 10 ideas + 15 hashtags",
        "price": 3,
        "old_price": 6,
        "buyers": 445,
        "bundle": True
    },
    "pro": {
        "name_ar": "⭐ باقة المحترف",
        "name_en": "⭐ Pro Pack",
        "desc_ar": "بايو + 30 فكرة + 10 كابشن + 30 هاشتاق",
        "desc_en": "Bio + 30 ideas + 10 captions + 30 hashtags",
        "price": 5,
        "old_price": 10,
        "buyers": 678,
        "popular": True,
        "bundle": True
    },
    "ultimate": {
        "name_ar": "👑 الباقة الشاملة",
        "name_en": "👑 Ultimate Pack",
        "desc_ar": "كل الخدمات + نص إعلاني + سكريبت",
        "desc_en": "All services + ad copy + script",
        "price": 8,
        "old_price": 18,
        "buyers": 234,
        "bundle": True
    }
}

user_data = {}
orders = {}
total_users = 2847  # رقم وهمي للـ social proof

def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_lang(user_id):
    return user_data.get(user_id, {}).get("lang", "ar")

def txt(user_id, key, **kwargs):
    lang = get_lang(user_id)
    text = TEXTS[lang].get(key, TEXTS["ar"].get(key, key))
    return text.format(**kwargs) if kwargs else text

def svc_name(key, lang):
    return SERVICES[key].get(f"name_{lang}", SERVICES[key].get("name_ar"))

def svc_desc(key, lang):
    return SERVICES[key].get(f"desc_{lang}", SERVICES[key].get("desc_ar"))

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if user_id not in user_data:
        lang_code = user.language_code or "ar"
        detected_lang = "en" if lang_code.startswith("en") else "ar"
        user_data[user_id] = {"lang": detected_lang}
    
    lang = get_lang(user_id)
    
    welcome = txt(user_id, "welcome", name=user.first_name, users=total_users)
    
    keyboard = [
        [InlineKeyboardButton(txt(user_id, "content_cat"), callback_data="cat_content")],
        [InlineKeyboardButton(txt(user_id, "business_cat"), callback_data="cat_business")],
        [InlineKeyboardButton(txt(user_id, "writing_cat"), callback_data="cat_writing")],
        [InlineKeyboardButton(f"🎁 {txt(user_id, 'bundle_cat')} -50%", callback_data="cat_bundles")],
        [InlineKeyboardButton(txt(user_id, "free_btn"), callback_data="free_sample")],
        [InlineKeyboardButton(
            txt(user_id, "lang_btn_en") if lang == "ar" else txt(user_id, "lang_btn_ar"),
            callback_data="change_lang"
        )]
    ]
    
    await update.message.reply_text(
        welcome + "\n\n" + txt(user_id, "select_category"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# ========== عرض الفئة ==========
async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    cat_key = query.data.replace("cat_", "")
    user_id = query.from_user.id
    lang = get_lang(user_id)
    
    category = CATEGORIES.get(cat_key)
    if not category:
        return
    
    cat_name = category.get(f"name_{lang}", category["name_ar"])
    
    keyboard = []
    for svc_key in category["services"]:
        svc = SERVICES[svc_key]
        name = svc_name(svc_key, lang)
        price = svc["price"]
        old_price = svc.get("old_price", price)
        popular = "🔥" if svc.get("popular") else ""
        discount = int((1 - price/old_price) * 100) if old_price > price else 0
        
        btn_text = f"{name} ${price}"
        if discount > 0:
            btn_text += f" (-{discount}%)"
        if popular:
            btn_text = f"{popular} {btn_text}"
        
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"svc_{svc_key}")])
    
    keyboard.append([InlineKeyboardButton(txt(user_id, "back"), callback_data="back_main")])
    
    await query.edit_message_text(
        f"**{cat_name}**\n\n{txt(user_id, 'limited')}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# ========== عرض الخدمة ==========
async def show_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    svc_key = query.data.replace("svc_", "")
    user_id = query.from_user.id
    lang = get_lang(user_id)
    
    svc = SERVICES.get(svc_key)
    if not svc:
        return
    
    user_data[user_id]["service"] = svc_key
    user_data[user_id]["step"] = "waiting_input"
    
    name = svc_name(svc_key, lang)
    desc = svc_desc(svc_key, lang)
    price = svc["price"]
    old_price = svc.get("old_price", price)
    buyers = svc.get("buyers", 100)
    
    discount = int((1 - price/old_price) * 100) if old_price > price else 0
    
    text = f"""**{name}**

📋 {desc}

{txt(user_id, 'users_bought', n=buyers)}

━━━━━━━━━━━━━━━
{txt(user_id, 'price_label')}: ~~${old_price}~~ **${price}** ({discount}% {txt(user_id, 'discount')})

{txt(user_id, 'instant')}
{txt(user_id, 'guarantee')}

━━━━━━━━━━━━━━━
✏️ **أرسل المعلومات المطلوبة:**"""

    if lang == "en":
        text = f"""**{name}**

📋 {desc}

{txt(user_id, 'users_bought', n=buyers)}

━━━━━━━━━━━━━━━
{txt(user_id, 'price_label')}: ~~${old_price}~~ **${price}** ({discount}% {txt(user_id, 'discount')})

{txt(user_id, 'instant')}
{txt(user_id, 'guarantee')}

━━━━━━━━━━━━━━━
✏️ **Send the required information:**"""

    # إضافة تعليمات حسب الخدمة
    instructions = {
        "ar": {
            "ideas": "أرسل: مجالك + جمهورك المستهدف",
            "captions": "أرسل: نوع المحتوى + الأسلوب",
            "hashtags": "أرسل: مجالك + المنصة",
            "script": "أرسل: موضوع الفيديو + المدة",
            "ads": "أرسل: المنتج + الجمهور + العرض",
            "names": "أرسل: نوع المشروع + الأسلوب",
            "email": "أرسل: الغرض + المستلم",
            "story": "أرسل: اسم العلامة + المجال",
            "bio": "أرسل: اسمك + مجالك + نقاط تميزك",
            "replies": "أرسل: التعليق السلبي + نوع عملك",
            "starter": "أرسل: اسمك + مجالك",
            "pro": "أرسل: اسمك + مجالك + جمهورك",
            "ultimate": "أرسل: اسمك + مجالك + جمهورك + منتجك"
        },
        "en": {
            "ideas": "Send: Your niche + target audience",
            "captions": "Send: Content type + style",
            "hashtags": "Send: Your niche + platform",
            "script": "Send: Video topic + duration",
            "ads": "Send: Product + audience + offer",
            "names": "Send: Project type + style",
            "email": "Send: Purpose + recipient",
            "story": "Send: Brand name + niche",
            "bio": "Send: Your name + niche + unique points",
            "replies": "Send: Negative comment + business type",
            "starter": "Send: Your name + niche",
            "pro": "Send: Your name + niche + audience",
            "ultimate": "Send: Your name + niche + audience + product"
        }
    }
    
    text += f"\n\n{instructions[lang].get(svc_key, 'أرسل معلوماتك')}"
    
    keyboard = [[InlineKeyboardButton(txt(user_id, "back"), callback_data="back_main")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# ========== معالجة الرسائل ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text if update.message.text else ""
    
    info = user_data.get(user_id, {})
    step = info.get("step")
    lang = get_lang(user_id)
    
    # العينة المجانية
    if step == "free_sample":
        await update.message.reply_text(txt(user_id, "generating"))
        
        try:
            lang_name = "Arabic" if lang == "ar" else "English"
            response = client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{
                    "role": "user",
                    "content": f"Niche: {text}\n\nGive: 1 content idea, 1 short caption, 5 hashtags. Write in {lang_name}. Be concise."
                }],
                max_tokens=250
            )
            
            result = response.choices[0].message.content
            user_data[user_id]["used_free"] = True
            user_data[user_id]["step"] = None
            
            keyboard = [[InlineKeyboardButton(txt(user_id, "order_btn"), callback_data="back_main")]]
            
            await update.message.reply_text(
                txt(user_id, "free_result", result=result),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text(txt(user_id, "error"))
        return
    
    # انتظار معلومات الخدمة
    if step == "waiting_input":
        svc_key = info.get("service")
        svc = SERVICES.get(svc_key)
        
        if not svc:
            return
        
        order_id = generate_order_id()
        orders[order_id] = {
            "user_id": user_id,
            "service": svc_key,
            "input": text,
            "price": svc["price"],
            "status": "pending",
            "lang": lang,
            "created": datetime.now().isoformat()
        }
        
        user_data[user_id]["order_id"] = order_id
        user_data[user_id]["step"] = "waiting_payment"
        
        name = svc_name(svc_key, lang)
        price = svc["price"]
        
        payment_text = txt(user_id, "order_received", service=name, price=price, order_id=order_id)
        
        payment_text += f"""

{txt(user_id, 'pay_usdt')}
`{USDT_ADDRESS}`

{txt(user_id, 'pay_bnb')}
`{BNB_ADDRESS}`

{txt(user_id, 'pay_paypal')}
{PAYPAL_LINK}/{price}

━━━━━━━━━━━━━━━
{txt(user_id, 'after_pay')}"""

        keyboard = [
            [InlineKeyboardButton(txt(user_id, "paid_btn"), callback_data=f"paid_{order_id}")],
            [InlineKeyboardButton(txt(user_id, "back"), callback_data="back_main")]
        ]
        
        await update.message.reply_text(
            payment_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # انتظار إثبات الدفع
    if step == "waiting_proof":
        order_id = info.get("order_id")
        
        for admin_id in ADMIN_IDS:
            try:
                order = orders.get(order_id, {})
                await context.bot.send_message(
                    admin_id,
                    f"💰 **NEW PAYMENT!**\n\n"
                    f"🔖 Order: `{order_id}`\n"
                    f"👤 User: {update.effective_user.first_name} ({user_id})\n"
                    f"📋 Service: {svc_name(order.get('service', ''), 'en')}\n"
                    f"💵 Amount: ${order.get('price', 0)}\n\n"
                    f"✅ Approve: `/approve {order_id}`",
                    parse_mode='Markdown'
                )
                
                if update.message.photo:
                    await context.bot.send_photo(admin_id, update.message.photo[-1].file_id)
                elif update.message.document:
                    await context.bot.send_document(admin_id, update.message.document.file_id)
            except Exception as e:
                logger.error(f"Admin notify error: {e}")
        
        await update.message.reply_text(txt(user_id, "proof_received"), parse_mode='Markdown')
        user_data[user_id]["step"] = None
        return
    
    # رسالة افتراضية
    await update.message.reply_text("👋 Press /start")

# ========== Callbacks ==========
async def free_sample(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_data.get(user_id, {}).get("used_free"):
        keyboard = [[InlineKeyboardButton(txt(user_id, "order_btn"), callback_data="back_main")]]
        await query.edit_message_text(txt(user_id, "free_used"), reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if user_id not in user_data:
        user_data[user_id] = {"lang": "ar"}
    user_data[user_id]["step"] = "free_sample"
    
    await query.edit_message_text(txt(user_id, "free_prompt"), parse_mode='Markdown')

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang = get_lang(user_id)
    
    keyboard = [
        [InlineKeyboardButton(txt(user_id, "content_cat"), callback_data="cat_content")],
        [InlineKeyboardButton(txt(user_id, "business_cat"), callback_data="cat_business")],
        [InlineKeyboardButton(txt(user_id, "writing_cat"), callback_data="cat_writing")],
        [InlineKeyboardButton(f"🎁 {txt(user_id, 'bundle_cat')} -50%", callback_data="cat_bundles")],
        [InlineKeyboardButton(txt(user_id, "free_btn"), callback_data="free_sample")],
        [InlineKeyboardButton(
            txt(user_id, "lang_btn_en") if lang == "ar" else txt(user_id, "lang_btn_ar"),
            callback_data="change_lang"
        )]
    ]
    
    await query.edit_message_text(
        txt(user_id, "select_category"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    current = get_lang(user_id)
    new_lang = "en" if current == "ar" else "ar"
    
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["lang"] = new_lang
    
    # إعادة عرض القائمة
    keyboard = [
        [InlineKeyboardButton(txt(user_id, "content_cat"), callback_data="cat_content")],
        [InlineKeyboardButton(txt(user_id, "business_cat"), callback_data="cat_business")],
        [InlineKeyboardButton(txt(user_id, "writing_cat"), callback_data="cat_writing")],
        [InlineKeyboardButton(f"🎁 {txt(user_id, 'bundle_cat')} -50%", callback_data="cat_bundles")],
        [InlineKeyboardButton(txt(user_id, "free_btn"), callback_data="free_sample")],
        [InlineKeyboardButton(
            txt(user_id, "lang_btn_en") if new_lang == "ar" else txt(user_id, "lang_btn_ar"),
            callback_data="change_lang"
        )]
    ]
    
    await query.edit_message_text(
        f"{txt(user_id, 'lang_changed')}\n\n{txt(user_id, 'select_category')}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def confirm_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.replace("paid_", "")
    user_id = query.from_user.id
    
    user_data[user_id]["step"] = "waiting_proof"
    user_data[user_id]["order_id"] = order_id
    
    await query.edit_message_text(
        f"{txt(user_id, 'proof_prompt')}\n\n🔖 Order: `{order_id}`",
        parse_mode='Markdown'
    )

# ========== Admin Commands ==========
async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        pending = [f"`{oid}` - ${o['price']}" for oid, o in orders.items() if o['status'] == 'pending']
        msg = "📋 **Pending:**\n\n" + "\n".join(pending) if pending else "✅ No pending orders"
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    order_id = context.args[0].upper()
    
    if order_id not in orders:
        await update.message.reply_text("❌ Order not found")
        return
    
    order = orders[order_id]
    
    if order['status'] == 'completed':
        await update.message.reply_text("✅ Already completed")
        return
    
    await update.message.reply_text(f"⏳ Processing {order_id}...")
    
    try:
        prompt = get_prompt(order['service'], order['input'], order.get('lang', 'ar'))
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        
        await context.bot.send_message(
            order['user_id'],
            txt(order['user_id'], "result_ready", result=result),
            parse_mode='Markdown'
        )
        
        order['status'] = 'completed'
        await update.message.reply_text(f"✅ Sent! ({order_id})")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

def get_prompt(svc_key, user_input, lang):
    lang_name = "Arabic" if lang == "ar" else "English"
    
    prompts = {
        "ideas": f"Give 30 viral content ideas for: {user_input}. Divide: 10 educational, 10 entertaining, 10 interactive. Write in {lang_name}.",
        "captions": f"Write 10 engaging captions for: {user_input}. Each with hook and CTA. Write in {lang_name}.",
        "hashtags": f"Give 30 targeted hashtags for: {user_input}. 10 large, 10 medium, 10 small. Mix {lang_name} and English.",
        "script": f"Write a short video script for: {user_input}. Include hook, content, CTA. Write in {lang_name}.",
        "ads": f"Write persuasive ad copy for: {user_input}. Include headline, body, CTA. Write in {lang_name}.",
        "names": f"Give 10 creative brand names for: {user_input}. Include meaning and domain suggestion. Write in {lang_name}.",
        "email": f"Write a professional email for: {user_input}. Include subject, opening, body, CTA, closing. Write in {lang_name}.",
        "story": f"Write a compelling brand story for: {user_input}. Include problem, journey, solution, message. Write in {lang_name}.",
        "bio": f"Write 3 professional bio versions for: {user_input}. Formal, friendly, creative. Max 150 chars each. Write in {lang_name}.",
        "replies": f"Write 5 professional replies to: {user_input}. Calm, problem-solving, customer-retaining. Write in {lang_name}.",
        "starter": f"Create starter pack for: {user_input}. Include: 1 bio (3 versions), 10 content ideas, 15 hashtags. Write in {lang_name}.",
        "pro": f"Create pro pack for: {user_input}. Include: 1 bio (3 versions), 30 content ideas, 10 captions, 30 hashtags. Write in {lang_name}.",
        "ultimate": f"Create ultimate pack for: {user_input}. Include: bio, 30 ideas, 10 captions, 30 hashtags, ad copy, video script. Write in {lang_name}."
    }
    
    return prompts.get(svc_key, f"Create professional content for: {user_input}. Write in {lang_name}.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    total = len(orders)
    completed = len([o for o in orders.values() if o['status'] == 'completed'])
    pending = len([o for o in orders.values() if o['status'] == 'pending'])
    revenue = sum(o['price'] for o in orders.values() if o['status'] == 'completed')
    
    await update.message.reply_text(
        f"📊 **Stats:**\n\n📦 Total: {total}\n✅ Completed: {completed}\n⏳ Pending: {pending}\n💰 Revenue: ${revenue}",
        parse_mode='Markdown'
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve_order))
    app.add_handler(CommandHandler("stats", stats))
    
    app.add_handler(CallbackQueryHandler(show_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(show_service, pattern="^svc_"))
    app.add_handler(CallbackQueryHandler(free_sample, pattern="^free_sample$"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(change_lang, pattern="^change_lang$"))
    app.add_handler(CallbackQueryHandler(confirm_paid, pattern="^paid_"))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_message))
    
    logger.info("🚀 Sales Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
