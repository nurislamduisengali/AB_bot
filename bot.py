import asyncio
import html  # 🔥 Импортируем для безопасного экранирования HTML
from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    InputMediaPhoto,
    InputMediaVideo
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BOT_TOKEN, ADMIN_ID






import os
import threading
from flask import Flask

# =======================
# Фоновый Flask-сервер для Render
# =======================
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()









# =======================
# Состояния
# =======================

class Submission(StatesGroup):
    waiting_for_content = State()
    waiting_for_solution = State()
    waiting_for_source = State()


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =======================
# Главное меню
# =======================

def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отправить задачу", callback_data="send_task")],
            [InlineKeyboardButton(text="Отправить новость или тему для обсуждения", callback_data="send_news")],
            [InlineKeyboardButton(text="Отправить математический мем", callback_data="send_meme")]
        ]
    )


# =======================
# Команда /start
# =======================

async def setup_commands():
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать работу")
    ])


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Здравствуйте! 👋\n\n"
        "Я бот предложки канала "
        "<a href='https://t.me/AB_problems'>«Задачи на любой вкус»</a> 📚✨\n\n"
        "Что вы хотите отправить?\n"
        "Выберите один из вариантов ниже 👇",
        reply_markup=main_menu(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


# =======================
# Выбор типа отправки
# =======================

@dp.callback_query(lambda c: c.data in ["send_task", "send_news", "send_meme"])
async def start_submission(callback: CallbackQuery, state: FSMContext):
    await callback.answer()  # 🔥 Убирает бесконечные "часики" на кнопке
    await state.clear()

    await state.update_data(
        photos=[],
        videos=[],
        text="",
        solution_text="",
        source_text="",
        type=callback.data,
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name
    )

    await state.set_state(Submission.waiting_for_content)

    if callback.data == "send_task":
        text = (
            "Отправьте задачу (можно приложить ссылку или фото).\n\n"
            "Когда закончите — нажмите или напишите в чат «Готово» ✅"
        )
    elif callback.data == "send_news":
        text = (
            "📢 Отправьте новость или тему для обсуждения (можно приложить ссылку, фото и видео).\n\n"
            "Когда закончите — нажмите или напишите в чат «Готово» ✅"
        )
    else:
        text = (
            "😂 Отправьте математический мем (можно приложить фото или видео).\n\n"
            "Когда закончите — нажмите или напишите в чат «Готово» ✅"
        )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Готово", callback_data="content_done")]
        ]
    )

    await callback.message.answer(text, reply_markup=kb)


# =======================
# Вспомогательные функции завершения шагов
# =======================

async def process_content_done(message_obj, state: FSMContext):
    data = await state.get_data()

    # 🛡 Безопасная проверка наличия типа сессии
    submission_type = data.get("type")
    if not submission_type:
        await message_obj.answer("⚠️ Сессия устарела. Нажмите /start, чтобы начать заново.", reply_markup=main_menu())
        await state.clear()
        return

    if submission_type == "send_task":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Готово", callback_data="solution_done")]
            ]
        )

        await message_obj.answer(
            "🔗 Отправьте ссылку на её решение.\n\n"
            "Когда закончите — нажмите или напишите в чат «Готово» ✅",
            reply_markup=kb
        )

        await state.set_state(Submission.waiting_for_solution)
    else:
        await finish_submission(message_obj, state)


async def process_solution_done(message_obj, state: FSMContext):
    data = await state.get_data()
    if not data.get("type"):
        await message_obj.answer("⚠️ Сессия устарела. Нажмите /start, чтобы начать заново.", reply_markup=main_menu())
        await state.clear()
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Готово", callback_data="source_done")]
        ]
    )

    await message_obj.answer(
        "📚 Укажите источник и автора.\n\n"
        "Когда закончите — нажмите или напишите в чат «Готово» ✅",
        reply_markup=kb
    )

    await state.set_state(Submission.waiting_for_source)


