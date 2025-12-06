# pro_tutor_with_history.py
import asyncio
import aiosqlite
from typing import Dict, Set, Optional
from collections import defaultdict
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, BaseFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ---------------- SETTINGS ----------------
BOT_TOKEN = "7691876985:AAF00PYw5m2W-tqcr_NnxcT5_KVwJ7SxoUA" #gubkin_bot
ADMIN_IDS: Set[int] = {7345258559}  # <-- replace with real admin IDs

# Initial in-memory tutor list (name -> telegram_id).
# Admins can add/remove tutors; we'll sync changes to DB at startup.
TUTORS: Dict[str, int] = {
    "Gulhayo A": 5361061503,
    "Doniyor B": 6642417048,
    "Elbobo C": 920022557
}

# ---------------- IN-MEMORY STORAGE ----------------
selected_tutor: Dict[int, int] = {}                # parent_id -> tutor_id
active_chats: Dict[int, Set[int]] = defaultdict(set)  # tutor_id -> set(parent_id)
last_parent_message: Dict[int, int] = {}           # tutor_id -> last parent_id
tutor_selected_parent: Dict[int, Optional[int]] = {}  # tutor reply selection
unread_counts: Dict[int, int] = defaultdict(int)
tutor_status: Dict[int, bool] = {tid: False for tid in TUTORS.values()}

# ---------------- BOT ----------------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_PATH = "tutor_bot.db"


# ------------------- DATABASE HELPERS -------------------
async def init_db():
    """Create tables if not exists and load tutors into memory."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS tutors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                tg_id INTEGER NOT NULL UNIQUE
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                tutor_id INTEGER,
                sender TEXT,           -- 'parent' / 'tutor' / 'admin'
                content TEXT,
                msg_type TEXT,        -- text/photo/document/video/audio/voice/sticker/location/contact
                file_id TEXT,
                timestamp TEXT
            )
            """
        )
        await db.commit()

        # Ensure initial TUTORS are in DB
        for name, tg in TUTORS.items():
            # insert or ignore
            await db.execute(
                "INSERT OR IGNORE INTO tutors (name, tg_id) VALUES (?, ?)",
                (name, tg)
            )
        await db.commit()

        # Load tutors from DB to in-memory TUTORS (overwrites previous)
        rows = await db.execute_fetchall("SELECT name, tg_id FROM tutors")
        if rows:
            TUTORS.clear()
            for name, tg in rows:
                TUTORS[name] = tg


