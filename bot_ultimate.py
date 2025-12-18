#!/usr/bin/env python3
"""
Ultimate AI Services Bot - النسخة النهائية المحسّنة
مع كل الميزات لزيادة المبيعات
"""

import os
import asyncio
import logging
import random
import string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from openai import OpenAI

# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# المتغيرات
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8533837337:AAEUuNwVb5AFHib3km1DHX_DMZyF7jNU5Qw')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PAYPAL_LINK = "https://paypal.me/mohammedalderei"
USDT_ADDRESS = "TFgQpnv2qVMHMojdjUrrzQ8iVB3fDR2HN9"
BNB_ADDRESS = "0x45ed64749a512936d2e7956f84d58f1240e8d2e0"
ADMIN_IDS = [507231172]  # أضف ID الخاص بك

# OpenAI Client
client = OpenAI()

# قاعدة بيانات بسيطة
user_data = {}
orders = {}
stats = {"total_users": 0, "total_orders": 0, "total_revenue": 0, "free_samples": 0}

# الترجمات
TEXTS = {
    'ar': {
        'welcome': """🚀 **مرحباً بك في AI Services Bot!**

أنا مساعدك الذكي لإنشاء محتوى احترافي في ثوانٍ!

🎁 **عرض خاص اليوم:** خصم 50% على الباقة الكاملة!

⚡ **لماذا تختارنا؟**
✅ نتائج فورية خلال 60 ثانية
✅ جودة احترافية مضمونة
✅ أسعار تبدأ من $1 فقط
✅ دعم عربي وإنجليزي

👥 **+{users} مستخدم سعيد**

اختر خدمتك الآن 👇""",
        'services_menu': "📋 **قائمة الخدمات:**",
        'social': "📱 السوشيال ميديا",
        'business': "💼 الأعمال",
        'content': "✍️ المحتوى",
        'packages': "🎁 الباقات",
        'free_sample': "🆓 عينة مجانية",
        'my_orders': "📦 طلباتي",
        'change_lang': "🌐 English",
        'back': "🔙 رجوع",
        'select_service': "اختر الخدمة:",
        'payment_title': "💳 **طريقة الدفع**",
        'payment_info': """💰 **المبلغ المطلوب:** ${price}

اختر طريقة الدفع المفضلة:""",
        'usdt_payment': "💎 USDT (TRC20)",
        'bnb_payment': "🔶 BNB (BEP20)",
        'paypal_payment': "💳 PayPal",
        'payment_instructions': """📋 **تعليمات الدفع:**

{method_info}

📝 **رقم الطلب:** `{order_id}`

⚠️ **مهم:** بعد الدفع، أرسل:
1. لقطة شاشة للإيصال
2. أو Transaction Hash

سيتم تسليم طلبك فورًا بعد التأكيد ✅""",
        'order_received': "✅ **تم استلام طلبك!**\n\nرقم الطلب: `{order_id}`\nالخدمة: {service}\nالسعر: ${price}\n\nجاري المعالجة...",
        'processing': "⏳ جاري إنشاء المحتوى...",
        'result_ready': "✅ **تم بنجاح!**\n\nإليك النتيجة:",
        'free_sample_limit': "⚠️ لقد استخدمت العينة المجانية بالفعل.\n\nللحصول على المزيد، اختر خدمة مدفوعة 💎",
        'free_sample_prompt': "أرسل وصفًا قصيرًا لما تريده (مثال: بايو لحساب طبخ):",
        'input_prompt': "📝 أرسل التفاصيل المطلوبة للخدمة:",
        'confirm_payment': "✅ تأكيد الدفع",
        'cancel': "❌ إلغاء",
        'admin_approve': "✅ موافقة",
        'admin_reject': "❌ رفض",
        'order_approved': "🎉 **تمت الموافقة على طلبك!**\n\nجاري إنشاء المحتوى...",
        'order_rejected': "❌ تم رفض الطلب. تواصل مع الدعم.",
        'stats': "📊 **إحصائيات البوت:**\n\n👥 المستخدمين: {users}\n📦 الطلبات: {orders}\n💰 الإيرادات: ${revenue}\n🆓 العينات المجانية: {samples}",
        'pending_orders': "📋 **الطلبات المعلقة:**\n\n{orders}",
        'no_pending': "لا توجد طلبات معلقة ✅",
        'referral': "🎁 **برنامج الإحالة:**\n\nشارك رابطك واحصل على خصم 20% لكل صديق!\n\nرابطك: https://t.me/Aistaruae_bot?start=ref_{user_id}",
        'discount_applied': "🎉 تم تطبيق خصم {discount}%!",
    },
    'en': {
        'welcome': """🚀 **Welcome to AI Services Bot!**

I'm your smart assistant for creating professional content in seconds!

🎁 **Today's Special:** 50% off the Complete Package!

⚡ **Why Choose Us?**
✅ Instant results in 60 seconds
✅ Guaranteed professional quality
✅ Prices starting from just $1
✅ Arabic & English support

👥 **+{users} happy users**

Choose your service now 👇""",
        'services_menu': "📋 **Services Menu:**",
        'social': "📱 Social Media",
        'business': "💼 Business",
        'content': "✍️ Content",
        'packages': "🎁 Packages",
        'free_sample': "🆓 Free Sample",
        'my_orders': "📦 My Orders",
        'change_lang': "🌐 العربية",
        'back': "🔙 Back",
        'select_service': "Select service:",
        'payment_title': "💳 **Payment Method**",
        'payment_info': """💰 **Amount Due:** ${price}

Choose your preferred payment method:""",
        'usdt_payment': "💎 USDT (TRC20)",
        'bnb_payment': "🔶 BNB (BEP20)",
        'paypal_payment': "💳 PayPal",
        'payment_instructions': """📋 **Payment Instructions:**

{method_info}

📝 **Order ID:** `{order_id}`

⚠️ **Important:** After payment, send:
1. Screenshot of receipt
2. Or Transaction Hash

Your order will be delivered immediately after confirmation ✅""",
        'order_received': "✅ **Order Received!**\n\nOrder ID: `{order_id}`\nService: {service}\nPrice: ${price}\n\nProcessing...",
        'processing': "⏳ Creating content...",
        'result_ready': "✅ **Done!**\n\nHere's your result:",
        'free_sample_limit': "⚠️ You've already used your free sample.\n\nFor more, choose a paid service 💎",
        'free_sample_prompt': "Send a short description of what you want (e.g., bio for cooking account):",
        'input_prompt': "📝 Send the required details for the service:",
        'confirm_payment': "✅ Confirm Payment",
        'cancel': "❌ Cancel",
        'admin_approve': "✅ Approve",
        'admin_reject': "❌ Reject",
        'order_approved': "🎉 **Your order has been approved!**\n\nCreating content...",
        'order_rejected': "❌ Order rejected. Contact support.",
        'stats': "📊 **Bot Statistics:**\n\n👥 Users: {users}\n📦 Orders: {orders}\n💰 Revenue: ${revenue}\n🆓 Free Samples: {samples}",
        'pending_orders': "📋 **Pending Orders:**\n\n{orders}",
        'no_pending': "No pending orders ✅",
        'referral': "🎁 **Referral Program:**\n\nShare your link and get 20% off for each friend!\n\nYour link: https://t.me/Aistaruae_bot?start=ref_{user_id}",
        'discount_applied': "🎉 {discount}% discount applied!",
    }
}

