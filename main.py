from os import getenv
from dotenv import load_dotenv
import asyncio
import time

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    CallbackQuery,
    LinkPreviewOptions
)
from aiogram.filters import Command
from aiogram.enums import ParseMode

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from asyncio import sleep
from asyncio import create_task

# =========================
# НАСТРОЙКИ БОТА
# =========================

load_dotenv()

TOKEN = getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в .env")

REQUESTS_CHAT_ID = -1003954456139
LOG_CHAT_ID = -5302445006


dp = Dispatcher()
router = Router()
dp.include_router(router)


# =========================
# АНТИСПАМ
# =========================

cooldowns = {}

albums = {}
album_timers = {}

BUTTON_DELAY = 10
MESSAGE_DELAY = 5


def check_spam(user_id: int, delay: int):

    now = time.time()

    last = cooldowns.get(user_id, 0)

    if now - last < delay:
        return False

    cooldowns[user_id] = now
    return True



def get_user_info(user):

    username = (
        f"@{user.username}"
        if user.username
        else "нет username"
    )

    return (
        f"Username: {username}\n"
        f"ID: {user.id}"
    )



# =========================
# FSM СОСТОЯНИЯ
# =========================

class Form(StatesGroup):
    waiting_nick = State()
    waiting_admin_reply = State()
    waiting_questionnaire = State()
    waiting_skin = State()


# =========================
# КНОПКИ
# =========================

menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Вступление",
                icon_custom_emoji_id="6033108709213736873",
                callback_data="join",
                style="primary"
            )
        ],
        [
            InlineKeyboardButton(
                text="Анкетник",
                icon_custom_emoji_id="6039779802741739617",
                callback_data="questionnaire"
            )
        ]
    ]
)



def reply_keyboard(user_id: int):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Ответить",
                    callback_data=f"reply_{user_id}"
                )
            ]
        ]
    )



FORM_CONFIG = {

    "join": {
        "state": Form.waiting_nick,
        "message": "Пожалуйста, укажите свой ник в игре.",
        "log": "📝 Открыта опция «Вступление»"
    },

    "questionnaire": {
        "state": Form.waiting_questionnaire,
        "message": '<b>Пожалуйста, заполните анкету по шаблону:</b>\n\n'
        '1) Ник в игре, юзернейм в телеграме.\n'
        '2) Имя/Прозвище/Кличка.\n'
        '3) Раса.\n'
        '4) Возраст.\n'
        '5) Внешность. Текстовое описание необязательно, если прикреплены изображения.\n'
        '6) Характер, черты личности.\n'
        '7) Биография.\n'
        '8) Дополнительная информация, факты.\n\n'
        'Текст разрешается оформлять по-своему (в т.ч. с использованием премиум-эмодзи).\n'
        'Проследите за тем, чтобы ваша анкета умещалась в одно сообщение телеграма. В противном случае можно вставить ссылки на сторонние хранители информации.',
        "log": "📋 Открыта опция «Анкетник»"
    }
}



# =========================
# START
# =========================

@router.message(Command("start"))
async def start(
    message: Message,
    state: FSMContext
):
    await state.clear()
    await message.answer(
        '<b>Вас приветствует бот сервера <a href="https://t.me/MLADAB0SNA">Mlada Bosna</a>!</b> Ниже описан функционал всех опций.\n\n'
        '1) <b>Вступление:</b> регистрация новых игроков. Требований для вступления нет, нужно всего лишь указать свой ник в игре.\n'
        '2) <b>Анкетник:</b> регистрация лорного персонажа. Необязательно для игры на сервере. Подробнее на <a href="https://t.me/MLADAB0SNA_chars">канале</a>.',
        reply_markup=menu,
        parse_mode=ParseMode.HTML,
        link_preview_options=LinkPreviewOptions(
            is_disabled=True
    )
    )



