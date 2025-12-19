# BOT_TOKEN = "8287691451:AAHOOR3LvsEbr6IsPnSC7ygvtUT5Lze20Wc"
import asyncio
import os
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Filter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import logging

# Logging sozlash
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ------------ TOKEN ------------
BOT_TOKEN = "8287691451:AAHOOR3LvsEbr6IsPnSC7ygvtUT5Lze20Wc"

# ------------ ADMIN ID ------------
ADMINS = {7345258559, 474777651,381234}

# ------------ СПИСОК ТЬЮТОРОВ ------------
TUTORS = {
    "Сафаров Шерзод Тожиевич": 627589541,
    "Аминова Самира Максудовна": 1879601730,
    "Акбаров Уткир Худойберганович": 6502274697,
    "Сайдалимова Инобат Абдуллаевна": 6827503862,
    "Ортиков Содик Хидирович": 1607442177,
    # "Doniyor": 6642417048,
    # "Elbobo": 920022557,
}

# ------------ MA'LUMOTLAR ------------
active_chats = {}
parent_to_tutor = {}
tutor_chats = {}
message_queue = []
admin_replies = {}
tutor_selections = {}
user_names = {}
all_messages = []  # Barcha xabarlar tarixi

# Papkalarni yaratish
os.makedirs("chat_logs", exist_ok=True)
os.makedirs("admin_logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Bot yaratish
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# =============== MA'LUMOTLARNI SAQLASH VA YUKLASH ==================

def save_bot_data():
    """Barcha muhim ma'lumotlarni faylga saqlash"""
    try:
        data = {
            "active_chats": active_chats,
            "parent_to_tutor": parent_to_tutor,
            "tutor_chats": tutor_chats,
            "user_names": user_names,
            "message_queue": message_queue[-100:],  # Oxirgi 100 ta xabarni saqlash
            "all_messages": all_messages[-500:],  # Oxirgi 500 ta xabarni saqlash
            "last_save_time": format_time()
        }

        with open("data/bot_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Ma'lumotlar saqlandi: {len(active_chats)} chat, {len(all_messages)} xabar")
        return True
    except Exception as e:
        logger.error(f"❌ Ma'lumotlarni saqlashda xato: {e}")
        return False


def load_bot_data():
    """Ma'lumotlarni fayldan yuklash"""
    global active_chats, parent_to_tutor, tutor_chats, user_names, message_queue, all_messages

    try:
        if os.path.exists("data/bot_data.json"):
            with open("data/bot_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            active_chats = data.get("active_chats", {})
            parent_to_tutor = data.get("parent_to_tutor", {})
            tutor_chats = data.get("tutor_chats", {})
            user_names = data.get("user_names", {})
            message_queue = data.get("message_queue", [])
            all_messages = data.get("all_messages", [])

            # String IDlarni integer ga o'tkazish
            if active_chats:
                new_active_chats = {}
                for key, value in active_chats.items():
                    try:
                        new_active_chats[int(key)] = value
                    except:
                        new_active_chats[key] = value
                active_chats = new_active_chats

            if parent_to_tutor:
                new_parent_to_tutor = {}
                for key, value in parent_to_tutor.items():
                    try:
                        new_parent_to_tutor[int(key)] = int(value)
                    except:
                        new_parent_to_tutor[key] = value
                parent_to_tutor = new_parent_to_tutor

            if tutor_chats:
                new_tutor_chats = {}
                for key, value in tutor_chats.items():
                    try:
                        new_tutor_chats[int(key)] = [int(v) for v in value]
                    except:
                        new_tutor_chats[key] = value
                tutor_chats = new_tutor_chats

            if user_names:
                new_user_names = {}
                for key, value in user_names.items():
                    try:
                        new_user_names[int(key)] = value
                    except:
                        new_user_names[key] = value
                user_names = new_user_names

            last_save = data.get("last_save_time", "Noma'lum")
            logger.info(
                f"✅ Ma'lumotlar yuklandi: {len(active_chats)} chat, {len(all_messages)} xabar (oxirgi saqlash: {last_save})")

            if active_chats:
                logger.info("📋 Yuklangan chatlar:")
                for parent_id, chat_info in active_chats.items():
                    tutor_name = chat_info.get("tutor_name", "Noma'lum")
                    logger.info(f"   • Parent {parent_id} → Tutor {tutor_name}")
        else:
            logger.info("ℹ️ Saqlangan ma'lumotlar topilmadi, yangi fayl yaratiladi")
    except Exception as e:
        logger.error(f"❌ Ma'lumotlarni yuklashda xato: {e}")
        active_chats = {}
        parent_to_tutor = {}
        tutor_chats = {}
        user_names = {}
        message_queue = []
        all_messages = []


def save_message_to_history(message_data):
    """Xabarni doimiy tarixga saqlash"""
    try:
        all_messages.append(message_data)
        save_bot_data()
        return True
    except Exception as e:
        logger.error(f"❌ Xabarni saqlashda xato: {e}")
        return False


# =============== FILTERLAR ==================

class IsAdmin(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in ADMINS


class IsTutor(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in TUTORS.values()


class IsParent(Filter):
    async def __call__(self, message: types.Message) -> bool:
        user_id = message.from_user.id
        return user_id not in ADMINS and user_id not in TUTORS.values()


# =============== FOYDALANUVCHI NOMINI OLISH ==================

async def get_user_name(user_id):
    """Foydalanuvchi nomini olish yoki yaratish"""
    if user_id in user_names:
        return user_names[user_id]

    try:
        user = await bot.get_chat(user_id)
        name = ""

        if user.username:
            name = f"@{user.username}"
        elif user.first_name and user.last_name:
            name = f"{user.first_name} {user.last_name}"
        elif user.first_name:
            name = user.first_name
        else:
            name = f"User_{user_id}"

        # Maxsus belgilarni tozalash
        name = name.replace('<', '').replace('>', '').replace('&', '').replace('"', "'")

        user_names[user_id] = name
        return name
    except Exception as e:
        logger.error(f"Get user name error {user_id}: {e}")
        return f"User_{user_id}"


# =============== VAQT FORMATI ==================

def format_time():
    """Hozirgi vaqtni formatlash: %d.%m.%Y | %H:%M"""
    return datetime.now().strftime("%d.%m.%Y | %H:%M")


def format_time_short():
    """Qisqa vaqt formati: %H:%M"""
    return datetime.now().strftime("%H:%M")


# =============== ADMIN PANEL ==================

async def admin_panel(message: types.Message = None, callback: CallbackQuery = None):
    """Admin panel - message yoki callback qabul qilishi mumkin"""
    try:
        # Message yoki callback ni tekshirish
        if message:
            user_id = message.from_user.id
        elif callback:
            user_id = callback.from_user.id
        else:
            return

        if user_id not in ADMINS:
            return

        # Bugungi xabarlarni sanash
        today = datetime.now().strftime("%d.%m.%Y")
        today_messages = [msg for msg in all_messages if msg.get('time', '').startswith(today.split(' ')[0])]

        kb = InlineKeyboardBuilder()
        kb.button(text="📊 Статистика", callback_data="admin_stats")
        kb.button(text="👥 Все чаты", callback_data="all_chats_admin")
        kb.button(text="📨 Ответить родителю", callback_data="reply_to_parent_menu")
        kb.button(text="📝 Последние сообщения", callback_data="recent_messages")
        kb.button(text="🗑️ Очистить очередь", callback_data="clear_queue")
        kb.adjust(2)

        text = (
            "👨‍💼 <b>Админ панель</b>\n\n"
            f"Активных чатов: {len(active_chats)}\n"
            f"Сообщений в очереди: {len(message_queue)}\n"
            f"Всего сообщений: {len(all_messages)}\n"
            f"Сообщений сегодня: {len(today_messages)}\n"
            f"Время: {format_time()}"
        )

        if message:
            await message.answer(text, reply_markup=kb.as_markup())
        elif callback:
            try:
                await callback.message.edit_text(text, reply_markup=kb.as_markup())
            except Exception as e:
                if "message is not modified" in str(e):
                    await callback.answer("✅ Админ панель уже открыта")
                else:
                    try:
                        await callback.message.delete()
                    except:
                        pass
                    await callback.message.answer(text, reply_markup=kb.as_markup())
    except Exception as e:
        logger.error(f"Admin panel error: {e}")


@dp.message(Command("admin"))
async def admin_panel_command(message: types.Message):
    await admin_panel(message=message)


# =============== STATISTIKA ==================

@dp.callback_query(F.data == "admin_stats")
async def admin_stats_handler(callback: CallbackQuery):
    # Bugungi xabarlarni sanash
    today = datetime.now().strftime("%d.%m.%Y")
    today_messages = [msg for msg in all_messages if msg.get('time', '').startswith(today.split(' ')[0])]

    stats_text = f"📊 <b>Статистика</b>\n\n"
    stats_text += f"• Активных чатов: {len(active_chats)}\n"
    stats_text += f"• Родителей: {len(parent_to_tutor)}\n"
    stats_text += f"• Сообщений в очереди: {len(message_queue)}\n"
    stats_text += f"• Всего сообщений: {len(all_messages)}\n"
    stats_text += f"• Сообщений сегодня: {len(today_messages)}\n\n"

    stats_text += "<b>По тьюторам:</b>\n"
    for tutor_name, tutor_id in TUTORS.items():
        count = len([m for m in all_messages if m.get('tutor_id') == tutor_id and m.get('type') != 'admin'])
        chat_count = len(tutor_chats.get(tutor_id, []))
        stats_text += f"• {tutor_name}: {chat_count} чатов, {count} сообщений\n"

    try:
        await callback.message.edit_text(stats_text)
    except Exception as e:
        if "message is not modified" in str(e):
            await callback.answer("✅ Статистика уже обновлена")
        else:
            try:
                await callback.message.delete()
            except:
                pass
            await callback.message.answer(stats_text)


# =============== BARCHA CHATLAR ==================

@dp.callback_query(F.data == "all_chats_admin")
async def all_chats_admin_handler(callback: CallbackQuery):
    if not active_chats:
        try:
            await callback.message.edit_text("❌ Нет активных чатов")
        except Exception as e:
            await callback.answer("❌ Нет активных чатов")
        return

    kb = InlineKeyboardBuilder()

    for parent_id, chat_info in active_chats.items():
        tutor_name = chat_info.get("tutor_name", "Неизвестно")
        parent_name = chat_info.get("parent_name", await get_user_name(parent_id))

        kb.button(
            text=f"👤 {parent_name[:15]} → {tutor_name[:10]}",
            callback_data=f"admin_chat_{parent_id}"
        )

    kb.button(text="🔙 Назад в админ", callback_data="back_to_admin")
    kb.adjust(1)

    try:
        await callback.message.edit_text(
            f"👥 <b>Все активные чаты ({len(active_chats)})</b>\n\n"
            "Выберите чат для просмотра:",
            reply_markup=kb.as_markup()
        )
    except Exception as e:
        if "message is not modified" in str(e):
            await callback.answer("✅ Список чатов уже открыт")
        else:
            try:
                await callback.message.delete()
            except:
                pass
            await callback.message.answer(
                f"👥 <b>Все активные чаты ({len(active_chats)})</b>\n\n"
                "Выберите чат для просмотра:",
                reply_markup=kb.as_markup()
            )


# =============== CHATNI KO'RISH ==================

@dp.callback_query(F.data.startswith("admin_chat_"))
async def admin_chat_view_handler(callback: CallbackQuery):
    try:
        parent_id = int(callback.data.split("_")[2])

        if parent_id not in active_chats:
            await callback.answer("❌ Чат не найден")
            return

        chat_info = active_chats[parent_id]
        tutor_name = chat_info.get("tutor_name", "Неизвестно")
        tutor_id = chat_info.get("tutor_id")

        parent_name = chat_info.get("parent_name", await get_user_name(parent_id))

        # Bu chat uchun xabarlarni topish
        chat_messages = [msg for msg in all_messages if msg.get('parent_id') == parent_id or
                         (msg.get('type') == 'admin_to_parent' and msg.get('parent_id') == parent_id)]

        # Faqat oxirgi 10 ta xabarni ko'rsatish
        recent_chat_messages = chat_messages[-10:]

        kb = InlineKeyboardBuilder()
        kb.button(text="💬 Ответить родителю", callback_data=f"admin_reply_parent_{parent_id}")
        kb.button(text="📋 История чата", callback_data=f"chat_history_{parent_id}")
        kb.button(text="🔙 Назад к чатам", callback_data="all_chats_admin")
        kb.adjust(1)

        text = f"💬 <b>Чат с родителем</b>\n\n"
        text += f"👤 Родитель: {parent_name}\n"
        text += f"🆔 ID: {parent_id}\n"
        text += f"👨‍🏫 Тьютор: {tutor_name}\n"
        text += f"🆔 Тьютор ID: {tutor_id}\n"
        text += f"📅 Чат создан: {chat_info.get('start_time', 'Неизвестно')}\n"
        text += f"💬 Всего сообщений: {len(chat_messages)}\n\n"

        if recent_chat_messages:
            text += "<b>Последние сообщения:</b>\n"
            for msg in recent_chat_messages:
                time = msg.get('time', '')

                if msg.get('type') == 'parent_to_tutor':
                    text += f"🕒 {time} 👤{parent_name}→{tutor_name}: {msg.get('message', '')[:40]}...\n"
                elif msg.get('type') == 'tutor_to_parent':
                    text += f"🕒 {time} {tutor_name}←{parent_name}: {msg.get('message', '')[:40]}...\n"
                elif msg.get('type') == 'admin_to_parent':
                    admin_name = msg.get('admin_name', 'Admin')
                    text += f"🕒 {time} 👨‍💼{admin_name}: {msg.get('message', '')[:40]}...\n"

        try:
            await callback.message.edit_text(text, reply_markup=kb.as_markup())
        except Exception as e:
            if "message is not modified" in str(e):
                await callback.answer("✅ Чат уже открыт")
            else:
                try:
                    await callback.message.delete()
                except:
                    pass
                await callback.message.answer(text, reply_markup=kb.as_markup())
    except Exception as e:
        logger.error(f"Admin chat view error: {e}")
        await callback.answer("❌ Ошибка при открытии чата")


# =============== CHAT TARIXI ==================
@dp.callback_query(F.data.startswith("chat_history_"))
async def chat_history_handler(callback: CallbackQuery):
    try:
        parent_id = int(callback.data.split("_")[2])

        if parent_id not in active_chats:
            await callback.answer("❌ Чат не найден")
            return

        chat_info = active_chats[parent_id]
        tutor_name = chat_info.get("tutor_name", "Неизвестно")
        parent_name = chat_info.get("parent_name", await get_user_name(parent_id))

        # Bu chat uchun xabarlarni topish
        chat_messages = [msg for msg in all_messages if msg.get('parent_id') == parent_id or
                         (msg.get('type') == 'admin_to_parent' and msg.get('parent_id') == parent_id)]

        if not chat_messages:
            await callback.answer("❌ В этом чате пока нет сообщений")
            return

        text = f"📜 <b>История чата с {parent_name}</b>\n\n"
        text += f"👨‍🏫 Тьютор: {tutor_name}\n"
        text += f"💬 Всего сообщений: {len(chat_messages)}\n\n"

        for msg in chat_messages[-20:]:  # Oxirgi 20 ta xabar
            time = msg.get('time', '')

            if msg.get('type') == 'parent_to_tutor':
                text += f"🕒 {time} 👤{parent_name}→{tutor_name}:\n   {msg.get('message', '')[:100]}\n"
            elif msg.get('type') == 'tutor_to_parent':
                text += f"🕒 {time} {tutor_name}←{parent_name}:\n   {msg.get('message', '')[:100]}\n"
            elif msg.get('type') == 'admin_to_parent':
                admin_name = msg.get('admin_name', 'Admin')
                text += f"🕒 {time} 👨‍💼{admin_name}:\n   {msg.get('message', '')[:100]}\n"

            text += "─" * 30 + "\n"

        kb = InlineKeyboardBuilder()
        kb.button(text="💬 Ответить родителю", callback_data=f"admin_reply_parent_{parent_id}")
        kb.button(text="🔙 Назад к чату", callback_data=f"admin_chat_{parent_id}")
        kb.adjust(1)

        try:
            await callback.message.edit_text(text[:4000], reply_markup=kb.as_markup())
        except Exception as e:
            if "message is not modified" in str(e):
                await callback.answer("✅ История уже открыта")
            else:
                try:
                    await callback.message.delete()
                except:
                    pass
                await callback.message.answer(text[:4000], reply_markup=kb.as_markup())
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        await callback.answer("❌ Ошибка при открытии истории")


# =============== ADMIN REPLY TO PARENT (from chat view) ==================
@dp.callback_query(F.data.startswith("admin_reply_parent_"))
async def admin_reply_parent_chat_handler(callback: CallbackQuery):
    try:
        parent_id = int(callback.data.replace("admin_reply_parent_", ""))

        if parent_id not in active_chats:
            await callback.answer("❌ Родитель не найден")
            return

        parent_name = active_chats[parent_id].get("parent_name", await get_user_name(parent_id))
        tutor_name = active_chats[parent_id].get("tutor_name", "Неизвестно")

        admin_replies[callback.from_user.id] = {
            "target_id": parent_id,
            "target_type": "parent",
            "parent_name": parent_name,
            "tutor_name": tutor_name
        }

        # Avvalgi xabarlarni ko'rsatish
        chat_messages = [msg for msg in all_messages if msg.get('parent_id') == parent_id]
        recent_messages = chat_messages[-5:] if chat_messages else []

        text = f"✍️ <b>Ответ родителю</b>\n\n"
        text += f"👤 Родитель: {parent_name}\n"
        text += f"👨‍🏫 Тьютор: {tutor_name}\n"
        text += f"🆔 ID: {parent_id}\n\n"

        if recent_messages:
            text += "<b>Последние сообщения в чате:</b>\n"
            for msg in recent_messages:
                if msg.get('type') == 'parent_to_tutor':
                    text += f"👤 {msg.get('time', '')}: {msg.get('message', '')[:50]}...\n"
                elif msg.get('type') == 'tutor_to_parent':
                    text += f"👨‍🏫 {msg.get('time', '')}: {msg.get('message', '')[:50]}...\n"
                elif msg.get('type') == 'admin_to_parent':
                    admin_name = msg.get('admin_name', 'Admin')
                    text += f"👨‍💼 {msg.get('time', '')}: {msg.get('message', '')[:50]}...\n"
            text += "\n"

        text += "<b>Введите ваш ответ:</b>\n(Текст или медиа сообщение)\n/cancel - отменить"

        try:
            await callback.message.edit_text(text)
        except Exception as e:
            if "message is not modified" in str(e):
                await callback.answer("✅ Готово к ответу")
            else:
                try:
                    await callback.message.delete()
                except:
                    pass
                await callback.message.answer(text)

        await callback.answer()
    except Exception as e:
        logger.error(f"Admin reply parent from chat error: {e}")
        await callback.answer("❌ Ошибка")


# =============== PARENTLARGA JAVOB MENYUSI ==================

@dp.callback_query(F.data == "reply_to_parent_menu")
async def reply_to_parent_menu_handler(callback: CallbackQuery):
    if not active_chats:
        try:
            await callback.message.edit_text("❌ Нет активных чатов с родителями")
        except:
            await callback.answer("❌ Нет активных чатов с родителями")
        return

    kb = InlineKeyboardBuilder()

    for parent_id, chat_info in active_chats.items():
        tutor_name = chat_info.get("tutor_name", "Неизвестно")
        parent_name = chat_info.get("parent_name", await get_user_name(parent_id))

        kb.button(
            text=f"👤 {parent_name[:15]} → {tutor_name[:10]}",
            callback_data=f"reply_parent_{parent_id}"
        )

    kb.button(text="🔙 Назад в админ", callback_data="back_to_admin")
    kb.adjust(1)

    try:
        await callback.message.edit_text(
            f"👥 <b>Выберите родителя для ответа ({len(active_chats)} чатов):</b>",
            reply_markup=kb.as_markup()
        )
    except Exception as e:
        if "message is not modified" in str(e):
            await callback.answer("✅ Меню уже открыто")
        else:
            try:
                await callback.message.delete()
            except:
                pass
            await callback.message.answer(
                f"👥 <b>Выберите родителя для ответа ({len(active_chats)} чатов):</b>",
                reply_markup=kb.as_markup()
            )


# =============== PARENTGA JAVOB ==================

@dp.callback_query(F.data.startswith("reply_parent_"))
async def reply_parent_handler(callback: CallbackQuery):
    try:
        parent_id = int(callback.data.split("_")[2])
        admin_id = callback.from_user.id

        if parent_id not in active_chats:
            await callback.answer("❌ Родитель не найден")
            return

        parent_name = active_chats[parent_id].get("parent_name", await get_user_name(parent_id))
        tutor_name = active_chats[parent_id].get("tutor_name", "Неизвестно")

        admin_replies[admin_id] = {
            "target_id": parent_id,
            "target_type": "parent",
            "parent_name": parent_name,
            "tutor_name": tutor_name
        }

        # Avvalgi xabarlarni ko'rsatish
        chat_messages = [msg for msg in all_messages if msg.get('parent_id') == parent_id]
        recent_messages = chat_messages[-5:] if chat_messages else []

        text = f"✍️ <b>Ответ родителю</b>\n\n"
        text += f"👤 Родитель: {parent_name}\n"
        text += f"👨‍🏫 Тьютор: {tutor_name}\n"
        text += f"🆔 ID: {parent_id}\n\n"

        if recent_messages:
            text += "<b>Последние сообщения в чате:</b>\n"
            for msg in recent_messages:
                if msg.get('type') == 'parent_to_tutor':
                    text += f"👤 {msg.get('time', '')}: {msg.get('message', '')[:50]}...\n"
                elif msg.get('type') == 'tutor_to_parent':
                    text += f"👨‍🏫 {msg.get('time', '')}: {msg.get('message', '')[:50]}...\n"
                elif msg.get('type') == 'admin_to_parent':
                    admin_name = msg.get('admin_name', 'Admin')
                    text += f"👨‍💼 {msg.get('time', '')}: {msg.get('message', '')[:50]}...\n"
            text += "\n"

        text += "<b>Введите ваш ответ:</b>\n(Текст или медиа сообщение)\n/cancel - отменить"

        await callback.message.edit_text(text)
    except Exception as e:
        logger.error(f"Reply parent error: {e}")
        await callback.answer("❌ Ошибка при выборе родителя")


# =============== BACK TO ADMIN ==================

@dp.callback_query(F.data == "back_to_admin")
async def back_to_admin_handler(callback: CallbackQuery):
    try:
        await admin_panel(callback=callback)
    except Exception as e:
        logger.error(f"Back to admin error: {e}")
        await callback.answer("❌ Ошибка при переходе в админ панель")


# =============== OXIRGI XABARLAR ==================

@dp.callback_query(F.data == "recent_messages")
async def recent_messages_handler(callback: CallbackQuery):
    if not all_messages:
        try:
            await callback.message.edit_text("📭 Нет сообщений в истории")
        except:
            await callback.answer("📭 Нет сообщений в истории")
        return

    text = "📨 <b>Последние сообщения:</b>\n\n"

    for msg in all_messages[-15:]:  # Oxirgi 15 ta xabar
        if 'parent_id' in msg and 'tutor_name' in msg:
            parent_id = msg.get('parent_id')
            tutor_name = msg.get('tutor_name', 'Неизвестно')
            message_text = msg.get('message', '')[:50]
            time = msg.get('time', '')
            direction = msg.get('direction', '→')

            # Parent nomini olish
            parent_name = user_names.get(parent_id, f"User_{parent_id}")

            if direction == "→":
                text += f"🕒 {time} 👤{parent_name}→{tutor_name}: {message_text}\n"
            else:
                text += f"🕒 {time} {tutor_name}←{parent_name}: {message_text}\n"
        elif 'admin_id' in msg:
            admin_id = msg.get('admin_id')
            target_name = msg.get('parent_name') or msg.get('tutor_name', 'Неизвестно')
            message_text = msg.get('message', '')[:50]
            time = msg.get('time', '')

            admin_name = user_names.get(admin_id, f"Admin_{admin_id}")
            text += f"🕒 {time} 👨‍💼{admin_name}→{target_name}: {message_text}\n"

    try:
        await callback.message.edit_text(text)
    except Exception as e:
        if "message is not modified" in str(e):
            await callback.answer("✅ Список уже обновлен")
        else:
            try:
                await callback.message.delete()
            except:
                pass
            await callback.message.answer(text)


# =============== QUEUE NI TOZALASH ==================

@dp.callback_query(F.data == "clear_queue")
async def clear_queue_handler(callback: CallbackQuery):
    global message_queue
    message_queue = []
    save_bot_data()
    await callback.answer("✅ Очередь сообщений очищена")
    await admin_panel(callback=callback)


# =============== ADMIN JAVOB YUBORISH ==================

@dp.message(IsAdmin())
async def admin_reply_handler(message: types.Message):
    admin_id = message.from_user.id

    # /cancel komandasi
    if message.text and message.text.lower() == "/cancel":
        if admin_id in admin_replies:
            del admin_replies[admin_id]
        await message.answer("❌ Ответ отменен")
        await admin_panel(message=message)
        return

    # Admin javob holati
    if admin_id in admin_replies:
        state = admin_replies[admin_id]
        target_id = state["target_id"]
        target_type = state["target_type"]

        parent_name = state.get("parent_name", await get_user_name(target_id))
        tutor_name = state.get("tutor_name", "Неизвестно")

        try:
            # Xabarni yuborish
            await send_message_from_object(target_id, message)

            # DOIMIY tarixga saqlash
            message_data = {
                "admin_id": admin_id,
                "admin_name": await get_user_name(admin_id),
                "parent_id": target_id,
                "parent_name": parent_name,
                "tutor_name": tutor_name,
                "message": message.text or "Медиа сообщение",
                "is_media": not bool(message.text),
                "time": format_time(),
                "type": "admin_to_parent"
            }

            save_message_to_history(message_data)

            # Chat tarixiga saqlash
            save_chat_history(
                from_id=admin_id,
                to_id=target_id,
                message=message,
                user_type="admin"
            )

            # Boshqa adminlarga xabar
            admin_name = await get_user_name(admin_id)
            msg_preview = message.text[:100] if message.text else "Медиа сообщение"

            for other_admin in ADMINS:
                if other_admin != admin_id:
                    try:
                        await bot.send_message(
                            other_admin,
                            f"📨 <b>АДМИН → РОДИТЕЛЬ</b>\n\n"
                            f"👨‍💼 Админ: {admin_name}\n"
                            f"👤 Родитель: {parent_name}\n"
                            f"👨‍🏫 Тьютор: {tutor_name}\n"
                            f"🆔 ID: {target_id}\n"
                            f"💬 Сообщение: {msg_preview}\n"
                            f"🕒 Время: {format_time()}"
                        )
                    except:
                        pass

            await message.answer(f"✅ Ответ отправлен родителю {parent_name}!")

            # Holatni tozalash
            del admin_replies[admin_id]

            # Admin panelga qaytish
            await admin_panel(message=message)

        except Exception as e:
            await message.answer(f"❌ Ошибка отправки: {e}")
            logger.error(f"Admin reply error: {e}")
    else:
        # Oddiy admin xabari
        if message.text and message.text.startswith("/"):
            await admin_panel(message=message)
        else:
            # Admin xabar yozayotganda
            await admin_panel(message=message)


# =============== /start ==================

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id

    # Foydalanuvchi nomini saqlash
    await get_user_name(user_id)

    # Admin
    if user_id in ADMINS:
        await admin_panel(message=message)
        return

    # Tutor
    if user_id in TUTORS.values():
        await message.answer(
            "👨‍🏫 <b>Здравствуйте, тьютор!</b>\n\n"
            "Сообщения от родителей будут приходить сюда.\n"
            "Отвечайте на сообщения родителей или выберите родителя для ответа.\n\n"
            "Для ответа:\n"
            "1. Ответьте на сообщение родителя (reply)\n"
            "2. Или напишите сообщение и выберите родителя из списка"
        )
        return

    # Parent - avval tekshirish, chat mavjudmi
    if user_id in active_chats:
        chat_info = active_chats[user_id]
        tutor_name = chat_info.get("tutor_name", "Неизвестно")
        parent_name = chat_info.get("parent_name", await get_user_name(user_id))

        kb = InlineKeyboardBuilder()
        kb.button(text="✏️ Написать тьютору", callback_data="open_chat")
        kb.button(text="🔁 Сменить тьютора", callback_data="change_tutor")
        kb.adjust(1)

        await message.answer(
            f"👋 <b>С возвращением, {parent_name}!</b>\n\n"
            f"👨‍🏫 Ваш тьютор: {tutor_name}\n"
            f"🕒 Чат создан: {chat_info.get('start_time', 'Неизвестно')}\n\n"
            "Пишите сообщения, они будут направлены вашему тьютору.",
            reply_markup=kb.as_markup()
        )
        return

    # Yangi parent - tutorlarni tanlash
    kb = InlineKeyboardBuilder()
    for tutor_name, tid in TUTORS.items():
        # Используем tutor_id в callback_data чтобы не превышать лимит байт
        kb.button(text=tutor_name, callback_data=f"choose_tutor_{tid}")
    kb.adjust(1)

    await message.answer(
        "👋 <b>Здравствуйте, уважаемый родитель!</b>\n\n"
        "Пожалуйста, выберите вашего тьютора:",
        reply_markup=kb.as_markup()
    )


# ...existing code...

@dp.callback_query(F.data == "open_chat")
async def open_chat_handler(callback: CallbackQuery):
    """Открыть чат — показать подсказку и кнопку смены тьютора"""
    try:
        parent_id = callback.from_user.id
        if parent_id not in active_chats:
            await callback.answer("❌ Сначала выберите тьютора через /start", show_alert=True)
            return

        tutor_name = active_chats[parent_id].get("tutor_name", "Неизвестно")

        kb = InlineKeyboardBuilder()
        kb.button(text="🔁 Сменить тьютора", callback_data="change_tutor")
        kb.adjust(1)

        text = (
            f"✏️ <b>Напишите сообщение тьютору {tutor_name}.</b>\n\n"
            "Просто отправьте текст или медиа — оно будет направлено вашему тьютору.\n\n"
            "Если хотите, можете сменить тьютора:"
        )

        try:
            await callback.message.edit_text(text, reply_markup=kb.as_markup())
        except Exception:
            await callback.message.answer(text, reply_markup=kb.as_markup())

        await callback.answer()
    except Exception as e:
        logger.error(f"open_chat_handler error: {e}")
        await callback.answer("❌ Ошибка")

@dp.callback_query(F.data == "change_tutor")
async def change_tutor_handler(callback: CallbackQuery):
    """Показать список тьюторов для смены"""
    try:
        parent_id = callback.from_user.id

        kb = InlineKeyboardBuilder()
        for tutor_name, tid in TUTORS.items():
            # Используем tutor_id в callback_data
            kb.button(text=tutor_name, callback_data=f"choose_tutor_{tid}")
        kb.adjust(1)

        try:
            await callback.message.edit_text(
                "🔁 <b>Выберите нового тьютора:</b>",
                reply_markup=kb.as_markup()
            )
        except Exception:
            await callback.message.answer(
                "🔁 <b>Выберите нового тьютора:</b>",
                reply_markup=kb.as_markup()
            )

        await callback.answer()
    except Exception as e:
        logger.error(f"change_tutor_handler error: {e}")
        await callback.answer("❌ Ошибка")
# ...existing code...

# =============== TUTOR TANLASH ==================

@dp.callback_query(F.data.startswith("choose_tutor_"))
async def choose_tutor_handler(callback: CallbackQuery):
    suffix = callback.data.split("choose_tutor_", 1)[1]

    # Поддержка старых callback'ов (имя) и новых (id)
    tutor_id = None
    tutor_name = None

    # Попробуем разобрать как id
    try:
        tid = int(suffix)
    except:
        tid = None

    if tid is not None:
        tutor_id = tid
        tutor_name = next((n for n, i in TUTORS.items() if i == tutor_id), None)
    else:
        tutor_name = suffix
        tutor_id = TUTORS.get(tutor_name)

    if not tutor_id or not tutor_name:
        await callback.answer("❌ Тьютор не найден")
        return

    parent_id = callback.from_user.id

    # Parent nomini olish
    parent_name = await get_user_name(parent_id)

    # Agar oldingi chat bo'lsa va u boshqa tuteurga tegishli bo'lsa, uni yangilaymiz
    old = active_chats.get(parent_id)
    if old:
        old_tid = old.get("tutor_id")
        if old_tid and old_tid != tutor_id:
            try:
                if old_tid in tutor_chats and parent_id in tutor_chats[old_tid]:
                    tutor_chats[old_tid].remove(parent_id)
            except:
                pass

    # Chat ma'lumotlarini saqlash / yangilash
    active_chats[parent_id] = {
        "tutor_id": tutor_id,
        "tutor_name": tutor_name,
        "parent_name": parent_name,
        "start_time": active_chats.get(parent_id, {}).get("start_time", format_time())
    }
    parent_to_tutor[parent_id] = tutor_id

    # Tutor chatlariga qo'shish
    if tutor_id not in tutor_chats:
        tutor_chats[tutor_id] = []
    if parent_id not in tutor_chats[tutor_id]:
        tutor_chats[tutor_id].append(parent_id)

    # MA'LUMOTLARNI FAYLGA SAQLASH
    save_bot_data()

    # Tutorga xabar
    try:
        await bot.send_message(
            tutor_id,
            f"👤 <b>Новый/обновлённый родитель обратился к вам!</b>\n\n"
            f"👤 Родитель: {parent_name}\n"
            f"🆔 ID: {parent_id}\n"
            f"🕒 Время: {format_time()}\n\n"
            f"Ответьте на это сообщение для связи с родителем."
        )
    except Exception as e:
        logger.error(f"Tutor notification error: {e}")

    await callback.message.edit_text(
        f"✅ <b>Вы выбрали тьютора:</b> {tutor_name}\n\n"
        "Теперь отправляйте сообщения, они будут направлены вашему тьютору."
    )

    # Adminlarga xabar
    await notify_admins(
        f"🆕 <b>НОВЫЙ / ОБНОВЛЁННЫЙ ЧАТ</b>\n\n"
        f"👤 Родитель: {parent_name}\n"
        f"🆔 ID: {parent_id}\n"
        f"👨‍🏫 Тьютор: {tutor_name}\n"
        f"🕒 Время: {format_time()}"
    )


# =============== PARENT -> TUTOR ==================

@dp.message(IsParent())
async def parent_to_tutor_handler(message: types.Message):
    parent_id = message.from_user.id

    if parent_id not in active_chats:
        await message.answer("❌ Сначала выберите тьютора через /start")
        return

    chat_info = active_chats[parent_id]
    tutor_id = chat_info["tutor_id"]
    tutor_name = chat_info["tutor_name"]
    parent_name = chat_info.get("parent_name", await get_user_name(parent_id))

    # Xabar matnini olish
    if message.text:
        msg_text = message.text
        msg_preview = message.text[:100]
        is_media = False
    else:
        msg_text = "Медиа сообщение"
        msg_preview = "📎 Медиа сообщение"
        is_media = True

    # 1. Tutorga yuborish (hozir parent id metadata qo'shamiz)
    try:
        # Agar text bo'lsa, parent id va parent nomini matn ichiga qo'shamiz
        if message.text:
            await bot.send_message(
                tutor_id,
                f"{message.text}\n\n🔎 Родитель ID: {parent_id}\n👤 {parent_name}"
            )
        else:
            # media xabarni yuborib, keyin parent metadata yuboramiz
            await send_message_from_object(tutor_id, message)
            await bot.send_message(tutor_id, f"🔎 Родитель ID: {parent_id}\n👤 {parent_name}")

        logger.info(f"Parent {parent_name} -> Tutor {tutor_name}: message sent")
    except Exception as e:
        logger.error(f"Parent->Tutor error: {e}")
        await message.answer(f"❌ Ошибка отправки тьютору: {e}")
        return

    # 2. DOIMIY tarixga saqlash
    message_data = {
        "parent_id": parent_id,
        "parent_name": parent_name,
        "tutor_id": tutor_id,
        "tutor_name": tutor_name,
        "message": msg_text,
        "is_media": is_media,
        "time": format_time(),
        "direction": "→",
        "type": "parent_to_tutor"
    }

    save_message_to_history(message_data)

    # 3. Queue ga qo'shish
    message_queue.append(message_data)

    # 4. Tarixga saqlash
    save_chat_history(
        from_id=parent_id,
        to_id=tutor_id,
        message=message,
        user_type="parent"
    )

    # 5. Adminlarga batafsil xabar
    admin_message = (
        f"📨 <b>РОДИТЕЛЬ → ТЬЮТОР</b>\n\n"
        f"👤 <b>Родитель:</b> {parent_name}\n"
        f"🆔 ID: {parent_id}\n"
        f"👨‍🏫 <b>Тьютор:</b> {tutor_name}\n"
        f"💬 <b>Сообщение:</b> {msg_preview}\n"
    )

    if is_media and message.caption:
        admin_message += f"📝 <b>Подпись:</b> {message.caption[:100]}\n"

    admin_message += f"🕒 <b>Время:</b> {format_time()}"

    await notify_admins(admin_message)

    await message.answer("✅ Сообщение отправлено тьютору!")


# =============== TUTOR -> PARENT (REPLY QILGANDA) ==================

@dp.message(IsTutor())
async def tutor_to_parent_reply(message: types.Message):
    """Tutor reply qilganda (reply mavjud bo'lganda)"""
    tutor_id = message.from_user.id

    # Tutor kim ekanligini aniqlash
    tutor_name = None
    for name, tid in TUTORS.items():
        if tid == tutor_id:
            tutor_name = name
            break

    if not tutor_name:
        await message.answer("❌ Вы не зарегистрины как тьютор")
        return

    # Xabar matnini olish
    if message.text:
        msg_text = message.text
        msg_preview = message.text[:100]
        is_media = False
    else:
        msg_text = "Медиа сообщение"
        msg_preview = "📎 Медиа сообщение"
        is_media = True

    # Agar reply bo'lsa
    if message.reply_to_message:
        reply_text = message.reply_to_message.text or message.reply_to_message.caption or ""

        # Reply qilingan xabarda parent ID ni qidirish
        parent_id = None

        if "Родитель ID:" in reply_text:
            try:
                lines = reply_text.split('\n')
                for line in lines:
                    if "Родитель ID:" in line:
                        parent_id = int(line.split(":")[1].strip())
                        break
            except Exception as e:
                logger.error(f"Parent ID parse error: {e}")

        # Agar parent ID topilsa
        if parent_id and parent_id in active_chats:
            # Parent nomini olish
            parent_info = active_chats.get(parent_id, {})
            parent_name = parent_info.get("parent_name", await get_user_name(parent_id))

            # 1. Parentga yuborish
            try:
                await send_message_from_object(parent_id, message)
                logger.info(f"Tutor {tutor_name} -> Parent {parent_name}: message sent")
            except Exception as e:
                logger.error(f"Tutor->Parent send error: {e}")
                await message.answer(f"❌ Ошибка отправки родителю: {e}")
                return

            # 2. DOIMIY tarixga saqlash
            message_data = {
                "parent_id": parent_id,
                "parent_name": parent_name,
                "tutor_id": tutor_id,
                "tutor_name": tutor_name,
                "message": msg_text,
                "is_media": is_media,
                "time": format_time(),
                "direction": "←",
                "type": "tutor_to_parent"
            }

            save_message_to_history(message_data)

            # 3. Tarixga saqlash
            save_chat_history(
                from_id=tutor_id,
                to_id=parent_id,
                message=message,
                user_type="tutor"
            )

            # 4. Adminlarga batafsil xabar
            admin_message = (
                f"📨 <b>ТЬЮТОР → РОДИТЕЛЬ</b>\n\n"
                f"👨‍🏫 <b>Тьютор:</b> {tutor_name}\n"
                f"🆔 ID: {tutor_id}\n"
                f"👤 <b>Родитель:</b> {parent_name}\n"
                f"🆔 ID: {parent_id}\n"
                f"💬 <b>Сообщение:</b> {msg_preview}\n"
            )

            if is_media and message.caption:
                admin_message += f"📝 <b>Подпись:</b> {message.caption[:100]}\n"

            admin_message += f"🕒 <b>Время:</b> {format_time()}"

            await notify_admins(admin_message)

            await message.answer(f"✅ Ответ отправлен родителю {parent_name}!")
            return

    # Agar reply bo'lmasa, parentlarni ko'rsatish
    await show_tutor_parents_menu(tutor_id, tutor_name, message)


# =============== TUTOR PARENTLAR MENYUSI ==================

async def show_tutor_parents_menu(tutor_id, tutor_name, message):
    """Tutorga parentlarni tanlash menyusini ko'rsatish"""
    if tutor_id not in tutor_chats or not tutor_chats[tutor_id]:
        await message.answer("❌ У вас нет активных чатов с родителями")
        return

    kb = InlineKeyboardBuilder()
    for parent_id in tutor_chats[tutor_id]:
        parent_info = active_chats.get(parent_id, {})
        parent_name = parent_info.get("parent_name", await get_user_name(parent_id))

        kb.button(text=f"👤 {parent_name}", callback_data=f"tutor_select_{parent_id}")

    kb.adjust(1)

    await message.answer(
        "👥 <b>Выберите родителя для ответа:</b>\n\n"
        "Или ответьте на сообщение родителя (reply)",
        reply_markup=kb.as_markup()
    )


# =============== TUTOR PARENT TANLASH ==================

@dp.callback_query(F.data.startswith("tutor_select_"))
async def tutor_select_parent_handler(callback: CallbackQuery):
    parent_id = int(callback.data.split("_")[2])
    tutor_id = callback.from_user.id

    # Parent nomini olish
    parent_info = active_chats.get(parent_id, {})
    parent_name = parent_info.get("parent_name", await get_user_name(parent_id))

    # Saqlash
    tutor_selections[tutor_id] = {
        "parent_id": parent_id,
        "parent_name": parent_name
    }

    await callback.message.edit_text(
        f"✅ Вы выбрали родителя {parent_name}\n\n"
        f"Теперь отправьте сообщение, оно будет направлено этому родителю."
    )


# =============== TUTOR -> PARENT (TANLAGAN PARENTGA) ==================

@dp.message(IsTutor(), ~F.reply_to_message.exists())
async def tutor_to_parent_selected(message: types.Message):
    """Tutor tanlagan parentga xabar yuboradi (reply yo'q bo'lsa)"""
    tutor_id = message.from_user.id

    # Tutor kim ekanligini aniqlash
    tutor_name = None
    for name, tid in TUTORS.items():
        if tid == tutor_id:
            tutor_name = name
            break

    if not tutor_name:
        return

    # Xabar matnini olish
    if message.text:
        msg_text = message.text
        msg_preview = message.text[:100]
        is_media = False
    else:
        msg_text = "Медиа сообщение"
        msg_preview = "📎 Медиа сообщение"
        is_media = True

    # Agar parent tanlangan bo'lsa
    if tutor_id in tutor_selections:
        selection = tutor_selections[tutor_id]
        parent_id = selection["parent_id"]
        parent_name = selection["parent_name"]

        try:
            # 1. Parentga yuborish
            await send_message_from_object(parent_id, message)
            logger.info(f"Tutor {tutor_name} -> Parent {parent_name} (selected): message sent")

            # 2. DOIMIY tarixga saqlash
            message_data = {
                "parent_id": parent_id,
                "parent_name": parent_name,
                "tutor_id": tutor_id,
                "tutor_name": tutor_name,
                "message": msg_text,
                "is_media": is_media,
                "time": format_time(),
                "direction": "←",
                "type": "tutor_to_parent"
            }

            save_message_to_history(message_data)

            # 3. Tarixga saqlash
            save_chat_history(
                from_id=tutor_id,
                to_id=parent_id,
                message=message,
                user_type="tutor"
            )

            # 4. Adminlarga batafsil xabar
            admin_message = (
                f"📨 <b>ТЬЮТОР → РОДИТЕЛЬ</b>\n\n"
                f"👨‍🏫 <b>Тьютор:</b> {tutor_name}\n"
                f"🆔 ID: {tutor_id}\n"
                f"👤 <b>Родитель:</b> {parent_name}\n"
                f"🆔 ID: {parent_id}\n"
                f"💬 <b>Сообщение:</b> {msg_preview}\n"
            )

            if is_media and message.caption:
                admin_message += f"📝 <b>Подпись:</b> {message.caption[:100]}\n"

            admin_message += f"🕒 <b>Время:</b> {format_time()}"

            await notify_admins(admin_message)

            await message.answer(f"✅ Сообщение отправлено родителю {parent_name}!")

        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
            logger.error(f"Tutor->Parent selected error: {e}")
    else:
        # Agar parent tanlanmagan bo'lsa, menyuni ko'rsatish
        await show_tutor_parents_menu(tutor_id, tutor_name, message)


# =============== YORDAMCHI FUNKTSIYALAR ==================

async def send_message_from_object(user_id, message):
    """Message object dan xabar yuborish"""
    try:
        if message.text:
            await bot.send_message(user_id, message.text)
        elif message.photo:
            await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "")
        elif message.video:
            await bot.send_video(user_id, message.video.file_id, caption=message.caption or "")
        elif message.document:
            await bot.send_document(user_id, message.document.file_id, caption=message.caption or "")
        elif message.voice:
            await bot.send_voice(user_id, message.voice.file_id)
        elif message.audio:
            await bot.send_audio(user_id, message.audio.file_id, caption=message.caption or "")
        else:
            await bot.send_message(user_id, "📎 Получено медиа-сообщение")
        return True
    except Exception as e:
        logger.error(f"Send message from object error to {user_id}: {e}")
        raise


def save_chat_history(from_id, to_id, message, user_type):
    """Chat tarixini saqlash"""
    try:
        # Kimga yuborilganligiga qarab fayl nomi
        file_id = to_id
        history_file = f"chat_logs/chat_{file_id}.json"

        # Yaratish yoki yuklash
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []

        # Kim yuborgan
        if user_type == "parent":
            sender = "Родитель"
        elif user_type == "tutor":
            sender = "Тьютор"
        else:
            sender = "Админ"

        # Xabar ma'lumotlari
        msg_data = {
            "time": format_time(),
            "from": sender,
            "from_id": from_id,
            "to_id": to_id,
            "type": "text"
        }

        if message.text:
            msg_data["text"] = message.text
        elif message.caption:
            msg_data["text"] = message.caption
            msg_data["type"] = "media"
        else:
            msg_data["text"] = "Медиа сообщение"
            msg_data["type"] = "media"

        history.append(msg_data)

        # Saqlash (max 500 ta xabar)
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history[-500:], f, ensure_ascii=False, indent=2)

        logger.info(f"History saved: {sender} {from_id} -> {to_id}")

    except Exception as e:
        logger.error(f"Save history error: {e}")


def load_chat_history(chat_id):
    """Chat tarixini yuklash"""
    history_file = f"chat_logs/chat_{chat_id}.json"

    if not os.path.exists(history_file):
        return []

    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Load history error: {e}")
        return []


async def notify_admins(text):
    """Adminlarga xabar yuborish"""
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, text)
            logger.info(f"Notification sent to admin {admin_id}")
        except Exception as e:
            logger.error(f"Notify admin error {admin_id}: {e}")


# =============== MAIN ==================

async def main():
    logger.info("🚀 Бот запускается...")

    # DOIMIY MA'LUMOTLARNI YUKLASH
    load_bot_data()

    try:
        me = await bot.get_me()
        logger.info(f"✅ Бот: @{me.username}")
        logger.info(f"✅ Админы: {ADMINS}")
        logger.info(f"✅ Тьюторы: {TUTORS}")
        logger.info(f"✅ Загружено чатов: {len(active_chats)}")
        logger.info(f"✅ Загружено сообщений: {len(all_messages)}")
        logger.info(f"✅ Загружено имён пользователей: {len(user_names)}")

        # Adminlarga start xabari
        for admin_id in ADMINS:
            try:
                await bot.send_message(
                    admin_id,
                    f"🤖 Бот запущен!\n"
                    f"/admin - админ панель\n"
                    f"Загружено чатов: {len(active_chats)}\n"
                    f"Всего сообщений: {len(all_messages)}\n"
                    f"Время: {format_time()}"
                )
            except Exception as e:
                logger.error(f"Admin start message error {admin_id}: {e}")
    except Exception as e:
        logger.error(f"❌ Бот ошибка: {e}")
        return

    # Avtomatik saqlash vazifasi
    async def auto_save():
        """Har 5 minutda bir ma'lumotlarni avtomatik saqlash"""
        while True:
            await asyncio.sleep(300)  # 5 minut
            try:
                if save_bot_data():
                    logger.info(f"🔄 Ma'lumotlar avtomatik saqlandi")
            except Exception as e:
                logger.error(f"Avtosaqlashda xato: {e}")

    # Avtomatik saqlashni ishga tushirish
    asyncio.create_task(auto_save())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())