# الخدمات مع الأسعار
SERVICES = {
    'social': {
        'ar': {'name': '📱 السوشيال ميديا', 'services': {
            'bio': {'name': '✍️ بايو احترافي', 'price': 1.5, 'prompt': 'اكتب بايو احترافي وجذاب لـ: {input}'},
            'captions': {'name': '📝 10 كابشنات', 'price': 2, 'prompt': 'اكتب 10 كابشنات جذابة ومتنوعة لـ: {input}'},
            'hashtags': {'name': '#️⃣ 30 هاشتاق', 'price': 1, 'prompt': 'اكتب 30 هاشتاق مستهدف لـ: {input}'},
            'replies': {'name': '💬 ردود ذكية', 'price': 1.5, 'prompt': 'اكتب 10 ردود ذكية وجذابة للتعليقات في مجال: {input}'},
        }},
        'en': {'name': '📱 Social Media', 'services': {
            'bio': {'name': '✍️ Professional Bio', 'price': 1.5, 'prompt': 'Write a professional and attractive bio for: {input}'},
            'captions': {'name': '📝 10 Captions', 'price': 2, 'prompt': 'Write 10 attractive and varied captions for: {input}'},
            'hashtags': {'name': '#️⃣ 30 Hashtags', 'price': 1, 'prompt': 'Write 30 targeted hashtags for: {input}'},
            'replies': {'name': '💬 Smart Replies', 'price': 1.5, 'prompt': 'Write 10 smart and engaging replies for comments in: {input}'},
        }}
    },
    'business': {
        'ar': {'name': '💼 الأعمال', 'services': {
            'brand_name': {'name': '🏷️ 10 أسماء تجارية', 'price': 2, 'prompt': 'اقترح 10 أسماء تجارية إبداعية لـ: {input}'},
            'email': {'name': '📧 إيميل احترافي', 'price': 2, 'prompt': 'اكتب إيميل احترافي لـ: {input}'},
            'brand_story': {'name': '📖 قصة العلامة', 'price': 4, 'prompt': 'اكتب قصة علامة تجارية مؤثرة لـ: {input}'},
            'pitch': {'name': '🎤 عرض تقديمي', 'price': 3, 'prompt': 'اكتب نص عرض تقديمي مقنع لـ: {input}'},
        }},
        'en': {'name': '💼 Business', 'services': {
            'brand_name': {'name': '🏷️ 10 Brand Names', 'price': 2, 'prompt': 'Suggest 10 creative brand names for: {input}'},
            'email': {'name': '📧 Professional Email', 'price': 2, 'prompt': 'Write a professional email for: {input}'},
            'brand_story': {'name': '📖 Brand Story', 'price': 4, 'prompt': 'Write an impactful brand story for: {input}'},
            'pitch': {'name': '🎤 Pitch', 'price': 3, 'prompt': 'Write a convincing pitch for: {input}'},
        }}
    },
    'content': {
        'ar': {'name': '✍️ المحتوى', 'services': {
            'ideas': {'name': '💡 30 فكرة محتوى', 'price': 3, 'prompt': 'اقترح 30 فكرة محتوى إبداعية لـ: {input}'},
            'ad_copy': {'name': '📢 نص إعلاني', 'price': 3, 'prompt': 'اكتب نص إعلاني مقنع لـ: {input}'},
            'script': {'name': '🎬 سكريبت فيديو', 'price': 3, 'prompt': 'اكتب سكريبت فيديو قصير وجذاب لـ: {input}'},
            'article': {'name': '📄 مقال كامل', 'price': 5, 'prompt': 'اكتب مقال شامل ومفصل عن: {input}'},
        }},
        'en': {'name': '✍️ Content', 'services': {
            'ideas': {'name': '💡 30 Content Ideas', 'price': 3, 'prompt': 'Suggest 30 creative content ideas for: {input}'},
            'ad_copy': {'name': '📢 Ad Copy', 'price': 3, 'prompt': 'Write a convincing ad copy for: {input}'},
            'script': {'name': '🎬 Video Script', 'price': 3, 'prompt': 'Write a short and engaging video script for: {input}'},
            'article': {'name': '📄 Full Article', 'price': 5, 'prompt': 'Write a comprehensive article about: {input}'},
        }}
    },
    'packages': {
        'ar': {'name': '🎁 الباقات', 'services': {
            'starter': {'name': '⭐ باقة المبتدئ', 'price': 5, 'original': 8, 'includes': ['bio', 'hashtags', 'captions'], 'prompt': 'اكتب بايو احترافي + 30 هاشتاق + 10 كابشنات لـ: {input}'},
            'pro': {'name': '💎 باقة المحترف', 'price': 10, 'original': 18, 'includes': ['bio', 'hashtags', 'captions', 'ideas', 'ad_copy'], 'prompt': 'اكتب بايو + 30 هاشتاق + 10 كابشنات + 30 فكرة محتوى + نص إعلاني لـ: {input}'},
            'business': {'name': '🚀 باقة الأعمال', 'price': 15, 'original': 25, 'includes': ['brand_name', 'brand_story', 'email', 'pitch', 'ad_copy'], 'prompt': 'اكتب 10 أسماء تجارية + قصة علامة + إيميل + عرض تقديمي + نص إعلاني لـ: {input}'},
        }},
        'en': {'name': '🎁 Packages', 'services': {
            'starter': {'name': '⭐ Starter Pack', 'price': 5, 'original': 8, 'includes': ['bio', 'hashtags', 'captions'], 'prompt': 'Write professional bio + 30 hashtags + 10 captions for: {input}'},
            'pro': {'name': '💎 Pro Pack', 'price': 10, 'original': 18, 'includes': ['bio', 'hashtags', 'captions', 'ideas', 'ad_copy'], 'prompt': 'Write bio + 30 hashtags + 10 captions + 30 content ideas + ad copy for: {input}'},
            'business': {'name': '🚀 Business Pack', 'price': 15, 'original': 25, 'includes': ['brand_name', 'brand_story', 'email', 'pitch', 'ad_copy'], 'prompt': 'Write 10 brand names + brand story + email + pitch + ad copy for: {input}'},
        }}
    }
}

