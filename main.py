# import asyncio
# from aiogram import Bot, Dispatcher, types
# from aiogram.filters import Command
# from aiogram.utils.keyboard import InlineKeyboardBuilder
# from aiogram.filters import BaseFilter
# from aiogram import types

# BOT_TOKEN = "7691876985:AAF00PYw5m2W-tqcr_NnxcT5_KVwJ7SxoUA"

# # Tyutorlar ro'yxati (nom : telegram user id)
# TUTORS = {
#     "Gulhayo A": 5361061503, #gulhayo
#     "Doniyor B": 6642417048, #doniyor
#     "Elbobo C": 920022557 #ELbobo
# }

# # Ota-ona → tanlangan tyutor
# selected_tutor = {}

# # Tyutor → ota-ona (oxirgi xabar yuborgan ota-ona)
# last_parent_message = {}

# bot = Bot(token=BOT_TOKEN)
# dp = Dispatcher()

# class IsTutor(BaseFilter):
#     async def __call__(self, message: types.Message) -> bool:
#         return message.from_user.id in TUTORS.values()

# # ------------------------- /start -------------------------
# @dp.message(Command("start"))
# async def start_handler(msg: types.Message):
#     # Agar tyutor bo‘lsa → hech qanday menyu chiqarmaymiz
#     if msg.from_user.id in TUTORS.values():
#         await msg.answer("Salom, tyutor! Sizga hech qanday menyu chiqmaydi.")
#         return

#     # Ota-ona bo‘lsa → tyutorlar ro‘yxati chiqariladi
#     kb = InlineKeyboardBuilder()
#     for name in TUTORS:
#         kb.button(text=name, callback_data=name)
#     kb.adjust(1)

#     await msg.answer(
#         "Assalomu alaykum!\nIltimos, tyutoringizni tanlang:",
#         reply_markup=kb.as_markup()
#     )


# # ----------------------- Tyutor tanlash (ota-ona) -----------------------
# @dp.callback_query()
# async def choose_tutor(call: types.CallbackQuery):
#     user_id = call.from_user.id
#     if user_id in TUTORS.values():  # tyutorlar callbackga tushmasin
#         return

#     tutor_name = call.data
#     tutor_id = TUTORS[tutor_name]
#     selected_tutor[user_id] = tutor_id

#     await call.message.answer(f"Siz {tutor_name} tyutorini tanladingiz.\nEndi xabaringizni yozing.")
#     await call.answer()


# # ------------------ Tyutor → Ota-ona javobi ------------------
# @dp.message(IsTutor())
# async def tutor_reply(msg: types.Message):
#     tutor_id = msg.from_user.id

#     if tutor_id in last_parent_message:
#         parent_id = last_parent_message[tutor_id]

#         await bot.send_message(
#             chat_id=parent_id,
#             text=f"📨 Tyutordan javob:\n\n{msg.text}"
#         )

#         await msg.answer("✔ Javob ota-onaga yuborildi!")
#     else:
#         await msg.answer("Hozircha ota-onadan xabar yo‘q.")


# # ------------------ Ota-ona → Tyutor xabari ------------------
# @dp.message()
# async def parent_to_tutor(msg: types.Message):
#     user_id = msg.from_user.id

#     # Agar tyutor bo‘lsa → bu handler ishlamasin
#     if user_id in TUTORS.values():
#         return

#     if user_id not in selected_tutor:
#         await msg.answer("Iltimos, avval /start orqali tyutorni tanlang.")
#         return

#     tutor_id = selected_tutor[user_id]
#     last_parent_message[tutor_id] = user_id  # tyutor kimga javob berishi kerak

#     await bot.send_message(
#         chat_id=tutor_id,
#         text=f"📩 Ota-onadan xabar:\n{msg.text}"
#     )

#     await msg.answer("✔ Xabar yuborildi!")


# # --------------------------- MAIN ---------------------------
# async def main():
#     await bot.delete_webhook(drop_pending_updates=True)
#     print("Bot ishga tushdi...")
#     await dp.start_polling(bot)


# if __name__ == "__main__":
#     asyncio.run(main())

# pro_tutor_bot.py

import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, BaseFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "8287691451:AAHOOR3LvsEbr6IsPnSC7ygvtUT5Lze20Wc"



# ------------------- TUTORLAR -------------------
TUTORS = {
    "Сафаров Шерзод Тожиевич": 627589541,
    "Аминова Самира Максудовна": 1879601730,
    "Акбаров Уткир Худойберганович": 6502274697,
    "Сайдалимова Инобат Абдуллаевна": 6827503862,
    "Ортиков Содик Хидирович": 1607442177,
    "admin": 920022557
}

# ------------------- ADMIN ---------------------
ADMIN_IDS = {7345258559}   # admin id lar

# Ota-ona → tanlangan tyutor
selected_tutor = {}

# Tyutor → oxirgi yozgan ota-ona
last_parent_message = {}


# ============ FILTER =============
class IsTutor(BaseFilter):
    async def __call__(self, msg: types.Message) -> bool:
        return msg.from_user.id in TUTORS.values()