async def add_tutor_db(name: str, tg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO tutors (name, tg_id) VALUES (?, ?)", (name, tg_id))
        await db.commit()


async def remove_tutor_db(tg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM tutors WHERE tg_id = ?", (tg_id,))
        await db.commit()


async def log_message(parent_id: Optional[int], tutor_id: Optional[int], sender: str, content: Optional[str],
                      msg_type: str, file_id: Optional[str]):
    ts = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (parent_id, tutor_id, sender, content, msg_type, file_id, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (parent_id, tutor_id, sender, content, msg_type, file_id, ts)
        )
        await db.commit()


async def get_history_by_parent(parent_id: int, limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        rows = await db.execute_fetchall(
            "SELECT id, parent_id, tutor_id, sender, content, msg_type, file_id, timestamp "
            "FROM messages WHERE parent_id = ? ORDER BY id DESC LIMIT ?",
            (parent_id, limit)
        )
        return rows


async def get_history_by_tutor(tg_id: int, limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        rows = await db.execute_fetchall(
            "SELECT id, parent_id, tutor_id, sender, content, msg_type, file_id, timestamp "
            "FROM messages WHERE tutor_id = ? ORDER BY id DESC LIMIT ?",
            (tg_id, limit)
        )
        return rows


# ---------------- FILTERS ----------------
class IsTutor(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in TUTORS.values()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def get_tutor_name_by_id(tid: int) -> Optional[str]:
    for name, uid in TUTORS.items():
        if uid == tid:
            return name
    return None


# ---------------- UTILS: forward and log media/text ----------------
async def forward_media_to_chat_and_log(tutor_id: int, parent: types.User, msg: types.Message, header: str):
    """
    Forward different media types to tutor preserving content and log message to DB.
    """
    # TEXT
    if msg.text:
        await bot.send_message(chat_id=tutor_id, text=f"{header}\n{msg.text}")
        await log_message(parent_id=parent.id, tutor_id=tutor_id, sender="parent", content=msg.text, msg_type="text", file_id=None)
        return

    # PHOTO
    if msg.photo:
        file_id = msg.photo[-1].file_id
        caption = msg.caption or ""
        await bot.send_photo(chat_id=tutor_id, photo=file_id, caption=f"{header}\n{caption}")
        await log_message(parent_id=parent.id, tutor_id=tutor_id, sender="parent", content=caption, msg_type="photo", file_id=file_id)
        return

    # DOCUMENT
    if msg.document:
        file_id = msg.document.file_id
        caption = msg.caption or ""
        await bot.send_document(chat_id=tutor_id, document=file_id, caption=f"{header}\n{caption}")
        await log_message(parent_id=parent.id, tutor_id=tutor_id, sender="parent", content=caption, msg_type="document", file_id=file_id)
        return

    # VIDEO
    if msg.video:
        file_id = msg.video.file_id
        caption = msg.caption or ""
        await bot.send_video(chat_id=tutor_id, video=file_id, caption=f"{header}\n{caption}")
        await log_message(parent_id=parent.id, tutor_id=tutor_id, sender="parent", content=caption, msg_type="video", file_id=file_id)
        return

    # AUDIO
    if msg.audio:
        file_id = msg.audio.file_id
        caption = msg.caption or ""
        await bot.send_audio(chat_id=tutor_id, audio=file_id, caption=f"{header}\n{caption}")
        await log_message(parent_id=parent.id, tutor_id=tutor_id, sender="parent", content=caption, msg_type="audio", file_id=file_id)
        return

    # VOICE
    if msg.voice:
        file_id = msg.voice.file_id
        await bot.send_voice(chat_id=tutor_id, voice=file_id, caption=header)
        await log_message(parent_id=parent.id, tutor_id=tutor_id, sender="parent", content=None, msg_type="voice", file_id=file_id)
        return

    # STICKER
    if msg.sticker:
        file_id = msg.sticker.file_id
        await bot.send_message(chat_id=tutor_id, text=header)
        await bot.send_sticker(chat_id=tutor_id, sticker=file_id)
        await log_message(parent_id=parent.id, tutor_id=tutor_id, sender="parent", content=None, msg_type="sticker", file_id=file_id)
        return

    # LOCATION
    if msg.location:
        await bot.send_message(chat_id=tutor_id, text=header)
        await bot.send_location(chat_id=tutor_id, latitude=msg.location.latitude, longitude=msg.location.longitude)
        await log_message(parent_id=parent.id, tutor_id=tutor_id, sender="parent", content=None, msg_type="location", file_id=None)
        return

    # CONTACT
    if msg.contact:
        contact_info = f"{msg.contact.first_name} {getattr(msg.contact, 'last_name', '')} {msg.contact.phone_number}"
        await bot.send_message(chat_id=tutor_id, text=f"{header}\nContact: {contact_info}")
        await log_message(parent_id=parent.id, tutor_id=tutor_id, sender="parent", content=contact_info, msg_type="contact", file_id=None)
        return

    # Unknown
    await bot.send_message(chat_id=tutor_id, text=f"{header}\n(Сообщение содержит неподдерживаемый тип или пусто.)")
    await log_message(parent_id=parent.id, tutor_id=tutor_id, sender="parent", content=None, msg_type="unknown", file_id=None)


async def forward_media_from_tutor_to_parent_and_log(parent_id: int, tutor: types.User, msg: types.Message):
    header = "📨 Ответ от тьютора:\n"
    # TEXT
    if msg.text:
        await bot.send_message(chat_id=parent_id, text=f"{header}{msg.text}")
        await log_message(parent_id=parent_id, tutor_id=tutor.id, sender="tutor", content=msg.text, msg_type="text", file_id=None)
        return

    # PHOTO
    if msg.photo:
        file_id = msg.photo[-1].file_id
        caption = msg.caption or ""
        await bot.send_photo(chat_id=parent_id, photo=file_id, caption=f"{header}\n{caption}")
        await log_message(parent_id=parent_id, tutor_id=tutor.id, sender="tutor", content=caption, msg_type="photo", file_id=file_id)
        return

    # DOCUMENT
    if msg.document:
        file_id = msg.document.file_id
        caption = msg.caption or ""
        await bot.send_document(chat_id=parent_id, document=file_id, caption=f"{header}\n{caption}")
        await log_message(parent_id=parent_id, tutor_id=tutor.id, sender="tutor", content=caption, msg_type="document", file_id=file_id)
        return

    # VIDEO
    if msg.video:
        file_id = msg.video.file_id
        caption = msg.caption or ""
        await bot.send_video(chat_id=parent_id, video=file_id, caption=f"{header}\n{caption}")
        await log_message(parent_id=parent_id, tutor_id=tutor.id, sender="tutor", content=caption, msg_type="video", file_id=file_id)
        return

    # VOICE
    if msg.voice:
        file_id = msg.voice.file_id
        await bot.send_voice(chat_id=parent_id, voice=file_id, caption=header)
        await log_message(parent_id=parent_id, tutor_id=tutor.id, sender="tutor", content=None, msg_type="voice", file_id=file_id)
        return

    # STICKER
    if msg.sticker:
        file_id = msg.sticker.file_id
        await bot.send_message(chat_id=parent_id, text=header)
        await bot.send_sticker(chat_id=parent_id, sticker=file_id)
        await log_message(parent_id=parent_id, tutor_id=tutor.id, sender="tutor", content=None, msg_type="sticker", file_id=file_id)
        return

    # LOCATION
    if msg.location:
        await bot.send_message(chat_id=parent_id, text=header)
        await bot.send_location(chat_id=parent_id, latitude=msg.location.latitude, longitude=msg.location.longitude)
        await log_message(parent_id=parent_id, tutor_id=tutor.id, sender="tutor", content=None, msg_type="location", file_id=None)
        return

    # CONTACT
    if msg.contact:
        contact_info = f"{msg.contact.first_name} {getattr(msg.contact, 'last_name', '')} {msg.contact.phone_number}"
        await bot.send_message(chat_id=parent_id, text=f"{header}\nContact: {contact_info}")
        await log_message(parent_id=parent_id, tutor_id=tutor.id, sender="tutor", content=contact_info, msg_type="contact", file_id=None)
        return

    # Unknown
    await bot.send_message(chat_id=parent_id, text=f"{header}\n(Сообщение содержит неподдерживаемый тип или пусто.)")
    await log_message(parent_id=parent_id, tutor_id=tutor.id, sender="tutor", content=None, msg_type="unknown", file_id=None)


# ---------------- COMMANDS / HANDLERS ----------------
@dp.message(Command("start"))
async def start_handler(msg: types.Message):
    user_id = msg.from_user.id

    # Admin gets admin panel
    if is_admin(user_id):
        kb = InlineKeyboardBuilder()
        kb.button(text="Админ-панель", callback_data="admin_panel")
        kb.adjust(1)
        await msg.answer("Здравствуйте, админ. Нажмите кнопку ниже для доступа к панели.", reply_markup=kb.as_markup())
        return

    # Tutor: no menu
    if user_id in TUTORS.values():
        tutor_selected_parent[user_id] = tutor_selected_parent.get(user_id) or None
        await msg.answer("Здравствуйте, тьютор! У вас нет меню в этом боте.")
        return

    # Parent: show tutors
    kb = InlineKeyboardBuilder()
    for name in TUTORS:
        kb.button(text=name, callback_data=name)
    kb.adjust(1)
    await msg.answer("Здравствуйте!\nПожалуйста, выберите вашего тьютора:", reply_markup=kb.as_markup())


@dp.callback_query()
async def choose_tutor(call: types.CallbackQuery):
    user_id = call.from_user.id

    # Ignore if tutor or admin pressed
    if user_id in TUTORS.values() or is_admin(user_id):
        await call.answer()
        return

    tutor_name = call.data
    tutor_id = TUTORS.get(tutor_name)
    if not tutor_id:
        await call.answer("Неверный выбор.", show_alert=True)
        return

    selected_tutor[user_id] = tutor_id
    await call.message.answer(f"Вы выбрали тьютора: {tutor_name}.\nТеперь отправьте сообщение (текст или медиа).")
    await call.answer()


# Parent -> Tutor (handles text + media), logs to DB
@dp.message()
async def parent_to_tutor(msg: types.Message):
    user_id = msg.from_user.id

    # ignore tutor messages here
    if user_id in TUTORS.values():
        return

    # admin messages shouldn't be forwarded as parent messages
    if is_admin(user_id):
        await msg.answer("Сообщение принято (админ). Оно не будет отправлено тьютору.")
        return

    if user_id not in selected_tutor:
        await msg.answer("Пожалуйста, сначала выберите тьютора через /start.")
        return

    tutor_id = selected_tutor[user_id]
    parent_title = f"📩 Сообщение от родителя:\n👤 {msg.from_user.full_name} (id: {user_id})"

    await forward_media_to_chat_and_log(tutor_id=tutor_id, parent=msg.from_user, msg=msg, header=parent_title)

    active_chats[tutor_id].add(user_id)
    last_parent_message[tutor_id] = user_id
    unread_counts[user_id] += 1

    await msg.answer("✔ Сообщение отправлено!")


# Tutor -> Parent (reply). Tutors can set selected parent or reply to last_parent_message.
@dp.message(IsTutor())
async def tutor_reply(msg: types.Message):
    tutor_id = msg.from_user.id

    # choose parent to reply: explicit selection preferred
    parent_id_to_reply = tutor_selected_parent.get(tutor_id)
    if parent_id_to_reply is None:
        parent_id_to_reply = last_parent_message.get(tutor_id)

    if not parent_id_to_reply:
        await msg.answer("Пока нет активных сообщений от родителей.")
        return

    # send and log
    await forward_media_from_tutor_to_parent_and_log(parent_id=parent_id_to_reply, tutor=msg.from_user, msg=msg)

    # reset unread counter
    unread_counts[parent_id_to_reply] = 0
    # keep last_parent_message as this parent
    last_parent_message[tutor_id] = parent_id_to_reply

    await msg.answer("✔ Ответ был отправлен родителю!")


# Tutor selects a parent to reply to: /select_parent <parent_id>
@dp.message(Command("select_parent"))
async def select_parent_cmd(msg: types.Message):
    tutor_id = msg.from_user.id
    if tutor_id not in TUTORS.values():
        await msg.answer("Эта команда только для тьюторов.")
        return
    parts = (msg.text or "").strip().split()
    if len(parts) != 2:
        await msg.answer("Использование: /select_parent <parent_id>")
        return
    try:
        pid = int(parts[1])
    except ValueError:
        await msg.answer("Неверный parent_id.")
        return
    tutor_selected_parent[tutor_id] = pid
    await msg.answer(f"Вы выбрали родителя с id {pid} для ответов.")


@dp.message(Command("clear_parent"))
async def clear_parent(msg: types.Message):
    tutor_id = msg.from_user.id
    if tutor_id not in TUTORS.values():
        await msg.answer("Эта команда только для тьюторов.")
        return
    tutor_selected_parent[tutor_id] = None
    await msg.answer("Выбор родителя очищен. Теперь ответы будут идти последнему написавшему родителю.")


# ---------------- ADMIN PANEL & COMMANDS ----------------
@dp.message(Command("admin"))
async def admin_panel(msg: types.Message):
    user_id = msg.from_user.id
    if not is_admin(user_id):
        await msg.answer("У вас нет доступа к админ панели.")
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить тьютора (usage: /add_tutor Имя ID)", callback_data="admin_add")
    kb.button(text="➖ Удалить тьютора (usage: /remove_tutor ID)", callback_data="admin_remove")
    kb.button(text="📋 Список тьюторов", callback_data="admin_list_tutors")
    kb.button(text="📜 История по родителю (usage: /history_parent ID)", callback_data="admin_history_parent")
    kb.button(text="📜 История по тьютору (usage: /history_tutor ID)", callback_data="admin_history_tutor")
    kb.button(text="💬 Активные чаты", callback_data="admin_active_chats")
    kb.button(text="🔔 Непрочитанные", callback_data="admin_unread")
    kb.adjust(1)
    await msg.answer("Админ-панель:", reply_markup=kb.as_markup())


@dp.callback_query()
async def admin_callbacks(call: types.CallbackQuery):
    user_id = call.from_user.id
    if not is_admin(user_id):
        await call.answer("Нет доступа.")
        return

    data = call.data
    if data == "admin_add":
        await call.message.answer("Чтобы добавить тьютора используйте команду:\n/add_tutor Имя ID")
    elif data == "admin_remove":
        await call.message.answer("Чтобы удалить тьютора используйте команду:\n/remove_tutor ID")
    elif data == "admin_list_tutors":
        if not TUTORS:
            await call.message.answer("Список тьюторов пуст.")
        else:
            text = "Список тьюторов:\n" + "\n".join([f"{name} — {uid}" for name, uid in TUTORS.items()])
            await call.message.answer(text)
    elif data == "admin_active_chats":
        lines = []
        for tid, parents in active_chats.items():
            name = get_tutor_name_by_id(tid) or str(tid)
            lines.append(f"{name} ({tid}) — {len(parents)} активных")
        await call.message.answer("Активные чаты:\n" + ("\n".join(lines) if lines else "Нет активных чатов."))
    elif data == "admin_unread":
        text = "Непрочитанные сообщения:\n" + "\n".join(f"{pid}: {cnt}" for pid, cnt in unread_counts.items() if cnt > 0) or "Нет непрочитанных"
        await call.message.answer(text)
    elif data == "admin_history_parent":
        await call.message.answer("Используйте команду: /history_parent <parent_id>")
    elif data == "admin_history_tutor":
        await call.message.answer("Используйте команду: /history_tutor <tutor_id>")
    await call.answer()


@dp.message(Command("add_tutor"))
async def add_tutor_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("У вас нет прав.")
        return
    parts = (msg.text or "").strip().split(maxsplit=2)
    if len(parts) < 3:
        await msg.answer("Использование: /add_tutor Имя ID")
        return
    name = parts[1]
    try:
        tid = int(parts[2])
    except ValueError:
        await msg.answer("ID должен быть числом.")
        return
    TUTORS[name] = tid
    tutor_status[tid] = False
    await add_tutor_db(name, tid)
    await msg.answer(f"Тьютор {name} с id {tid} добавлен.")


@dp.message(Command("remove_tutor"))
async def remove_tutor_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("У вас нет прав.")
        return
    parts = (msg.text or "").strip().split()
    if len(parts) != 2:
        await msg.answer("Использование: /remove_tutor ID")
        return
    try:
        tid = int(parts[1])
    except ValueError:
        await msg.answer("ID должен быть числом.")
        return
    # remove entry by value
    removed = None
    for name, uid in list(TUTORS.items()):
        if uid == tid:
            removed = name
            del TUTORS[name]
    tutor_status.pop(tid, None)
    active_chats.pop(tid, None)
    last_parent_message.pop(tid, None)
    tutor_selected_parent.pop(tid, None)
    await remove_tutor_db(tid)
    if removed:
        await msg.answer(f"Тьютор {removed} ({tid}) удалён.")
    else:
        await msg.answer("Тьютор не найден.")


@dp.message(Command("list_tutors"))
async def list_tutors_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("У вас нет прав.")
        return
    if not TUTORS:
        await msg.answer("Список тьюторов пуст.")
    else:
        await msg.answer("Список тьюторов:\n" + "\n".join([f"{name} — {uid}" for name, uid in TUTORS.items()]))


@dp.message(Command("history_parent"))
async def history_parent_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("У вас нет прав.")
        return
    parts = (msg.text or "").strip().split()
    if len(parts) != 2:
        await msg.answer("Использование: /history_parent <parent_id>")
        return
    try:
        pid = int(parts[1])
    except ValueError:
        await msg.answer("Неверный parent_id.")
        return
    rows = await get_history_by_parent(pid, limit=100)
    if not rows:
        await msg.answer("История пустая.")
        return
    text_lines = []
    for r in rows:
        _, parent_id, tutor_id, sender, content, msg_type, file_id, ts = r
        tname = get_tutor_name_by_id(tutor_id) or str(tutor_id)
        text_lines.append(f"[{ts}] {sender} -> tutor:{tname} type:{msg_type} content:{(content[:80] + '...') if content and len(content) > 80 else content or file_id}")
    await msg.answer("\n".join(text_lines))


@dp.message(Command("history_tutor"))
async def history_tutor_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("У вас нет прав.")
        return
    parts = (msg.text or "").strip().split()
    if len(parts) != 2:
        await msg.answer("Использование: /history_tutor <tutor_id>")
        return
    try:
        tid = int(parts[1])
    except ValueError:
        await msg.answer("Неверный tutor_id.")
        return
    rows = await get_history_by_tutor(tid, limit=100)
    if not rows:
        await msg.answer("История пустая.")
        return
    text_lines = []
    for r in rows:
        _, parent_id, tutor_id, sender, content, msg_type, file_id, ts = r
        text_lines.append(f"[{ts}] parent:{parent_id} {sender} type:{msg_type} content:{(content[:80] + '...') if content and len(content) > 80 else content or file_id}")
    await msg.answer("\n".join(text_lines))


# ----------------- Misc admin commands -----------------
@dp.message(Command("unread_stats"))
async def unread_stats_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("У вас нет прав.")
        return
    text = "Непрочитанные сообщения:\n"
    any_unread = False
    for pid, cnt in unread_counts.items():
        if cnt > 0:
            text += f"{pid}: {cnt}\n"
            any_unread = True
    if not any_unread:
        text = "Нет непрочитанных сообщений."
    await msg.answer(text)


# ------------------- MAIN -------------------
async def main():
    await init_db()
    # load tutors into in-memory dict is already done by init_db
    await bot.delete_webhook(drop_pending_updates=True)
    print("Pro bot with history started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
