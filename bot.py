import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import BaseFilter
from aiogram import types

BOT_TOKEN = "7691876985:AAF00PYw5m2W-tqcr_NnxcT5_KVwJ7SxoUA"

# Tyutorlar ro'yxati (nom : telegram user id)
TUTORS = {
    "Gulhayo A": 5361061503,
    "Doniyor B": 6642417048,
    "Elbobo C": 920022557
}

# Ota-ona → tanlangan tyutor
selected_tutor = {}

# Tyutor → ota-ona (oxirgi xabar yuborgan ota-ona)
last_parent_message = {}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# --------------------- FILTER: Tutorni aniqlash ---------------------
class IsTutor(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in TUTORS.values()


# --------------------------- /start --------------------------------
@dp.message(Command("start"))
async def start_handler(msg: types.Message):
    # Agar tyutor bo‘lsa → menyu chiqarmaymiz
    if msg.from_user.id in TUTORS.values():
        await msg.answer("Здравствуйте, тьютор! У вас нет меню.")
        return

    # Ota-ona bo‘lsa → tyutorlar ro‘yxati
    kb = InlineKeyboardBuilder()
    for name in TUTORS:
        kb.button(text=name, callback_data=name)
    kb.adjust(1)

    await msg.answer(
        "Здравствуйте!\nПожалуйста, выберите вашего тьютора:",
        reply_markup=kb.as_markup()
    )


# ------------------ Ota-ona tyutor tanlash ------------------
@dp.callback_query()
async def choose_tutor(call: types.CallbackQuery):
    user_id = call.from_user.id

    # Tyutor callbackni bosib yubormasin
    if user_id in TUTORS.values():
        return

    tutor_name = call.data
    tutor_id = TUTORS[tutor_name]

    selected_tutor[user_id] = tutor_id

    await call.message.answer(
        f"Вы выбрали тьютора: {tutor_name}.\nТеперь можете отправить сообщение."
    )
    await call.answer()


# ------------------ Tyutor → Ota-ona javobi ------------------
@dp.message(IsTutor())
async def tutor_reply(msg: types.Message):
    tutor_id = msg.from_user.id

    if tutor_id in last_parent_message:
        parent_id = last_parent_message[tutor_id]

        await bot.send_message(
            chat_id=parent_id,
            text=f"📨 Ответ от тьютора:\n\n{msg.text}"
        )

        await msg.answer("✔ Ответ был отправлен родителю!")
    else:
        await msg.answer("Пока нет сообщений от родителей.")


# ------------------ Ota-ona → Tyutor xabari ------------------
@dp.message()
async def parent_to_tutor(msg: types.Message):
    user_id = msg.from_user.id

    # Agar tyutor bo‘lsa → bu handler ishlamasin
    if user_id in TUTORS.values():
        return

    if user_id not in selected_tutor:
        await msg.answer("Пожалуйста, сначала выберите тьютора через /start.")
        return

    tutor_id = selected_tutor[user_id]

    # Tyutor kimga javob berishi kerakligini saqlaymiz
    last_parent_message[tutor_id] = user_id

    await bot.send_message(
        chat_id=tutor_id,
        text=f"📩 Сообщение от родителя:\n{msg.text}"
    )

    await msg.answer("✔ Сообщение отправлено!")


# ----------------------------- MAIN -----------------------------
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
