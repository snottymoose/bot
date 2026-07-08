from os import getenv
from dotenv import load_dotenv
import asyncio
import time

from aiogram import Bot, Dispatcher, Router
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    CallbackQuery
)
from aiogram.filters import Command
from aiogram.enums import ParseMode

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


# =========================
# НАСТРОЙКИ БОТА
# =========================

load_dotenv()

TOKEN = getenv("BOT_TOKEN")

REQUESTS_CHAT_ID = -5315904328
LOG_CHAT_ID = -5302445006


dp = Dispatcher()
router = Router()
dp.include_router(router)


# =========================
# АНТИСПАМ
# =========================

button_cooldowns = {}
message_cooldowns = {}

BUTTON_DELAY = 10
MESSAGE_DELAY = 5


def check_button_spam(user_id: int):

    now = time.time()

    if user_id in button_cooldowns:
        if now - button_cooldowns[user_id] < BUTTON_DELAY:
            return False

    button_cooldowns[user_id] = now
    return True



def check_message_spam(user_id: int):

    now = time.time()

    if user_id in message_cooldowns:
        if now - message_cooldowns[user_id] < MESSAGE_DELAY:
            return False

    message_cooldowns[user_id] = now
    return True



def get_user_info(user):

    username = (
        f"@{user.username}"
        if user.username
        else "нет username"
    )

    return (
        f"Telegram: {username}\n"
        f"ID: {user.id}"
    )



# =========================
# FSM СОСТОЯНИЯ
# =========================

class Form(StatesGroup):
    waiting_nick = State()
    waiting_mods = State()
    waiting_admin_reply = State()
    waiting_questionnaire = State()


# =========================
# КНОПКИ
# =========================

menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Вступление",
                callback_data="join"
            )
        ],
        [
            InlineKeyboardButton(
                text="Моды",
                callback_data="mods"
            )
        ],
        [
            InlineKeyboardButton(
                text="Анкетник",
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
                    text="💬 Ответить игроку",
                    callback_data=f"reply_{user_id}"
                )
            ]
        ]
    )



# =========================
# START
# =========================

@router.message(Command("start"))
async def start(message: Message):

    await message.answer(
        'Вас приветствует многофункциональный бот сервера '
        '<a href="https://t.me/MLADAB0SNA">Mlada Bosna</a>!\n\n'
        '1) <b>Вступление:</b> регистрация для новых игроков.\n'
        '2) <b>Моды:</b> [<i>Временно</i>] здесь можно предложить желаемые моды для добавления на сервер. Полный список предложений без указания отправителей будет отправлен в чат сервера для обсуждения. После этого пройдет голосование.',
        reply_markup=menu,
        parse_mode=ParseMode.HTML
    )



# =========================
# ВСТУПЛЕНИЕ
# =========================

@router.callback_query(lambda call: call.data == "join")
async def joining(
    call: CallbackQuery,
    state: FSMContext,
    bot: Bot
):

    user_id = call.from_user.id


    if not check_button_spam(user_id):

        await call.answer(
            "нет",
            show_alert=True
        )

        return


    current_state = await state.get_state()

    if current_state:

        await call.answer(
            "Вы уже заполняете заявку.",
            show_alert=True
        )

        return


    await state.set_state(Form.waiting_nick)


    await call.message.answer(
        "Пожалуйста, укажите свой ник в игре."
    )


    await bot.send_message(
        LOG_CHAT_ID,
        f"📝 Начата заявка на вступление\n\n"
        f"{get_user_info(call.from_user)}"
    )


    await call.answer()



# =========================
# МОДЫ
# =========================

@router.callback_query(lambda call: call.data == "mods")
async def mods(
    call: CallbackQuery,
    state: FSMContext,
    bot: Bot
):

    user_id = call.from_user.id


    if not check_button_spam(user_id):

        await call.answer(
            "нет",
            show_alert=True
        )

        return


    current_state = await state.get_state()

    if current_state:

        await call.answer(
            "Вы уже заполняете заявку.",
            show_alert=True
        )

        return


    await state.set_state(Form.waiting_mods)


    await call.message.answer(
        "Пожалуйста, укажите полные названия модов. Не забывайте, что на сервер планируется добавить минимальное их количество."
    )


    await bot.send_message(
        LOG_CHAT_ID,
        f"🧩 Открыто предложение модов\n\n"
        f"{get_user_info(call.from_user)}"
    )


    await call.answer()

# =========================
# АНКЕТНИК
# =========================