def get_user_lang(user_id):
    return user_data.get(user_id, {}).get('lang', 'ar')

def get_text(user_id, key, **kwargs):
    lang = get_user_lang(user_id)
    text = TEXTS[lang].get(key, TEXTS['ar'].get(key, key))
    return text.format(**kwargs) if kwargs else text

def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

async def generate_ai_content(prompt, lang='ar'):
    try:
        system_prompt = "أنت كاتب محتوى محترف. اكتب محتوى إبداعي وجذاب باللغة العربية." if lang == 'ar' else "You are a professional content writer. Write creative and engaging content in English."
        
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.8
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # تهيئة بيانات المستخدم
    if user_id not in user_data:
        user_data[user_id] = {
            'lang': 'ar',
            'free_sample_used': False,
            'orders': [],
            'referral': None,
            'discount': 0
        }
        stats['total_users'] += 1
    
    # التحقق من الإحالة
    if context.args and context.args[0].startswith('ref_'):
        ref_id = context.args[0].replace('ref_', '')
        if ref_id != str(user_id):
            user_data[user_id]['referral'] = ref_id
            user_data[user_id]['discount'] = 10
    
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'social'), callback_data='cat_social'),
         InlineKeyboardButton(get_text(user_id, 'business'), callback_data='cat_business')],
        [InlineKeyboardButton(get_text(user_id, 'content'), callback_data='cat_content'),
         InlineKeyboardButton(get_text(user_id, 'packages'), callback_data='cat_packages')],
        [InlineKeyboardButton(get_text(user_id, 'free_sample'), callback_data='free_sample')],
        [InlineKeyboardButton(get_text(user_id, 'my_orders'), callback_data='my_orders'),
         InlineKeyboardButton(get_text(user_id, 'change_lang'), callback_data='change_lang')],
        [InlineKeyboardButton("🎁 برنامج الإحالة" if lang == 'ar' else "🎁 Referral", callback_data='referral')]
    ]
    
    welcome_text = get_text(user_id, 'welcome', users=stats['total_users'] + 1247)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    lang = get_user_lang(user_id)
    
    if data == 'main_menu':
        await show_main_menu(update, context)
    
    elif data == 'change_lang':
        new_lang = 'en' if lang == 'ar' else 'ar'
        user_data[user_id]['lang'] = new_lang
        await show_main_menu(update, context)
    
    elif data.startswith('cat_'):
        category = data.replace('cat_', '')
        await show_category_services(update, context, category)
    
    elif data.startswith('srv_'):
        parts = data.split('_')
        category = parts[1]
        service = parts[2]
        await show_service_details(update, context, category, service)
    
    elif data.startswith('buy_'):
        parts = data.split('_')
        category = parts[1]
        service = parts[2]
        await show_payment_options(update, context, category, service)
    
    elif data.startswith('pay_'):
        parts = data.split('_')
        method = parts[1]
        category = parts[2]
        service = parts[3]
        await show_payment_instructions(update, context, method, category, service)
    
    elif data == 'free_sample':
        await handle_free_sample(update, context)
    
    elif data == 'my_orders':
        await show_user_orders(update, context)
    
    elif data == 'referral':
        await show_referral(update, context)
    
    elif data.startswith('approve_'):
        order_id = data.replace('approve_', '')
        await approve_order(update, context, order_id)
    
    elif data.startswith('reject_'):
        order_id = data.replace('reject_', '')
        await reject_order(update, context, order_id)