@router.callback_query(F.data.in_(FORM_CONFIG.keys()))
async def open_form(
    call: CallbackQuery,
    state: FSMContext,
    bot: Bot
):

    user_id = call.from_user.id


    if not check_spam(user_id, BUTTON_DELAY):

        await call.answer(
            "Подождите.",
            show_alert=True
        )

        return


    if await state.get_state():

        await state.clear()


    data = FORM_CONFIG[call.data]


    await state.set_state(
        data["state"]
    )

    await call.message.answer(
        data["message"],
        parse_mode=ParseMode.HTML,
        link_preview_options=LinkPreviewOptions(
            is_disabled=True
        )
    )

    await bot.send_message(
        LOG_CHAT_ID,
        f"{data['log']}\n\n"
        f"{get_user_info(call.from_user)}"
    )


    await call.answer()

async def send_application(
    bot: Bot,
    message: Message,
    title: str
):

    await bot.send_message(
        REQUESTS_CHAT_ID,
        f"{title}\n\n"
        f"{get_user_info(message.from_user)}"
    )


    await bot.copy_message(
        chat_id=REQUESTS_CHAT_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        reply_markup=reply_keyboard(
            message.from_user.id
        )
    )


    await bot.send_message(
        LOG_CHAT_ID,
        f"✅ {title}\n"
        f"{get_user_info(message.from_user)}"
    )
# =========================
# ПОЛУЧЕНИЕ НИКА
# =========================

@router.message(Form.waiting_nick)
async def get_nick(
    message: Message,
    state: FSMContext,
    bot: Bot
):


    if not message.text:

        await message.answer(
            "Отправьте текстовый ник."
        )

        return


    if message.text and len(message.text) > 50:

        await message.answer(
            "Ник слишком длинный."
        )

        return


    await send_application(
        bot,
        message,
        "🟢 #Вступление"
    )


    await message.answer(
        "Заявка отправлена! Вы можете обратиться лично к "
        "<a href='https://t.me/MLADAB0SNA/6'>младшему администратору</a>, "
        "если ответ не поступил в течение 6-ти часов.",
        parse_mode=ParseMode.HTML,
        link_preview_options=LinkPreviewOptions(
            is_disabled=True
        )
    )


    await state.clear()


# =========================
# ПОЛУЧЕНИЕ АНКЕТЫ
# =========================

@router.message(Form.waiting_questionnaire)
async def get_questionnaire(
    message: Message,
    state: FSMContext,
    bot: Bot
):

    # Для альбома не проверяем каждую картинку
    if not message.media_group_id:

        if not check_spam(
            message.from_user.id,
            MESSAGE_DELAY
        ):
            await message.answer(
                "Слишком много сообщений. Подождите."
            )
            return


    if not message.text and not message.caption and not message.photo and not message.document:

        await message.answer(
            "К анкете возможно прикрепить только изображения и файлы."
        )

        return


    # Если это альбом с картинками
# Если это альбом с картинками
# Если это альбом с картинками
    if message.media_group_id:

        media_id = message.media_group_id

        if media_id not in albums:
            albums[media_id] = {
                "messages": [],
                "user": message.from_user,
                "chat_id": message.chat.id,
                "state": state
            }

        albums[media_id]["messages"].append(message.message_id)

        if media_id in album_timers:
            album_timers[media_id].cancel()


        async def process_album():

            await sleep(3)

            album = albums.pop(media_id, None)

            if not album:
                return


            await bot.send_message(
                REQUESTS_CHAT_ID,
                "📋 #Анкета\n\n"
                f"{get_user_info(album['user'])}",
                reply_markup=reply_keyboard(
                    album["user"].id
                )
            )


            for msg_id in album["messages"]:

                await bot.copy_message(
                    chat_id=REQUESTS_CHAT_ID,
                    from_chat_id=album["chat_id"],
                    message_id=msg_id
                )


            await bot.send_message(
                LOG_CHAT_ID,
                f"✅ 📋 #Анкета\n"
                f"{get_user_info(album['user'])}"
            )


            await bot.send_message(
                album["user"].id,
                "Спасибо! Теперь, пожалуйста, отправьте файл вашего скина."
            )


            await album["state"].set_state(
                Form.waiting_skin
            )

            album_timers.pop(media_id, None)


        album_timers[media_id] = create_task(
            process_album()
        )


        return


    # Обычная анкета (без альбома)

    await bot.send_message(
        REQUESTS_CHAT_ID,
        "📋 #Анкета\n\n"
        f"{get_user_info(message.from_user)}",
        reply_markup=reply_keyboard(message.from_user.id)
    )


    await bot.copy_message(
        chat_id=REQUESTS_CHAT_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )


    await bot.send_message(
        LOG_CHAT_ID,
        f"✅ 📋 #Анкета\n"
        f"{get_user_info(message.from_user)}"
    )


    await message.answer(
        "Спасибо! Теперь, пожалуйста, отправьте файл вашего скина."
    )


    await state.set_state(
        Form.waiting_skin
    )

