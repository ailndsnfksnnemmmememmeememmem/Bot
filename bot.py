import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.error import BadRequest, TimedOut, InvalidToken
from dotenv import load_dotenv
from urllib.parse import urlparse
import database  # استيراد ملف قاعدة البيانات
import shutil

# تحميل ملفات البيئة
load_dotenv()

# تهيئة التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# متغيرات عامة
TELEGRAM_BOT_TOKEN = '8182800982:AAGLM8kJ2mwOUrkpj3fLxmHtN5zbLVTfdhk'  # توكن البوت الجديد
ADMIN_ID = 904718229  # معرف الأدمن الجديد
DATABASE_NAME = 'bot_database.db'

welcome_message = "مرحبًا! أنا بوت تليجرام. كيف يمكنني مساعدتك؟ 😊"
button_layout = [
    [InlineKeyboardButton("🔄 بداء التشغيل", callback_data='start'), InlineKeyboardButton("💰 رصيد", callback_data='balance'), InlineKeyboardButton("🛍️ عرض المنتجات", callback_data='show_products')],
    [InlineKeyboardButton("📞 التواصل مع الدعم الفني", url='https://t.me/ail_teknik_destek')]
]

# رابط حساب التجرام الافتراضي
support_telegram_link = 'https://t.me/ail_teknik_destek'

# دالة للرد على أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
    else:
        return

    database.update_user_balance(user_id, 0)  # إضافة المستخدم إذا لم يكن موجودًا

    keyboard = get_start_keyboard(user_id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_message, reply_markup=reply_markup)

    # عرض الإعلان المؤقت
    ad_code = database.get_ad()
    if ad_code:
        if update.message:
            ad_message = await update.message.reply_text(ad_code)
        elif update.callback_query:
            ad_message = await update.callback_query.message.reply_text(ad_code)
        context.job_queue.run_once(delete_ad_message, 30, chat_id=update.message.chat_id if update.message else update.callback_query.message.chat_id, message_id=ad_message.message_id)

def get_start_keyboard(user_id: int) -> list:
    keyboard = button_layout.copy()
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("➕ إضافة منتج", callback_data='add_product')])
        keyboard.append([InlineKeyboardButton("👥 عرض جميع المستخدمين", callback_data='show_users'), InlineKeyboardButton("📝 تغيير رسالة الترحيب", callback_data='change_welcome_message'), InlineKeyboardButton("📢 إرسال رسالة جماعية", callback_data='send_broadcast')])
        keyboard.append([InlineKeyboardButton("🔗 تغيير معرف الدعم الفني", callback_data='change_support_link')])
        keyboard.append([InlineKeyboardButton("🗄️ إرسال نسخة احتياطية", callback_data='send_backup')])
        keyboard.append([InlineKeyboardButton("🔄 استعادة نسخة احتياطية", callback_data='restore_backup')])
        keyboard.append([InlineKeyboardButton("📢 إضافة إعلان", callback_data='add_ad')])  # إضافة زر لإضافة إعلان
        keyboard.append([InlineKeyboardButton("🛑 إيقاف الإعلانات", callback_data='stop_ads')])  # إضافة زر لإيقاف الإعلانات
        keyboard.append([InlineKeyboardButton("📝 تغيير كود الإعلان", callback_data='change_ad_code')])  # إضافة زر لتغيير كود الإعلان
    return keyboard

# دالة لحذف رسالة الإعلان بعد 30 ثانية
async def delete_ad_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.delete_message(chat_id=context.job.chat_id, message_id=context.job.message_id)

# دالة للرد على أمر /balance
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    balance = database.get_user_balance(user_id)
    await update.message.reply_text(f'رصيدك الحالي هو: {balance} 💰')

