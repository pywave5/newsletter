from datetime import datetime, time

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InputFile
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from filters.admin_filter import IsAdmin
from states.admin import AdminStates
from keyboards.admin import InlineKeyboardsControl, ReplyKeyboardsControl

from database.requests import get_all_users, add_task, remove_task, get_task

from config import ADMINS_IDS

admin = Router()
inline_keyboards = InlineKeyboardsControl()
reply_keyboards = ReplyKeyboardsControl()
scheduler = AsyncIOScheduler()

async def scheduled_send(message: Message,
                         news_text: str,
                         chats: list,
                         task_id: int,
                         button_text: str | None = None,
                         button_url: str | None = None,
                         ) -> None:

    reply_markup = None
    if button_text and button_url:
        reply_markup = await inline_keyboards.create_keyboards([
            {"text": button_text, "url": button_url}
        ])

    for chat_id in chats:
        try:
            await message.bot.send_message(
                chat_id=chat_id,
                text=news_text,
                reply_markup=reply_markup
            )
        except TelegramBadRequest:
            await message.answer("Произошла ошибка при рассылке.")

    await remove_task(task_id)


async def scheduled_send_media(message: Message,
                               file_data: str,
                               news_text: str,
                               chats: list,
                               task_id: int,
                               button_text: str | None = None,
                               button_url: str | None = None,
                               ) -> None:
    reply_markup = None
    if button_text and button_url:
        reply_markup = await inline_keyboards.create_keyboards([{"text": button_text, "url": button_url}])

    for chat_id in chats:
        try:
            if file_data:
                if file_data.endswith(('.jpg', '.png')):
                    await message.bot.send_photo(
                        chat_id=chat_id,
                        photo=file_data,
                        caption=news_text,
                        reply_markup=reply_markup
                    )
                elif file_data.endswith(('.mp3', '.wav')):
                    await message.bot.send_audio(
                        chat_id=chat_id,
                        audio=file_data,
                        caption=news_text,
                        reply_markup=reply_markup
                    )
                elif file_data.endswith('.mp4'):
                    await message.bot.send_video(
                        chat_id=chat_id,
                        video=file_data,
                        caption=news_text,
                        reply_markup=reply_markup
                    )
                elif file_data.endswith('.pdf'):
                    await message.bot.send_document(
                        chat_id=chat_id,
                        document=file_data,
                        caption=news_text,
                        reply_markup=reply_markup
                    )
            else:
                await message.answer(f"Не удалось найти файл для отправки в чат {chat_id}")
        except TelegramBadRequest as e:
            await message.answer(f"Произошла ошибка при рассылке в чат {chat_id}: {e}")
    await remove_task(task_id)

@admin.message(IsAdmin(), Command("apanel"))
async def open_panel(message: Message, state: FSMContext) -> None:
    buttons = [
        {"text": "🧑‍✈️ Список админов", "callback": "admins_list", "url": None},
        {"text": "🔔 Сделать объявление", "callback": "sendall", "url": None},
        {"text": "📊 Статистика", "callback": "static", "url": None},
        {"text": "💳 Цены на курсы", "callback": "course_price", "url": None},
        {"text": "❌ Закрыть меню", "callback": "close_menu", "url": None}
    ]

    await message.answer(f"<b>Добро пожаловать в Админ-панель🗂</b>\n\n"
                        f"Выбери один из пунктов для управления ботом👇",
                        reply_markup=await inline_keyboards.create_keyboards(buttons))

    await state.set_state(AdminStates.choice_item)

@admin.callback_query(F.data == "back_to_menu")
async def back_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.choice_item)
    await open_panel(callback.message, state)
    await callback.message.delete()
    await callback.answer()

@admin.callback_query(F.data == "close_menu")
async def cmd_close_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.delete()

@admin.callback_query(F.data == "static")
async def all_users(callback: CallbackQuery) -> None:
    await callback.message.delete()
    users = await get_all_users()
    clients = await get_all_users(only_clients=True)

    await callback.message.answer(f"📊 <b>Статистика по пользователям бота:</b>\n\n"
                                  f"👤 <b>Всего пользователей: {len(users)}</b>\n"
                                  f"🥇 <b>Количество клиентов: {len(clients)}</b>",
                                  reply_markup=await inline_keyboards.create_keyboard(text="⬅️ Назад", callback="back_to_menu", url=None))