async def show_category_services(update: Update, context: ContextTypes.DEFAULT_TYPE, category):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    
    cat_data = SERVICES[category][lang]
    keyboard = []
    
    for srv_key, srv_data in cat_data['services'].items():
        price_text = f"${srv_data['price']}"
        if 'original' in srv_data:
            price_text = f"~~${srv_data['original']}~~ ${srv_data['price']}"
        
        keyboard.append([InlineKeyboardButton(
            f"{srv_data['name']} - {price_text}",
            callback_data=f'srv_{category}_{srv_key}'
        )])
    
    keyboard.append([InlineKeyboardButton(get_text(user_id, 'back'), callback_data='main_menu')])
    
    await update.callback_query.edit_message_text(
        f"{cat_data['name']}\n\n{get_text(user_id, 'select_service')}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_service_details(update: Update, context: ContextTypes.DEFAULT_TYPE, category, service):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    
    srv_data = SERVICES[category][lang]['services'][service]
    
    # حساب الخصم
    discount = user_data.get(user_id, {}).get('discount', 0)
    final_price = srv_data['price'] * (1 - discount/100)
    
    text = f"**{srv_data['name']}**\n\n"
    if 'original' in srv_data:
        text += f"💰 السعر: ~~${srv_data['original']}~~ **${srv_data['price']}** (خصم 50%!)\n" if lang == 'ar' else f"💰 Price: ~~${srv_data['original']}~~ **${srv_data['price']}** (50% off!)\n"
    else:
        text += f"💰 السعر: **${srv_data['price']}**\n" if lang == 'ar' else f"💰 Price: **${srv_data['price']}**\n"
    
    if discount > 0:
        text += f"\n🎁 خصم إضافي {discount}%: **${final_price:.2f}**\n" if lang == 'ar' else f"\n🎁 Extra {discount}% off: **${final_price:.2f}**\n"
    
    text += f"\n⚡ التسليم: فوري (60 ثانية)" if lang == 'ar' else "\n⚡ Delivery: Instant (60 seconds)"
    
    keyboard = [
        [InlineKeyboardButton("🛒 اشتري الآن" if lang == 'ar' else "🛒 Buy Now", callback_data=f'buy_{category}_{service}')],
        [InlineKeyboardButton(get_text(user_id, 'back'), callback_data=f'cat_{category}')]
    ]
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_payment_options(update: Update, context: ContextTypes.DEFAULT_TYPE, category, service):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    
    srv_data = SERVICES[category][lang]['services'][service]
    price = srv_data['price']
    
    # حساب الخصم
    discount = user_data.get(user_id, {}).get('discount', 0)
    if discount > 0:
        price = price * (1 - discount/100)
    
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'usdt_payment'), callback_data=f'pay_usdt_{category}_{service}')],
        [InlineKeyboardButton(get_text(user_id, 'bnb_payment'), callback_data=f'pay_bnb_{category}_{service}')],
        [InlineKeyboardButton(get_text(user_id, 'paypal_payment'), callback_data=f'pay_paypal_{category}_{service}')],
        [InlineKeyboardButton(get_text(user_id, 'back'), callback_data=f'srv_{category}_{service}')]
    ]
    
    await update.callback_query.edit_message_text(
        get_text(user_id, 'payment_info', price=f"{price:.2f}"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_payment_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE, method, category, service):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    
    srv_data = SERVICES[category][lang]['services'][service]
    price = srv_data['price']
    
    # حساب الخصم
    discount = user_data.get(user_id, {}).get('discount', 0)
    if discount > 0:
        price = price * (1 - discount/100)
    
    order_id = generate_order_id()
    
    # حفظ الطلب
    orders[order_id] = {
        'user_id': user_id,
        'category': category,
        'service': service,
        'price': price,
        'method': method,
        'status': 'pending_payment',
        'created_at': datetime.now(),
        'input': None
    }
    
    if method == 'usdt':
        method_info = f"💎 **USDT (TRC20)**\n\n📋 العنوان:\n`{USDT_ADDRESS}`\n\n💰 المبلغ: **${price:.2f}**" if lang == 'ar' else f"💎 **USDT (TRC20)**\n\n📋 Address:\n`{USDT_ADDRESS}`\n\n💰 Amount: **${price:.2f}**"
    elif method == 'bnb':
        method_info = f"🔶 **BNB (BEP20)**\n\n📋 العنوان:\n`{BNB_ADDRESS}`\n\n💰 المبلغ: **${price:.2f}**" if lang == 'ar' else f"🔶 **BNB (BEP20)**\n\n📋 Address:\n`{BNB_ADDRESS}`\n\n💰 Amount: **${price:.2f}**"
    else:
        method_info = f"💳 **PayPal**\n\n🔗 الرابط:\n{PAYPAL_LINK}/{price:.2f}\n\n💰 المبلغ: **${price:.2f}**" if lang == 'ar' else f"💳 **PayPal**\n\n🔗 Link:\n{PAYPAL_LINK}/{price:.2f}\n\n💰 Amount: **${price:.2f}**"
    
    # حفظ الطلب في سياق المستخدم
    context.user_data['pending_order'] = order_id
    context.user_data['awaiting'] = 'payment_proof'
    
    keyboard = [[InlineKeyboardButton(get_text(user_id, 'cancel'), callback_data='main_menu')]]
    
    await update.callback_query.edit_message_text(
        get_text(user_id, 'payment_instructions', method_info=method_info, order_id=order_id),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_free_sample(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_data.get(user_id, {}).get('free_sample_used', False):
        keyboard = [[InlineKeyboardButton(get_text(user_id, 'back'), callback_data='main_menu')]]
        await update.callback_query.edit_message_text(
            get_text(user_id, 'free_sample_limit'),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    context.user_data['awaiting'] = 'free_sample_input'
    
    keyboard = [[InlineKeyboardButton(get_text(user_id, 'cancel'), callback_data='main_menu')]]
    await update.callback_query.edit_message_text(
        get_text(user_id, 'free_sample_prompt'),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_user_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    
    user_orders = [o for o in orders.values() if o['user_id'] == user_id]
    
    if not user_orders:
        text = "لا توجد طلبات سابقة" if lang == 'ar' else "No previous orders"
    else:
        text = "📦 **طلباتك:**\n\n" if lang == 'ar' else "📦 **Your Orders:**\n\n"
        for order in user_orders[-5:]:
            status_emoji = "✅" if order['status'] == 'completed' else "⏳"
            text += f"{status_emoji} {order.get('service', 'N/A')} - ${order['price']:.2f}\n"
    
    keyboard = [[InlineKeyboardButton(get_text(user_id, 'back'), callback_data='main_menu')]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def show_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    keyboard = [[InlineKeyboardButton(get_text(user_id, 'back'), callback_data='main_menu')]]
    await update.callback_query.edit_message_text(
        get_text(user_id, 'referral', user_id=user_id),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    lang = get_user_lang(user_id)
    
    awaiting = context.user_data.get('awaiting')
    
    if awaiting == 'free_sample_input':
        # معالجة العينة المجانية
        context.user_data['awaiting'] = None
        user_data[user_id]['free_sample_used'] = True
        stats['free_samples'] += 1
        
        await update.message.reply_text(get_text(user_id, 'processing'))
        
        prompt = f"اكتب بايو قصير واحترافي لـ: {text}" if lang == 'ar' else f"Write a short professional bio for: {text}"
        result = await generate_ai_content(prompt, lang)
        
        if result:
            await update.message.reply_text(f"{get_text(user_id, 'result_ready')}\n\n{result}")
            
            # عرض القائمة الرئيسية
            keyboard = [[InlineKeyboardButton("🛒 احصل على المزيد" if lang == 'ar' else "🛒 Get More", callback_data='main_menu')]]
            await update.message.reply_text(
                "🎁 أعجبتك النتيجة؟ احصل على خدمات أكثر بأسعار رائعة!" if lang == 'ar' else "🎁 Liked the result? Get more services at great prices!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text("حدث خطأ. حاول مرة أخرى." if lang == 'ar' else "An error occurred. Please try again.")
    
    elif awaiting == 'payment_proof':
        # استلام إثبات الدفع
        order_id = context.user_data.get('pending_order')
        if order_id and order_id in orders:
            orders[order_id]['status'] = 'pending_approval'
            orders[order_id]['proof'] = text
            context.user_data['awaiting'] = 'service_input'
            
            await update.message.reply_text(
                "✅ تم استلام إثبات الدفع!\n\nالآن أرسل التفاصيل المطلوبة للخدمة:" if lang == 'ar' else "✅ Payment proof received!\n\nNow send the required details for the service:"
            )
            
            # إشعار الأدمن
            for admin_id in ADMIN_IDS:
                try:
                    keyboard = [
                        [InlineKeyboardButton("✅ موافقة", callback_data=f'approve_{order_id}'),
                         InlineKeyboardButton("❌ رفض", callback_data=f'reject_{order_id}')]
                    ]
                    await context.bot.send_message(
                        admin_id,
                        f"🆕 **طلب جديد!**\n\nرقم الطلب: `{order_id}`\nالمستخدم: {user_id}\nالمبلغ: ${orders[order_id]['price']:.2f}\nإثبات الدفع: {text}",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                except:
                    pass
    
    elif awaiting == 'service_input':
        order_id = context.user_data.get('pending_order')
        if order_id and order_id in orders:
            orders[order_id]['input'] = text
            context.user_data['awaiting'] = None
            
            await update.message.reply_text(
                "✅ تم استلام التفاصيل!\n\nسيتم تسليم طلبك فور تأكيد الدفع." if lang == 'ar' else "✅ Details received!\n\nYour order will be delivered once payment is confirmed."
            )
    
    # التعامل مع الصور (إثبات الدفع)
    elif update.message.photo:
        order_id = context.user_data.get('pending_order')
        if order_id and order_id in orders:
            orders[order_id]['status'] = 'pending_approval'
            orders[order_id]['proof'] = 'screenshot'
            context.user_data['awaiting'] = 'service_input'
            
            await update.message.reply_text(
                "✅ تم استلام لقطة الشاشة!\n\nالآن أرسل التفاصيل المطلوبة للخدمة:" if lang == 'ar' else "✅ Screenshot received!\n\nNow send the required details for the service:"
            )
            
            # إرسال الصورة للأدمن
            for admin_id in ADMIN_IDS:
                try:
                    keyboard = [
                        [InlineKeyboardButton("✅ موافقة", callback_data=f'approve_{order_id}'),
                         InlineKeyboardButton("❌ رفض", callback_data=f'reject_{order_id}')]
                    ]
                    await context.bot.send_photo(
                        admin_id,
                        update.message.photo[-1].file_id,
                        caption=f"🆕 **طلب جديد!**\n\nرقم الطلب: `{order_id}`\nالمستخدم: {user_id}\nالمبلغ: ${orders[order_id]['price']:.2f}",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                except:
                    pass

async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id):
    if order_id not in orders:
        await update.callback_query.answer("الطلب غير موجود")
        return
    
    order = orders[order_id]
    order['status'] = 'completed'
    stats['total_orders'] += 1
    stats['total_revenue'] += order['price']
    
    user_id = order['user_id']
    lang = get_user_lang(user_id)
    
    # إنشاء المحتوى
    category = order['category']
    service = order['service']
    user_input = order.get('input', 'general')
    
    srv_data = SERVICES[category][lang]['services'][service]
    prompt = srv_data['prompt'].format(input=user_input)
    
    await update.callback_query.edit_message_text(f"✅ تمت الموافقة على الطلب {order_id}\n\nجاري إنشاء المحتوى...")
    
    result = await generate_ai_content(prompt, lang)
    
    if result:
        try:
            await context.bot.send_message(
                user_id,
                f"🎉 **تم إنجاز طلبك!**\n\nرقم الطلب: `{order_id}`\n\n{result}",
                parse_mode='Markdown'
            )
            
            # رسالة متابعة
            keyboard = [[InlineKeyboardButton("🛒 اطلب المزيد" if lang == 'ar' else "🛒 Order More", callback_data='main_menu')]]
            await context.bot.send_message(
                user_id,
                "⭐ شكرًا لك! نتمنى أن تكون راضيًا عن الخدمة.\n\n🎁 احصل على خصم 10% على طلبك القادم!" if lang == 'ar' else "⭐ Thank you! We hope you're satisfied with the service.\n\n🎁 Get 10% off your next order!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error sending result: {e}")

async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id):
    if order_id not in orders:
        await update.callback_query.answer("الطلب غير موجود")
        return
    
    order = orders[order_id]
    order['status'] = 'rejected'
    
    user_id = order['user_id']
    lang = get_user_lang(user_id)
    
    await update.callback_query.edit_message_text(f"❌ تم رفض الطلب {order_id}")
    
    try:
        await context.bot.send_message(
            user_id,
            get_text(user_id, 'order_rejected')
        )
    except:
        pass

# أوامر الأدمن
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    await update.message.reply_text(
        get_text(user_id, 'stats',
            users=stats['total_users'],
            orders=stats['total_orders'],
            revenue=stats['total_revenue'],
            samples=stats['free_samples']
        ),
        parse_mode='Markdown'
    )

async def admin_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    pending = [f"`{oid}` - ${o['price']:.2f}" for oid, o in orders.items() if o['status'] == 'pending_approval']
    
    if pending:
        await update.message.reply_text(
            get_text(user_id, 'pending_orders', orders='\n'.join(pending)),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(get_text(user_id, 'no_pending'))

async def admin_approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    if not context.args:
        await admin_pending(update, context)
        return
    
    order_id = context.args[0]
    
    class FakeQuery:
        async def edit_message_text(self, text, **kwargs):
            await update.message.reply_text(text)
        async def answer(self, text=None):
            pass
    
    class FakeUpdate:
        callback_query = FakeQuery()
    
    await approve_order(FakeUpdate(), context, order_id)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("pending", admin_pending))
    app.add_handler(CommandHandler("approve", admin_approve_cmd))
    
    # الاستجابات
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))
    
    logger.info("🚀 Ultimate Bot Started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
