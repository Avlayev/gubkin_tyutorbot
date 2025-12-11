# ADMIN_ID = 7345258559
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, BaseFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
# BOT_TOKEN = "7691876985:AAF00PYw5m2W-tqcr_NnxcT5_KVwJ7SxoUA"

# ------------ ADMIN ID ------------
ADMINS = {7345258559, 474777651, 6515097273}

# ------------ СПИСОК ТЬЮТОРОВ ------------
TUTORS = {
    "Сафаров Шерзод Тожиевич": 627589541,
    "Аминова Самира Максудовна": 1879601730,
    "Акбаров Уткир Худойберганович": 6502274697,
    "Сайдалимова Инобат Абдуллаевна": 6827503862,
    "Ортиков Содик Хидирович": 1607442177,
    "admin": 920022557
}

selected_tutor = {}     # Родитель → выбранный тьютор
last_parent = {}        # Тьютор → последний родитель

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

os.makedirs("chat_logs", exist_ok=True)


# =============== ФИЛЬТР: ТЬЮТОР ==================
class IsTutor(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in TUTORS.values()


# =============== ЛОГИ АДМИНУ ==================
async def log_to_admin(text: str, msg: types.Message = None):
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, text)

            if msg:
                if msg.photo:
                    await bot.send_photo(admin_id, msg.photo[-1].file_id)
                elif msg.video:
                    await bot.send_video(admin_id, msg.video.file_id)
                elif msg.voice:
                    await bot.send_voice(admin_id, msg.voice.file_id)
                elif msg.video_note:
                    await bot.send_video_note(admin_id, msg.video_note.file_id)
                elif msg.document:
                    await bot.send_document(admin_id, msg.document.file_id)

        except:
            pass


# =============== СОХРАНЕНИЕ ЛОГА ====================
def save_log(user_id, role, text, username=None):
    """Username ham saqlanadi"""
    with open(f"chat_logs/{user_id}.txt", "a", encoding="utf-8") as file:
        if username:
            file.write(f"[{role}] ({username}) {text}\n")
        else:
            file.write(f"[{role}] {text}\n")


# =============== /start ==============================
@dp.message(Command("start"))
async def start(msg: types.Message):
    user_id = msg.from_user.id

    # Admin
    if user_id in ADMINS:
        kb = InlineKeyboardBuilder()
        kb.button(text="📁 Просмотреть все чаты", callback_data="logs")
        kb.adjust(1)
        return await msg.answer("👨‍💼 Админ-панель", reply_markup=kb.as_markup())

    # Тьютор
    if user_id in TUTORS.values():
        return await msg.answer("👋 Здравствуйте, тьютор! Сообщения будут приходить напрямую от родителей.")

    # Родителю показать список тьюторов
    kb = InlineKeyboardBuilder()
    for name in TUTORS:
        kb.button(text=name, callback_data=name)
    kb.adjust(1)

    await msg.answer("Здравствуйте!\nПожалуйста, выберите вашего тьютора:", reply_markup=kb.as_markup())


# =============== АДМИН КНОПКА ЛОГОВ ====================
@dp.callback_query(F.data == "logs")
async def admin_logs(call: types.CallbackQuery):
    files = os.listdir("chat_logs")

    if not files:
        return await call.message.answer("📁 Пока что нет сохранённых чатов.")

    for file in files:
        user_id = int(file.replace(".txt", ""))

        # Get username from Telegram
        try:
            user = await bot.get_chat(user_id)
            username = user.username or f"{user.first_name} {user.last_name or ''}"
        except:
            username = "Неизвестно"

        with open(f"chat_logs/{file}", "r", encoding="utf-8") as f:
            content = f.read()

        await call.message.answer(
            f"📄 Чат с пользователем:\n"
            f"ID: {user_id}\n"
            f"Имя: @{username if user.username else username}\n\n"
            f"{content}"
        )


# =============== РОДИТЕЛЬ ВЫБИРАЕТ ТЬЮТОРА ==============
@dp.callback_query()
async def choose_tutor(call: types.CallbackQuery):
    user_id = call.from_user.id

    if user_id in ADMINS or user_id in TUTORS.values():
        return await call.answer()

    tutor_name = call.data
    tutor_id = TUTORS[tutor_name]

    selected_tutor[user_id] = tutor_id

    await call.message.answer(f"Вы выбрали тьютора: {tutor_name}.\nМожете отправить сообщение.")
    await call.answer()

    await log_to_admin(f"👤 Родитель {user_id} выбрал тьютора {tutor_name}.")


# =============== ТЬЮТОР → РОДИТЕЛЬ ====================
@dp.message(IsTutor())
async def tutor_answer(msg: types.Message):
    tutor_id = msg.from_user.id

    if tutor_id not in last_parent:
        return await msg.answer("❗ Вам ещё не писали родители.")

    parent_id = last_parent[tutor_id]

    await forward_message(parent_id, msg)

    save_log(parent_id, "ТЬЮТОР", msg.text or "MEDIA")
    await log_to_admin(f"📨 ТЬЮТОР → РОДИТЕЛЬ ({parent_id})", msg)

    await msg.answer("✔ Сообщение отправлено.")


# =============== РОДИТЕЛЬ → ТЬЮТОР ====================
@dp.message()
async def parent_message(msg: types.Message):
    user_id = msg.from_user.id

    if user_id in TUTORS.values() or user_id in ADMINS:
        return

    if user_id not in selected_tutor:
        return await msg.answer("Пожалуйста, сначала выберите тьютора командой /start.")

    tutor_id = selected_tutor[user_id]
    last_parent[tutor_id] = user_id

    await forward_message(tutor_id, msg)

    username = msg.from_user.username or msg.from_user.full_name

    save_log(user_id, "РОДИТЕЛЬ", msg.text or "MEDIA", username)
    await log_to_admin(f"📩 РОДИТЕЛЬ → ТЬЮТОР ({user_id})", msg)

    await msg.answer("✔ Сообщение отправлено.")


# =============== ОТПРАВКА МЕДИА ====================
async def forward_message(to, msg):
    if msg.photo:
        await bot.send_photo(to, msg.photo[-1].file_id, caption=msg.caption or "")
    elif msg.video:
        await bot.send_video(to, msg.video.file_id, caption=msg.caption or "")
    elif msg.voice:
        await bot.send_voice(to, msg.voice.file_id)
    elif msg.video_note:
        await bot.send_video_note(to, msg.video_note.file_id)
    elif msg.document:
        await bot.send_document(to, msg.document.file_id)
    else:
        await bot.send_message(to, msg.text)


# =============== MAIN =====================================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("BOT ЗАПУЩЕН")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