@router.callback_query(lambda call: call.data == "questionnaire")
async def questionnaire(
    call: CallbackQuery,
    state: FSMContext
):

    user_id = call.from_user.id


    if not check_button_spam(user_id):

        await call.answer(
            "нет",
            show_alert=True
        )

        return


    current_state = await state.get_state()

    if current_state:

        await call.answer(
            "Вы уже заполняете анкету.",
            show_alert=True
        )

        return


    await state.set_state(Form.waiting_questionnaire)


    await call.message.answer(
        "Пожалуйста, заполните анкету по шаблону:"
    )


    await call.answer()

# =========================
# ПОЛУЧЕНИЕ НИКА
# =========================

@router.message(Form.waiting_nick)
async def get_nick(
    message: Message,
    state: FSMContext,
    bot: Bot
):


    if not check_message_spam(message.from_user.id):

        await message.answer(
            "Слишком много сообщений. Подождите."
        )

        return



    if not message.text:

        await message.answer(
            "Отправьте текст."
        )

        return



    if len(message.text) > 50:

        await message.answer(
            "Ник слишком длинный."
        )

        return



    text = (
        "🟢 Новая заявка\n\n"
        f"Ник: {message.text}\n"
        f"{get_user_info(message.from_user)}"
    )


    await bot.send_message(
        REQUESTS_CHAT_ID,
        text,
        reply_markup=reply_keyboard(message.from_user.id)
    )


    await bot.send_message(
        LOG_CHAT_ID,
        f"✅ Заявка отправлена\n"
        f"{get_user_info(message.from_user)}\n"
        f"Ник: {message.text}"
    )


    await message.answer(
        "Заявка отправлена."
    )


    await state.clear()



# =========================
# ПОЛУЧЕНИЕ МОДОВ
# =========================

@router.message(Form.waiting_mods)
async def get_mods(
    message: Message,
    state: FSMContext,
    bot: Bot
):


    if not check_message_spam(message.from_user.id):

        await message.answer(
            "Слишком много сообщений. Подождите."
        )

        return



    if not message.text:

        await message.answer(
            "Отправьте текст."
        )

        return



    if len(message.text) > 1000:

        await message.answer(
            "Сообщение слишком длинное."
        )

        return



    text = (
        "🧩 Новое предложение модов\n\n"
        f"{get_user_info(message.from_user)}\n\n"
        f"{message.text}"
    )


    await bot.send_message(
        REQUESTS_CHAT_ID,
        text,
        reply_markup=reply_keyboard(message.from_user.id)
    )


    await bot.send_message(
        LOG_CHAT_ID,
        f"✅ Предложение модов отправлено\n"
        f"{get_user_info(message.from_user)}"
    )


    await message.answer(
        "Предложение отправлено."
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


    if not check_message_spam(message.from_user.id):

        await message.answer(
            "Слишком много сообщений. Подождите."
        )

        return



    if not message.text and not message.photo:

        await message.answer(
            "Отправьте анкету."
        )

        return



    # Текст перед анкетой
    prefix = (
        "📋 Новая анкета\n\n"
        f"{get_user_info(message.from_user)}\n\n"
    )



    # =========================
    # ЕСЛИ АНКЕТА ТЕКСТОМ
    # =========================

    if message.text:

        await bot.send_message(
            REQUESTS_CHAT_ID,
            prefix
        )

        await bot.copy_message(
            chat_id=REQUESTS_CHAT_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=reply_keyboard(message.from_user.id)
        )



    # =========================
    # ЕСЛИ АНКЕТА С КАРТИНКОЙ
    # =========================

    elif message.photo:

        await bot.send_message(
            REQUESTS_CHAT_ID,
            prefix
        )

        await bot.copy_message(
            chat_id=REQUESTS_CHAT_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=reply_keyboard(message.from_user.id)
        )



    await bot.send_message(
        LOG_CHAT_ID,
        f"📋 Анкета отправлена\n"
        f"{get_user_info(message.from_user)}"
    )


    await message.answer(
        "Анкета отправлена."
    )


    await state.clear()

# =========================
# ОТВЕТ АДМИНИСТРАТОРА
# =========================

@router.callback_query(lambda call: call.data.startswith("reply_"))
async def reply_user(
    call: CallbackQuery,
    state: FSMContext
):

    user_id = int(call.data.split("_")[1])


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

    user_id = data["reply_user_id"]


    await bot.send_message(
        user_id,
        f"{message.text}"
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
# ЗАПУСК
# =========================

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