# =========================
# ПОЛУЧЕНИЕ СКИНА
# =========================

@router.message(Form.waiting_skin)
async def get_skin(
    message: Message,
    state: FSMContext,
    bot: Bot
):


    if not message.document:

        await message.answer(
            "Пожалуйста, отправьте скин именно файлом (без сжатия изображения)."
        )

        return


    await bot.send_message(
        REQUESTS_CHAT_ID,
        "🎨 #Скин\n\n"
        f"{get_user_info(message.from_user)}",
        reply_markup=reply_keyboard(
            message.from_user.id
        )
    )


    await bot.copy_message(
        chat_id=REQUESTS_CHAT_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )


    await bot.send_message(
        LOG_CHAT_ID,
        f"✅ 🎨 #Скин\n"
        f"{get_user_info(message.from_user)}"
    )


    await message.answer(
        "Анкета отправлена."
    )


    await state.clear()

# =========================
# ОТВЕТ АДМИНИСТРАТОРА
# =========================

@router.callback_query(F.data.startswith("reply_"))
async def reply_user(
    call: CallbackQuery,
    state: FSMContext
):

    try:
        user_id = int(call.data.split("_")[1])

    except:
        await call.answer(
            "Ошибка пользователя",
            show_alert=True
        )
        return


    await state.update_data(
        reply_user_id=user_id
    )


    await state.set_state(
        Form.waiting_admin_reply
    )


    await call.message.answer(
        "Напишите сообщение для игрока:"
    )


    await call.answer()



@router.message(Form.waiting_admin_reply)
async def send_admin_reply(
    message: Message,
    state: FSMContext,
    bot: Bot
):

    data = await state.get_data()

    user_id = data.get("reply_user_id")

    if not user_id:
        await message.answer(
            "Ошибка: игрок не найден."
        )
        await state.clear()
        return


    await bot.copy_message(
        chat_id=user_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )


    await message.answer(
        "Сообщение отправлено игроку."
    )


    await bot.send_message(
        LOG_CHAT_ID,
        f"💬 Администратор отправил ответ\n"
        f"{get_user_info(message.from_user)}\n"
        f"Игрок ID: {user_id}"
    )


    await state.clear()

# =========================
# ОБРАБОТКА СООБЩЕНИЙ БЕЗ ОПЦИИ
# =========================

@router.message()
async def no_option_selected(
    message: Message,
    state: FSMContext
):

    if message.text and message.text.startswith("/"):
        return

    current_state = await state.get_state()

    if current_state:
        return

    await message.answer(
        "Для начала необходимо выбрать опцию из списка.",
        reply_markup=menu
    )

# =========================
# ЗАПУСК
# =========================

@dp.error()
async def error_handler(event):
    print(
        "Ошибка:",
        event.exception
    )

async def main():

    bot = Bot(token=TOKEN)


    await bot.set_my_commands(
        [
            BotCommand(
                command="start",
                description="Рестарт"
            )
        ]
    )


    print("Bot started...")


    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())