@admin.callback_query(F.data == "admins_list")
async def admins_list(callback: CallbackQuery, bot) -> None:
    await callback.message.delete()
    admins_info = []
    for index, admin_id in enumerate(ADMINS_IDS, start=1):
        admin = await bot.get_chat(admin_id)
        admin_name = admin.first_name
        if admin.username:
            link = f"<a href='https://t.me/{admin.username}'>{admin_name}</a>"
        else:
            link = f"<a href='https://t.me/{admin_id}'>{admin_name}</a>"
        admins_info.append(f"{index}. {link}")

    admins_list_message = "\n".join(admins_info)
    await callback.message.answer(
        f"<b>Список админов:</b>\n\n{admins_list_message}",
        disable_web_page_preview=True,
        reply_markup=await inline_keyboards.create_keyboard(text="⬅️ Назад", callback="back_to_menu", url=None)
    )
    await callback.answer()

@admin.callback_query(F.data == "back_to_types_news")
async def back_to_news(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.choice_type_news)
    await cmd_send(callback, state)
    await callback.answer()

@admin.callback_query(F.data == "sendall")
async def choice_time(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    buttons = [
        {"text": "Сейчас", "callback": "now", "url": None},
        {"text": "В другое время", "callback": "any_time", "url": None},
        {"text": "⬅️ Назад", "callback": "back_to_menu", "url": None}
    ]
    await callback.message.answer(
        "Выберите время публикации",
        reply_markup=await inline_keyboards.create_keyboards(buttons, row_width=2)
    )
    await state.set_state(AdminStates.choice_time_news)

@admin.callback_query(F.data == "any_time")
async def select_time(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    await callback.message.answer(
        "Укажите дату публикации в формате <b>D.M.Y</b>\n"
        "Пример: <code>15.12.2024</code>",
        reply_markup=await inline_keyboards.create_keyboard("⬅️ Назад", "sendall", None)
    )
    await state.update_data(choice_time_selected=True)
    await state.set_state(AdminStates.choice_data)

@admin.message(AdminStates.choice_data)
async def select_time(message: Message, state: FSMContext) -> None:
    user_input = message.text.strip()
    try:
        selected_date = datetime.strptime(user_input, "%d.%m.%Y").date()
        now = datetime.now().date()

        if selected_date < now:
            await message.answer("Дата не может быть в прошлом. Укажите корректную дату.")
            return

    except ValueError:
        await message.answer("Неверный формат даты! Пожалуйста, введите в формате <b>D.M.Y</b> (например, 15.12.2024).")
        return

    await state.update_data(publication_date=selected_date)

    await message.answer("Укажите время публикации, в формате: <b>HH:MM</b>\n"
                         "Пример: <code>12:30</code>",
                         reply_markup=await inline_keyboards.create_keyboard("⬅️ Назад", "sendall", None))

    await state.set_state(AdminStates.choice_time)

@admin.message(AdminStates.choice_time)
async def select_time(message: Message, state: FSMContext) -> None:
    user_input = message.text.strip()

    try:
        selected_time = datetime.strptime(user_input, "%H:%M").time()
    except ValueError:
        await message.answer(
            "Неверный формат времени! Пожалуйста, введите в формате <b>HH:MM</b> (например, 14:30)."
        )
        return

    data = await state.get_data()
    publication_date = data.get("publication_date")
    if not publication_date:
        await message.answer("Что-то пошло не так, начните заново.")
        await state.clear()
        return

    publication_datetime = datetime.combine(publication_date, selected_time)

    if publication_datetime < datetime.now():
        await message.answer(
            "Указанное время уже прошло. Укажите корректные данные."
        )
        return

    await state.update_data(publication_time=selected_time)

    await message.answer(
        f"✅ Публикация запланирована на <b>{publication_datetime.strftime('%d.%m.%Y %H:%M')}</b>.\n"
        "Подтвердите или измените время.",
        reply_markup=await inline_keyboards.create_keyboard(text="✅ Подтвердить",
                                                            callback="selected_time",
                                              url=None)
    )
    await state.set_state(AdminStates.choice_time_selected)

@admin.callback_query(F.data == "selected_time", AdminStates.choice_time_selected)
async def selected_time(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.choice_type_news)
    await cmd_send(callback, state)

@admin.callback_query(F.data == "now", AdminStates.choice_time_news)
async def cmd_send(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    buttons = [
        {"text": "📝 Текстовое", "callback": "news_text", "url": None},
        {"text": "🖼 Медийное", "callback": "news_media", "url": None},
        {"text": "⬅️ Назад", "callback": "back_to_menu", "url": None}
    ]
    await callback.message.answer("Выберите тип объявления👇",
                                  reply_markup=await inline_keyboards.create_keyboards(buttons=buttons))
    await state.set_state(AdminStates.choice_type_news)
    await callback.answer()

@admin.callback_query(IsAdmin(), F.data == "news_text")
async def news_text(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    buttons = [
        {"text": "⬅️ Назад", "callback": "back_to_types_news", "url": None}
    ]
    await state.set_state(AdminStates.news_text)
    await callback.message.answer(f"Введите текст для отправки объявления\n"
                                  f"Не больше <b>4096</b> сиволов.",
                                  reply_markup=await inline_keyboards.create_keyboards(buttons))
    await callback.answer()

@admin.message(IsAdmin(), AdminStates.news_text)
async def news_text(message: Message, state: FSMContext) -> None:
    await state.update_data(news_message=message.text)
    data = await state.get_data()
    buttons = [
        {"text": "📌 Добавить кнопку со ссылкой", "callback": "add_link_btn", "url": None},
        {"text": "✅ Перейти к публикации", "callback": "go_to_publish", "url": None},
        {"text": "❌ Отменить публикацию", "callback": "back_to_menu", "url": None},
    ]
    await message.answer(f"<b>Текстовое объявление:</b>\n\n"
                         f"{data['news_message']}",
                         reply_markup=await inline_keyboards.create_keyboards(buttons, row_width=1))

@admin.callback_query(F.data == "add_link_btn")
async def add_btn(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(f"Введите название кнопки\n"
                                  f"Например: <blockquote>Подробнее</blockquote>")
    await state.set_state(AdminStates.button_link)
    await callback.answer()

@admin.message(IsAdmin(), AdminStates.button_link)
async def step_to_link(message: Message, state: FSMContext) -> None:
    await state.update_data(btn_name=message.text)
    await message.answer(f"Отлично, теперь укажите ссылку, куда будет вести эта кнопка!\n"
                         f"Например: <blockquote>https://youtube.com</blockquote>",
                         disable_web_page_preview=True)

    await state.set_state(AdminStates.step_to_link)

@admin.message(IsAdmin(), AdminStates.step_to_link)
async def create_link(message: Message, state: FSMContext) -> None:
    if not message.text.startswith("http://") and not message.text.startswith("https://"):
        await message.answer("❌ Некорректный URL. Убедитесь, что он начинается с http:// или https://.")
        return

    await state.update_data(btn_link=message.text)
    data = await state.get_data()

    inline_buttons = [
        {"text": data['btn_name'], "callback": None, "url": data['btn_link']}
    ]

    reply_buttons = ["✅ Опубликовать", "❌ Отменить"]

    await message.answer(
        "✅ <b>Готово!</b>\n"
        "Ваша публикация готова к рассылке",
        reply_markup=await reply_keyboards.create_keyboards(row=1, texts=reply_buttons)
    )

    await message.answer(
        f"{data['news_message']}",
        reply_markup=await inline_keyboards.create_keyboards(inline_buttons)
    )

    await state.update_data(markup=inline_buttons)

    await state.set_state(AdminStates.go_to_publish)

@admin.callback_query(F.data == "go_to_publish")
async def cmd_publish(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    data = await state.get_data()

    reply_buttons = ["✅ Опубликовать", "❌ Отменить"]

    await callback.message.answer("<b>Текстовое объявление</b>",
                                  reply_markup=await reply_keyboards.create_keyboards(row=1, texts=reply_buttons))
    await callback.message.answer(data['news_message'])

    await state.set_state(AdminStates.go_to_publish)
    await callback.answer()

@admin.message(IsAdmin(), F.text == "❌ Отменить", AdminStates.go_to_publish)
async def cancel_news(message: Message, state: FSMContext) -> None:
    await message.answer("Ваша публикация отменена!",
                         reply_markup=ReplyKeyboardRemove())
    await state.clear()


@admin.message(IsAdmin(), F.text == "✅ Опубликовать", AdminStates.go_to_publish)
async def publish_news(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    all_chats = await get_all_users()

    if data.get("choice_time_selected"):
        publication_date = data.get("publication_date")
        publication_time = data.get("publication_time")

        run_at = datetime.strptime(f"{publication_date} {publication_time}", "%Y-%m-%d %H:%M:%S")
        run_at_str = run_at.isoformat()

        await add_task(
            run_at=run_at_str,
            news_text=data.get("news_message"),
            button_text=data.get("btn_name"),
            button_url=data.get("btn_link")
        )

        task = await get_task(run_at=run_at_str)

        scheduler.add_job(
            scheduled_send,
            'date',
            run_date=task['run_at'],
            kwargs={
                "message": message,
                "news_text": task['news_text'],
                "task_id": task['id'],
                "chats": all_chats,
                "button_text": task['button_text'],
                "button_url": task['button_url']
            }
        )

        await message.answer(f"Ваша публикация")
        await message.answer(f"<b>{data['news_message']}</b>",
                             reply_markup=await inline_keyboards.create_keyboards(
                                 data.get("markup", [])) if "markup" in data else None)
        await message.answer(f"будет отправлена в <b>{publication_date} {publication_time}</b>",
                             reply_markup=ReplyKeyboardRemove())

        return

    for chat_id in all_chats:
        try:
            await message.bot.send_message(
                chat_id=chat_id,
                text=data["news_message"],
                reply_markup=await inline_keyboards.create_keyboards(
                    data.get("markup", [])) if "markup" in data else None
            )
        except TelegramBadRequest:
            await message.answer("Ошибка при публикации рассылки, возможно, бот не является Администратором чата.")

    await message.answer("✅ Объявление успешно опубликовано!", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@admin.callback_query(F.data == "news_media")
async def news_media(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    buttons = [
        {"text": "⬅️ Назад", "callback": "back_to_types_news", "url": None}
    ]
    await state.set_state(AdminStates.news_media)
    await callback.message.answer(
        "<b>Вы можете отправить одно из:</b>\n\n"
        "📷 Фотографию\n"
        "📹 Видео\n"
        "🎧 Аудио\n"
        "📄 Документ",
        reply_markup=await inline_keyboards.create_keyboards(buttons)
    )
    await callback.answer()

@admin.message(IsAdmin(), ~F.text & (F.photo | F.video | F.audio | F.document), AdminStates.news_media)
async def handle_media(message: Message, state: FSMContext) -> None:
    if message.photo:
        media_type = "photo"
        media_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        media_id = message.video.file_id
    elif message.audio:
        media_type = "audio"
        media_id = message.audio.file_id
    elif message.document:
        media_type = "document"
        media_id = message.document.file_id
    else:
        await message.answer("❌ Не удалось определить тип медиа. Попробуйте снова.")
        return

    await state.update_data(media_id=media_id, media_type=media_type)
    await message.answer(
        "Введите описание для медиа-контента:\n"
        "Не больше <b>1096</b> символов.",
    )
    await state.set_state(AdminStates.media_handle_state)

@admin.message(IsAdmin(), F.text, AdminStates.media_handle_state)
async def handle_media_caption(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    caption = message.text

    buttons = [
        {"text": "📌 Добавить кнопку со ссылкой", "callback": "add_link_btn_media", "url": None},
        {"text": "✅ Опубликовать", "callback": "go_to_publish_media", "url": None},
        {"text": "❌ Отменить публикацию", "callback": "back_to_menu", "url": None},
    ]

    if len(caption) > 1096:
        await message.answer("❌ Описание слишком длинное. Попробуйте снова.")
        return

    media_type = data["media_type"]
    media_id = data["media_id"]

    if media_type == "photo":
        await message.answer_photo(media_id, caption=caption,                                  reply_markup=await inline_keyboards.create_keyboards(buttons, row_width=1))
    elif media_type == "video":
        await message.answer_video(media_id, caption=caption,                                reply_markup=await inline_keyboards.create_keyboards(buttons, row_width=1))
    elif media_type == "audio":
        await message.answer_audio(media_id, caption=caption,                               reply_markup=await inline_keyboards.create_keyboards(buttons, row_width=1))
    elif media_type == "document":
        await message.answer_document(media_id, caption=caption,
                                      reply_markup=await inline_keyboards.create_keyboards(buttons, row_width=1))
    await state.update_data(caption=caption)

@admin.callback_query(F.data == "add_link_btn_media", AdminStates.media_handle_state)
async def add_link_btn_media(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    await state.set_state(AdminStates.adding_link_button)
    await callback.message.answer("Введите текст кнопки:")

@admin.message(IsAdmin(), AdminStates.adding_link_button)
async def handle_button_text(message: Message, state: FSMContext) -> None:
    await state.update_data(button_text=message.text)
    await message.answer("Теперь введите URL для кнопки:")

    await state.set_state(AdminStates.adding_link_url)

@admin.message(IsAdmin(), AdminStates.adding_link_url)
async def handle_button_url(message: Message, state: FSMContext) -> None:
    url = message.text

    reply_buttons = ["✅ Опубликовать", "❌ Отменить"]

    if not url.startswith("http://") and not url.startswith("https://"):
        await message.answer("❌ Некорректный URL. Убедитесь, что он начинается с http:// или https://.")
        return

    data = await state.get_data()
    button_text = data.get("button_text")

    new_button = {"text": button_text, "url": url}
    buttons = data.get("buttons", [])
    buttons.append(new_button)

    await state.update_data(buttons=buttons)

    media_type = data["media_type"]
    media_id = data["media_id"]
    caption = data.get("caption", "")

    reply_markup = await inline_keyboards.create_keyboards(buttons=buttons, row_width=1)

    if media_type == "photo":
        await message.answer_photo(media_id, caption=caption, reply_markup=reply_markup)
    elif media_type == "video":
        await message.answer_video(media_id, caption=caption, reply_markup=reply_markup)
    elif media_type == "audio":
        await message.answer_audio(media_id, caption=caption, reply_markup=reply_markup)
    elif media_type == "document":
        await message.answer_document(media_id, caption=caption, reply_markup=reply_markup)

    await message.answer("✅ Кнопка успешно добавлена! Вы можете перейти к публикации.",
                         reply_markup=await reply_keyboards.create_keyboards(row=1, texts=reply_buttons))
    await state.set_state(AdminStates.go_to_publish_media)

@admin.message(IsAdmin(), F.text == "❌ Отменить", AdminStates.go_to_publish_media)
async def cancel_media_publish(message: Message, state: FSMContext) -> None:
    await message.answer("Публикация отменена! Вы можете начать заново, если потребуется.",
                         reply_markup=ReplyKeyboardRemove())
    await state.clear()


@admin.message(IsAdmin(), F.text == "✅ Опубликовать", AdminStates.go_to_publish_media)
async def publish_media(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    media_type = data["media_type"]
    media_id = data["media_id"]
    caption = data.get("caption", "")
    buttons = data.get("buttons", [])

    reply_markup = await inline_keyboards.create_keyboards(buttons=buttons, row_width=1) if buttons else None
    chats = await get_all_users()

    if data.get("choice_time_selected"):
        publication_date = data.get("publication_date")
        publication_time = data.get("publication_time")

        run_at = datetime.strptime(f"{publication_date} {publication_time}", "%Y-%m-%d %H:%M:%S")
        run_at_str = run_at.isoformat()

        await add_task(
            run_at=f"{data.get('publication_date')} {data.get('publication_time')}",
            news_text=caption,
            button_text=buttons[0]["text"],
            button_url=buttons[0]["url"],
            file_data=media_id
        )

        task = await get_task(run_at=run_at_str)

        scheduler.add_job(
            scheduled_send_media,
            'date',
            run_date=task['run_at'],
            kwargs={
                "message": message,
                "file_data": task['media_id'],
                "news_text": task['news_text'],
                "task_id": task['id'],
                "chats": chats,
                "button_text": task['button_text'],
                "button_url": task['button_url']
            }
        )

        await message.answer("<b>Ваша публикация</b>")
        if media_type == "photo":
            await message.answer_photo(photo=media_id, caption=caption, reply_markup=reply_markup)
        elif media_type == "video":
            await message.answer_video(video=media_id, caption=caption, reply_markup=reply_markup)
        elif media_type == "audio":
            await message.answer_audio(audio=media_id, caption=caption, reply_markup=reply_markup)
        elif media_type == "document":
            await message.answer_document(document=media_id, caption=caption, reply_markup=reply_markup)
        await message.answer(f"будет отправлена в <b>{data['publication_date']} - {data['publication_time']}</b>")

        return

    for chat_id in chats:
        try:
            if media_type == "photo":
                await message.bot.send_photo(chat_id=chat_id, photo=media_id, caption=caption, reply_markup=reply_markup)
            elif media_type == "video":
                await message.bot.send_video(chat_id=chat_id, video=media_id, caption=caption, reply_markup=reply_markup)
            elif media_type == "audio":
                await message.bot.send_audio(chat_id=chat_id, audio=media_id, caption=caption, reply_markup=reply_markup)
            elif media_type == "document":
                await message.bot.send_document(chat_id=chat_id, document=media_id, caption=caption, reply_markup=reply_markup)
        except TelegramBadRequest:
            await message.answer("Произошла ошибка, возможно, бот не является Админстратором чата.")

    await message.answer("✅ Медиа успешно опубликовано!", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@admin.callback_query(F.data == "go_to_publish_media")
async def go_to_publish_media(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.go_to_publish_media)
    await publish_media(callback.message, state)
    await callback.answer()