# دالة للرد على أمر /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("➕ إضافة رصيد", callback_data='add_balance'), InlineKeyboardButton("➖ خصم رصيد", callback_data='subtract_balance')], 
            [InlineKeyboardButton("👥 عرض جميع المستخدمين", callback_data='show_users'), InlineKeyboardButton("📝 تغيير رسالة الترحيب", callback_data='change_welcome_message'), InlineKeyboardButton("📢 إرسال رسالة جماعية", callback_data='send_broadcast')],
            [InlineKeyboardButton("🔗 تغيير معرف الدعم الفني", callback_data='change_support_link')],
            [InlineKeyboardButton("🗄️ إرسال نسخة احتياطية", callback_data='send_backup')],
            [InlineKeyboardButton("🔄 استعادة نسخة احتياطية", callback_data='restore_backup')],
            [InlineKeyboardButton("🗑️ حذف منتج", callback_data='delete_product')],
            [InlineKeyboardButton("📢 إضافة إعلان", callback_data='add_ad')],  # إضافة زر لإضافة إعلان
            [InlineKeyboardButton("🛑 إيقاف الإعلانات", callback_data='stop_ads')],  # إضافة زر لإيقاف الإعلانات
            [InlineKeyboardButton("📝 تغيير كود الإعلان", callback_data='change_ad_code')],  # إضافة زر لتغيير كود الإعلان
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('اختر إجراء:', reply_markup=reply_markup)
    else:
        await update.message.reply_text('أنت لست أدمن. 🚫')