class IsAdmin(BaseFilter):
    async def __call__(self, msg: types.Message) -> bool:
        return msg.from_user.id in ADMIN_IDS


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ============ START =============
@dp.message(Command("start"))
async def start_handler(msg: types.Message):

    # Admin
    if msg.from_user.id in ADMIN_IDS:
        await msg.answer("Админ-панель готова. Команды будут добавлены позже.")
        return

    # Tyutor
    if msg.from_user.id in TUTORS.values():
        await msg.answer("Здравствуйте, тьютор! Вы можете отвечать родителям.")
        return

    # Ota-ona
    kb = InlineKeyboardBuilder()
    for name in TUTORS:
        kb.button(text=name, callback_data=name)
    kb.adjust(1)

    await msg.answer(
        "Здравствуйте!\nВыберите тьютора:",
        reply_markup=kb.as_markup()
    )


# ============ TYUTOR TANLASH ============
@dp.callback_query()
async def choose_tutor(call: types.CallbackQuery):

    user_id = call.from_user.id

    # Admin va tyutor tanlamasin
    if user_id in ADMIN_IDS or user_id in TUTORS.values():
        await call.answer()
        return

    tutor_name = call.data
    tutor_id = TUTORS[tutor_name]

    selected_tutor[user_id] = tutor_id

    await call.message.answer(
        f"Вы выбрали тьютора: {tutor_name}.\nТеперь отправьте сообщение."
    )
    await call.answer()


# ============ TYUTOR → OTA-ONA ============
@dp.message(IsTutor())
async def tutor_reply(msg: types.Message):

    tutor_id = msg.from_user.id

    if tutor_id not in last_parent_message:
        await msg.answer("Пока нет сообщений от родителей.")
        return

    parent_id = last_parent_message[tutor_id]

    # HEADER
    header = f"📨 Ответ от тьютора:\n\n"

    # -------- TEXT --------
    if msg.text:
        await bot.send_message(parent_id, header + msg.text)
        await msg.answer("✔ Ответ отправлен родителю!")
        return

    # -------- PHOTO --------
    if msg.photo:
        await bot.send_photo(
            parent_id,
            msg.photo[-1].file_id,
            caption=header + (msg.caption or "")
        )
        await msg.answer("✔ Фото отправлено!")
        return

    # -------- VIDEO --------
    if msg.video:
        await bot.send_video(
            parent_id,
            msg.video.file_id,
            caption=header + (msg.caption or "")
        )
        await msg.answer("✔ Видео отправлено!")
        return

    # -------- VOICE --------
    if msg.voice:
        await bot.send_voice(
            parent_id,
            msg.voice.file_id,
            caption=header
        )
        await msg.answer("✔ Голосовое отправлено!")
        return

    # -------- DOCUMENT --------
    if msg.document:
        await bot.send_document(
            parent_id,
            msg.document.file_id,
            caption=header
        )
        await msg.answer("✔ Документ отправлен!")
        return

    await msg.answer("Тип медиа не поддерживается.")


# ============ OTA-ONA → TYUTOR ============
@dp.message()
async def parent_to_tutor(msg: types.Message):

    user_id = msg.from_user.id

    # Admin → hech qayerga yubormaymiz
    if user_id in ADMIN_IDS:
        await msg.answer("Сообщение принято (админ).")
        return

    # Tyutor emas → ota-ona bo‘lishi kerak
    if user_id not in selected_tutor:
        await msg.answer("Пожалуйста, сначала выберите тьютора через /start.")
        return

    tutor_id = selected_tutor[user_id]
    last_parent_message[tutor_id] = user_id  # tyutor kimga javob beradi

    header = f"📩 Сообщение от родителя:\n👤 {msg.from_user.full_name} (id: {user_id})\n\n"

    # -------- TEXT --------
    if msg.text:
        await bot.send_message(tutor_id, header + msg.text)
        await msg.answer("✔ Сообщение отправлено!")
        return

    # -------- PHOTO --------
    if msg.photo:
        await bot.send_photo(
            tutor_id,
            msg.photo[-1].file_id,
            caption=header + (msg.caption or "")
        )
        await msg.answer("✔ Фото отправлено!")
        return

    # -------- VIDEO --------
    if msg.video:
        await bot.send_video(
            tutor_id,
            msg.video.file_id,
            caption=header + (msg.caption or "")
        )
        await msg.answer("✔ Видео отправлено!")
        return

    # -------- VOICE --------
    if msg.voice:
        await bot.send_voice(
            tutor_id,
            msg.voice.file_id,
            caption=header
        )
        await msg.answer("✔ Голосовое отправлено!")
        return

    # -------- DOCUMENT --------
    if msg.document:
        await bot.send_document(
            tutor_id,
            msg.document.file_id,
            caption=header
        )
        await msg.answer("✔ Документ отправлен!")
        return

    await msg.answer("Тип медиа не поддерживается.")


# ============ MAIN ============
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