async def finish_submission(message_obj, state: FSMContext):
    data = await state.get_data()

    submission_type = data.get("type")
    if not submission_type:
        await message_obj.answer("⚠️ Сессия устарела. Нажмите /start, чтобы начать заново.", reply_markup=main_menu())
        await state.clear()
        return

    photos = data.get("photos", [])
    videos = data.get("videos", [])

    text = data.get("text", "").strip()
    solution_text = data.get("solution_text", "").strip()
    source_text = data.get("source_text", "").strip()

    username = data.get("username")
    full_name = html.quote(data.get("full_name", ""))

    sender = f"@{username}" if username else full_name

    if submission_type == "send_task":
        header = "📥 <b>Задача</b>"
    elif submission_type == "send_news":
        header = "📢 <b>Новость</b>"
    else:
        header = "😂 <b>Мем</b>"

    caption = f"{header}\n"
    caption += f"👤 Отправил: {sender}\n"

    if submission_type == "send_task":
        if text:
            caption += f"\n📝 Текст задачи:\n{text}"
        if solution_text:
            caption += f"\n\n🔗 Решение:\n{solution_text}"
        if source_text:
            caption += f"\n\n📚 Источник и автор:\n{source_text}"
    else:
        if text:
            caption += f"\n{text}"

    media_group = []
    for photo in photos:
        media_group.append(InputMediaPhoto(media=photo))
    for video in videos:
        media_group.append(InputMediaVideo(media=video))

    try:
        if not media_group:
            await bot.send_message(ADMIN_ID, caption, parse_mode="HTML")
        else:
            media_group[0].caption = caption
            media_group[0].parse_mode = "HTML"
            await bot.send_media_group(ADMIN_ID, media=media_group)

        await message_obj.answer(
            "✅ Ваше сообщение отправлено, спасибо!",
            reply_markup=main_menu()
        )
    except Exception as e:
        print(f"Ошибка при отправке админу: {e}")
        await message_obj.answer(
            "⚠️ Произошла ошибка при отправке сообщения. Попробуйте ещё раз через /start",
            reply_markup=main_menu()
        )
    finally:
        await state.clear()


# =======================
# ЭТАП 1 — Контент
# =======================

@dp.message(Submission.waiting_for_content)
async def collect_content(message: Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "готово":
        await process_content_done(message, state)
        return

    data = await state.get_data()

    photos = data.get("photos", [])
    videos = data.get("videos", [])
    text = data.get("text", "")

    incoming_text = ""
    if message.caption:
        incoming_text = html.quote(message.caption)
    elif message.text:
        incoming_text = html.quote(message.text)

    if message.photo:
        photos.append(message.photo[-1].file_id)
        if incoming_text:
            text += ("\n" if text else "") + incoming_text
    elif message.video:
        videos.append(message.video.file_id)
        if incoming_text:
            text += ("\n" if text else "") + incoming_text
    elif message.text:
        if incoming_text:
            text += ("\n" if text else "") + incoming_text

    await state.update_data(photos=photos, videos=videos, text=text)


@dp.callback_query(lambda c: c.data == "content_done")
async def content_done_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await process_content_done(callback.message, state)


# =======================
# ЭТАП 2 — Решение
# =======================

@dp.message(Submission.waiting_for_solution)
async def collect_solution(message: Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "готово":
        await process_solution_done(message, state)
        return

    data = await state.get_data()
    solution_text = data.get("solution_text", "")

    if message.text:
        clean_text = html.quote(message.text)
        solution_text += ("\n" if solution_text else "") + clean_text

    await state.update_data(solution_text=solution_text)


@dp.callback_query(lambda c: c.data == "solution_done")
async def solution_done_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await process_solution_done(callback.message, state)


# =======================
# ЭТАП 3 — Источник
# =======================

@dp.message(Submission.waiting_for_source)
async def collect_source(message: Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "готово":
        await finish_submission(message, state)
        return

    data = await state.get_data()
    source_text = data.get("source_text", "")

    if message.text:
        clean_text = html.quote(message.text)
        source_text += ("\n" if source_text else "") + clean_text

    await state.update_data(source_text=source_text)


@dp.callback_query(lambda c: c.data == "source_done")
async def source_done_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await finish_submission(callback.message, state)


# =======================
# Запуск бота
# =======================

async def main():
    await setup_commands()
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        keep_alive()
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Бот успешно остановлен!")