# دالة لمعالجة الأزرار
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'start':
        await start(update, context)
    elif query.data == 'balance':
        user_id = query.from_user.id
        balance = database.get_user_balance(user_id)
        await query.message.reply_text(f'رصيدك الحالي هو: {balance} 💰')
    elif query.data == 'add_balance':
        await query.message.reply_text('أدخل المعرف والمبلغ المراد إضافته (مثال: 123456789 100)')
    elif query.data == 'subtract_balance':
        await query.message.reply_text('أدخل المعرف والمبلغ المراد خصمه (مثال: 123456789 50)')
    elif query.data == 'add_product':
        context.user_data['step'] = 'name'
        await query.message.reply_text('أدخل اسم المنتج:')
    elif query.data == 'show_products':
        products = database.get_all_products()
        if products:
            product_list = "\n".join([f"{product[0]}: {product[1]}" for product in products])
            keyboard = []
            for product in products:
                product_id = product[0]
                product_name = product[1]
                product_description = product[3]
                product_price = product[4]
                keyboard.append([InlineKeyboardButton(f"عرض {product_name}", callback_data=f'view_{product_id}')])
                keyboard.append([
                    InlineKeyboardButton(f"وصف: {product_description}", callback_data='ignore'),
                    InlineKeyboardButton(f"سعر: {product_price} دولار", callback_data='ignore')
                ])
            keyboard.append([InlineKeyboardButton("رجوع", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(f'قائمة المنتجات:\n{product_list}', reply_markup=reply_markup)
        else:
            await query.message.reply_text('لا توجد منتجات متاحة. 🛍️')
    elif query.data == 'edit_buttons':
        context.user_data['step'] = 'edit_buttons'
        await query.message.reply_text('أدخل اسم الزر الجديد:')
    elif query.data == 'change_word':
        context.user_data['step'] = 'old_word'
        await query.message.reply_text('أدخل الكلمة القديمة:')
    elif query.data == 'remove_button':
        context.user_data['step'] = 'remove_button_name'
        await query.message.reply_text('أدخل اسم الزر المراد حذفه:')
    elif query.data == 'show_users':
        users = database.get_all_users()
        if users:
            user_list = "\n".join([f"{user}" for user in users])
            await query.message.reply_text(f'قائمة المستخدمين:\n{user_list}')
        else:
            await query.message.reply_text('لا توجد مستخدمين مسجلين. 👥')
    elif query.data == 'change_welcome_message':
        context.user_data['step'] = 'change_welcome_message'
        await query.message.reply_text('أدخل رسالة الترحيب الجديدة:')
    elif query.data == 'send_broadcast':
        context.user_data['step'] = 'send_broadcast'
        await query.message.reply_text('أدخل الرسالة التي تريد إرسالها جماعيًا:')
    elif query.data == 'change_button_layout':
        context.user_data['step'] = 'change_button_layout'
        await query.message.reply_text('أدخل تشكيل الأزرار الجديد (قائمة من الأزرار مفصولة بفواصل):')
    elif query.data == 'change_support_link':
        context.user_data['step'] = 'change_support_link'
        await query.message.reply_text('أدخل الرابط الجديد للدعم الفني (يجب أن يبدأ بـ https://t.me/):')
    elif query.data == 'send_backup':
        await send_backup(update, context)
    elif query.data == 'restore_backup':
        context.user_data['step'] = 'restore_backup'
        await query.message.reply_text('أرسل الملف المحفوظ لاستعادة النسخة الاحتياطية:')
    elif query.data == 'delete_product':
        context.user_data['step'] = 'delete_product_id'
        await query.message.reply_text('أدخل معرف المنتج المراد حذفه:')
    elif query.data == 'add_ad':
        context.user_data['step'] = 'add_ad_code'
        await query.message.reply_text('أدخل كود الإعلان:')
    elif query.data == 'stop_ads':
        database.update_ad_status(0)
        await query.message.reply_text('تم إيقاف الإعلانات. 🛑')
    elif query.data == 'change_ad_code':
        context.user_data['step'] = 'change_ad_code'
        await query.message.reply_text('أدخل كود الإعلان الجديد:')
    elif query.data.startswith('view_'):
        product_id = query.data.split('_')[1]
        user_id = query.from_user.id

        # تحقق من وجود المنتج في قاعدة البيانات
        product = database.get_product(product_id)
        if product:
            product_name = product[1]
            product_price = product[4]
            product_description = product[3]
            product_image_url = product[5]

            message = f'اسم المنتج: {product_name}\nالسعر: {product_price} دولار\nالوصف: {product_description}'
            keyboard = [[InlineKeyboardButton("🛍️ شراء المنتج", callback_data=f'buy_{product_id}')], [InlineKeyboardButton("↩️ رجوع", callback_data='back')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if product_image_url:
                await query.message.reply_photo(photo=product_image_url, caption=message, reply_markup=reply_markup)
            else:
                await query.message.reply_text(message, reply_markup=reply_markup)
        else:
            await query.message.reply_text('المنتج غير متاح. 🛍️')
    elif query.data.startswith('buy_'):
        product_id = query.data.split('_')[1]
        user_id = query.from_user.id

        # تحقق من وجود المنتج في قاعدة البيانات
        product = database.get_product(product_id)
        if product:
            if database.get_user_balance(user_id) >= product[4]:
                database.update_user_balance(user_id, -product[4])
                context.user_data['product_id'] = product_id
                context.user_data['step'] = 'address'
                await query.message.reply_text('أدخل العنوان: 🏠')
            else:
                await query.message.reply_text('رصيدك غير كافٍ لشراء هذا المنتج. 💰')
        else:
            await query.message.reply_text('المنتج غير متاح. 🛍️')
    elif query.data == 'back':
        await start(update, context)
    elif query.data.startswith('confirm_'):
        order_id = query.data.split('_')[1]
        await confirm_order(update, context, order_id)
    elif query.data.startswith('reject_'):
        order_id = query.data.split('_')[1]
        context.user_data['order_id'] = order_id
        context.user_data['step'] = 'reject_reason'
        await query.message.reply_text('أدخل سبب الرفض: 📝')

# دالة لتأكيد الطلب
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    order = database.get_order(order_id)
    if order:
        user_id = order[1]
        product_id = order[2]
        database.update_order_status(order_id, 'confirmed')
        await send_order_confirmation(update, context, user_id, product_id)
        await update.callback_query.message.reply_text('تم تأكيد الطلب بنجاح. ✅')

# دالة لمعالجة الرسائل النصية
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    text = update.message.text

    # إرسال معرف المستخدم مع الرد على الرسالة
    await update.message.reply_text(f'معرفك هو: {user_id}\nرسالتك: {text}')

    if user_id == ADMIN_ID:
        step = context.user_data.get('step')
        if step == 'name':
            context.user_data['product_name'] = text
            context.user_data['step'] = 'category'
            await update.message.reply_text('أدخل القسم:')
        elif step == 'category':
            context.user_data['product_category'] = text
            context.user_data['step'] = 'description'
            await update.message.reply_text('أدخل وصف المنتج:')
        elif step == 'description':
            context.user_data['product_description'] = text
            context.user_data['step'] = 'price'
            await update.message.reply_text('أدخل سعر المنتج:')
        elif step == 'price':
            context.user_data['product_price'] = int(text)
            context.user_data['step'] = 'image'
            await update.message.reply_text('أدخل رابط صورة المنتج:')
        elif step == 'image':
            product_name = context.user_data['product_name']
            product_category = context.user_data['product_category']
            product_description = context.user_data['product_description']
            product_price = context.user_data['product_price']
            product_id = str(len(database.get_all_products()) + 1)  # استخدام سلسلة للمفتاح
            database.add_product(product_id, product_name, product_category, product_description, product_price, text)
            await update.message.reply_text(f'تمت إضافة المنتج: {product_name} في القسم {product_category} بسعر {product_price} 🛍️')
            context.user_data.clear()
        elif step == 'edit_buttons':
            new_button_name = text
            context.user_data['new_button_name'] = new_button_name
            context.user_data['step'] = 'edit_buttons_callback'
            await update.message.reply_text('أدخل البيانات الجديدة للزر:')
        elif step == 'edit_buttons_callback':
            new_button_name = context.user_data['new_button_name']
            new_button_callback = text
            # تحديث الزر في قاعدة البيانات
            await update.message.reply_text(f'تم تعديل الزر: {new_button_name} بالبيانات الجديدة: {new_button_callback} 🛠️')
            context.user_data.clear()
        elif step == 'old_word':
            context.user_data['old_word'] = text
            context.user_data['step'] = 'new_word'
            await update.message.reply_text('أدخل الكلمة الجديدة:')
        elif step == 'new_word':
            old_word = context.user_data['old_word']
            new_word = text
            # تحديث الكلمة المحددة في البوت
            # يمكنك تخزين الكلمة الجديدة في مكان مناسب أو تنفيذ أي إجراء آخر هنا
            await update.message.reply_text(f'تم تغيير الكلمة من "{old_word}" إلى "{new_word}". 📝')
            context.user_data.clear()
        elif step == 'remove_button_name':
            button_name = text
            # حذف الزر من قاعدة البيانات
            await update.message.reply_text(f'تم حذف الزر: {button_name} 🗑️')
            context.user_data.clear()
        elif step == 'reject_reason':
            order_id = context.user_data['order_id']
            reason = text
            order = database.get_order(order_id)
            user_id = order[1]
            product_id = order[2]
            database.update_user_balance(user_id, products[product_id]['price'])
            await update.message.reply_text(f'تم رفض الطلب {order_id} بسبب: {reason} 🛑')
            await send_order_rejection(update, context, user_id, product_id, reason)
            database.update_order_status(order_id, 'rejected')
            context.user_data.clear()
        elif step == 'buy_number_service_id':
            service_id = text
            await order_number(update, context, service_id)
            context.user_data.clear()
        elif step == 'reuse_number_order_id':
            order_id = text
            await reuse_number(update, context, order_id)
            context.user_data.clear()
        elif step == 'get_messages_order_id':
            order_id = text
            await get_messages(update, context, order_id)
            context.user_data.clear()
        elif step == 'refund_number_order_id':
            order_id = text
            await refund_number(update, context, order_id)
            context.user_data.clear()
        elif step == 'get_rental_messages_rental_id':
            rental_id = text
            await get_rental_messages(update, context, rental_id)
            context.user_data.clear()
        elif step == 'activate_rental_rental_id':
            rental_id = text
            await activate_rental(update, context, rental_id)
            context.user_data.clear()
        elif step == 'order_rental_service_id':
            service_id = text
            await order_rental(update, context, service_id)
            context.user_data.clear()
        elif step == 'renew_rental_rental_id':
            rental_id = text
            await renew_rental(update, context, rental_id)
            context.user_data.clear()
        elif step == 'change_welcome_message':
            global welcome_message
            welcome_message = text
            await update.message.reply_text(f'تم تغيير رسالة الترحيب إلى: "{welcome_message}". 📝')
            context.user_data.clear()
        elif step == 'send_broadcast':
            broadcast_message = context.user_data['broadcast_message']
            for user_id in database.get_all_users():
                await context.bot.send_message(chat_id=user_id, text=broadcast_message)
            await update.message.reply_text('تم إرسال الرسالة الجماعية بنجاح. 📢')
            context.user_data.clear()
        elif step == 'change_button_layout':
            new_layout = text.split(',')
            global button_layout
            button_layout = []
            for i in range(0, len(new_layout), 3):
                row = []
                for j in range(3):
                    if i + j < len(new_layout):
                        button_text = new_layout[i + j].strip()
                        button_data = button_text.lower().replace(' ', '_')
                        row.append(InlineKeyboardButton(button_text, callback_data=button_data))
                button_layout.append(row)
            await update.message.reply_text('تم تغيير تشكيل الأزرار بنجاح. 🛠️')
            context.user_data.clear()
            # إرسال تشكيل الأزرار الجديد إلى المستخدم
            keyboard = get_start_keyboard(user_id)
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(welcome_message, reply_markup=reply_markup)
        elif step == 'change_support_link':
            global support_telegram_link
            parsed_url = urlparse(text)
            if parsed_url.scheme == 'https' and parsed_url.netloc == 't.me':
                support_telegram_link = text
                await update.message.reply_text(f'تم تغيير رابط الدعم الفني إلى: "{support_telegram_link}". 🔗')
                context.user_data.clear()
                # تحديث لوحة المفاتيح بالرابط الجديد
                button_layout[-1] = [InlineKeyboardButton("التواصل مع الدعم الفني", url=support_telegram_link)]
                keyboard = get_start_keyboard(user_id)
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(welcome_message, reply_markup=reply_markup)
            else:
                await update.message.reply_text('الرابط غير صالح. يجب أن يبدأ بـ https://t.me/ 🚫')
        elif step == 'delete_product_id':
            product_id = text
            database.delete_product(product_id)
            await update.message.reply_text(f'تم حذف المنتج بنجاح. 🗑️')
            context.user_data.clear()
        elif step == 'add_ad_code':
            ad_code = text
            database.add_ad(ad_code)
            await update.message.reply_text(f'تم إضافة كود الإعلان بنجاح. 📢')
            context.user_data.clear()
        elif step == 'change_ad_code':
            new_ad_code = text
            database.change_ad_code(new_ad_code)
            await update.message.reply_text(f'تم تغيير كود الإعلان بنجاح. 📝')
            context.user_data.clear()
        elif step == 'restore_backup':
            if update.message.document:
                file = await update.message.document.get_file()
                await file.download_to_drive(DATABASE_NAME)
                await update.message.reply_text('تم استعادة النسخة الاحتياطية بنجاح. 🗄️')
                context.user_data.clear()
            else:
                await update.message.reply_text('يرجى إرسال ملف النسخة الاحتياطية. 📁')
        else:
            if text.startswith('-'):
                parts = text.split()
                if len(parts) == 2:
                    target_user_id = int(parts[0][1:])  # إزالة علامة الناقص
                    amount = int(parts[1])
                    database.subtract_user_balance(target_user_id, amount)
                    await update.message.reply_text(f'تم خصم {amount} من رصيد المستخدم {target_user_id} 💰')
                else:
                    await update.message.reply_text('تنسيق الرسالة غير صحيح. 🚫')
            else:
                parts = text.split()
                if len(parts) == 2:
                    target_user_id = int(parts[0])
                    amount = int(parts[1])
                    database.update_user_balance(target_user_id, amount)
                    await update.message.reply_text(f'تمت إضافة {amount} إلى رصيد المستخدم {target_user_id} 💰')
                elif len(parts) == 3 and parts[2] == 'subtract':
                    target_user_id = int(parts[0])
                    amount = int(parts[1])
                    database.subtract_user_balance(target_user_id, amount)
                    await update.message.reply_text(f'تم خصم {amount} من رصيد المستخدم {target_user_id} 💰')
                else:
                    await update.message.reply_text('تنسيق الرسالة غير صحيح. 🚫')
    else:
        step = context.user_data.get('step')
        if step == 'address':
            context.user_data['address'] = text
            context.user_data['step'] = 'notes'
            await update.message.reply_text('أدخل الملاحظات (إذا كان لديك أي ملاحظات): 📝')
        elif step == 'notes':
            context.user_data['notes'] = text
            product_id = context.user_data['product_id']
            product_name = database.get_product(product_id)[1]
            product_image_url = database.get_product(product_id)[5]
            address = context.user_data['address']
            notes = context.user_data['notes']
            message = f'تم شراء المنتج {product_name} بنجاح!\nالعنوان: {address}\nالملاحظات: {notes} 🛍️'
            try:
                if product_image_url:
                    await update.message.reply_photo(photo=product_image_url, caption=message)
                else:
                    await update.message.reply_text(message)
            except (BadRequest, TimedOut) as e:
                await update.message.reply_text(f'حدث خطأ أثناء معالجة الصورة: {str(e)} 🚫')
            await update.message.reply_text(f'رصيدك المتبقي: {database.get_user_balance(user_id)} 💰')
            await update.message.reply_text('تم تقديم طلبك بنجاح. ✅')
            await send_order_to_admin(update, context, user_id, product_id)
            context.user_data.clear()

# دالة لإرسال الطلب إلى الأدمن
async def send_order_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, product_id: int) -> None:
    product_name = database.get_product(product_id)[1]
    product_description = database.get_product(product_id)[3]
    product_image_url = database.get_product(product_id)[5]
    address = context.user_data.get('address', 'No address provided')
    notes = context.user_data.get('notes', 'No notes provided')
    message = f'طلب جديد من المستخدم {user_id}:\nالمنتج: {product_name}\nالوصف: {product_description}\nالعنوان: {address}\nالملاحظات: {notes} 🛍️'
    order_id = str(len(database.get_all_orders()) + 1)
    database.add_order(order_id, user_id, product_id, address, notes, 'pending')
    keyboard = [
        [InlineKeyboardButton("تأكيد الطلب", callback_data=f'confirm_{order_id}')],
        [InlineKeyboardButton("رفض الطلب", callback_data=f'reject_{order_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if product_image_url:
        try:
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=product_image_url, caption=message, reply_markup=reply_markup)
        except BadRequest as e:
            if "Image_process_failed" in str(e):
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"حدث خطأ أثناء معالجة الصورة: {str(e)}. يرجى التحقق من حجم ونوع الصورة. 🚫")
            else:
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"حدث خطأ أثناء معالجة الصورة: {str(e)} 🚫")
    else:
        await context.bot.send_message(chat_id=ADMIN_ID, text=message, reply_markup=reply_markup)

# دالة لإرسال تأكيد الطلب إلى المستخدم
async def send_order_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, product_id: int) -> None:
    product_name = database.get_product(product_id)[1]
    product_description = database.get_product(product_id)[3]
    product_image_url = database.get_product(product_id)[5]
    message = f'تم تأكيد طلبك للمنتج {product_name}.\nالوصف: {product_description} ✅'
    if product_image_url:
        try:
            await context.bot.send_photo(chat_id=user_id, photo=product_image_url, caption=message)
        except BadRequest as e:
            if "Image_process_failed" in str(e):
                await context.bot.send_message(chat_id=user_id, text=f"حدث خطأ أثناء معالجة الصورة: {str(e)}. يرجى التحقق من حجم ونوع الصورة. 🚫")
            else:
                await context.bot.send_message(chat_id=user_id, text=f"حدث خطأ أثناء معالجة الصورة: {str(e)} 🚫")
    else:
        await context.bot.send_message(chat_id=user_id, text=message)

# دالة لإرسال رفض الطلب إلى المستخدم
async def send_order_rejection(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, product_id: int, reason: str) -> None:
    product_name = database.get_product(product_id)[1]
    product_description = database.get_product(product_id)[3]
    product_image_url = database.get_product(product_id)[5]
    message = f'تم رفض طلبك للمنتج {product_name}.\nالوصف: {product_description}\nالسبب: {reason}\nرصيدك المتبقي: {database.get_user_balance(user_id)} 🛑'
    if product_image_url:
        try:
            await context.bot.send_photo(chat_id=user_id, photo=product_image_url, caption=message)
        except BadRequest as e:
            if "Image_process_failed" in str(e):
                await context.bot.send_message(chat_id=user_id, text=f"حدث خطأ أثناء معالجة الصورة: {str(e)}. يرجى التحقق من حجم ونوع الصورة. 🚫")
            else:
                await context.bot.send_message(chat_id=user_id, text=f"حدث خطأ أثناء معالجة الصورة: {str(e)} 🚫")
    else:
        await context.bot.send_message(chat_id=user_id, text=message)

# دالة لإرسال نسخة احتياطية من البيانات إلى الأدمن
async def send_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    backup_file = 'bot_database_backup.db'
    shutil.copyfile(DATABASE_NAME, backup_file)

    with open(backup_file, 'rb') as file:
        await context.bot.send_document(chat_id=update.callback_query.message.chat_id, document=file, caption="نسخة احتياطية لقاعدة البيانات 🗄️")

    os.remove(backup_file)  # حذف الملف المؤقت بعد الإرسال

# دالة لاستعادة نسخة احتياطية من البيانات
async def restore_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.document:
        file = await update.message.document.get_file()
        await file.download_to_drive(DATABASE_NAME)
        await update.message.reply_text('تم استعادة النسخة الاحتياطية بنجاح. 🗄️')
    else:
        await update.message.reply_text('يرجى إرسال ملف النسخة الاحتياطية. 📁')

def main() -> None:
    # إنشاء مثيل للـ ApplicationBuilder وتمرير التوكن
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # تسجيل المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, restore_backup))  # تسجيل معالج لاستعادة النسخة الاحتياطية

    # تأكيد إنشاء الجداول قبل بدء البوت
    database.init_db()

    # بدء البوت
    application.run_polling()

if __name__ == '__main__':
    main()
