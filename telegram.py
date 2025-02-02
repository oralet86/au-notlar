import asyncio
from global_variables import BOT_TOKEN, logger
from aiogram import Bot, Dispatcher, Router, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    Message,
    MenuButtonCommands,
    BotCommand,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.types.callback_query import CallbackQuery
import manager as m

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()

# Create a router for message handlers
router = Router()
dp.include_router(router)


@router.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with "/start" command
    """
    text = (
        f"Merhaba, {html.bold(message.from_user.full_name)}\n"
        "Notları takip edilen bölümleri görmek için: /bolumler\n"
        "Tüm komutları aşağıdaki menüye tıklayarak görebilirsiniz."
    )
    await message.answer(text)
    return


@router.message(Command("bolumler"))
async def bolumler_handler(message: Message) -> None:
    """
    This handler recieves messages with "/bolumler" command
    """
    inline_keyboard = [
        [InlineKeyboardButton(text=name, callback_data=f"dept_{id}")]
        for id, name in m.get_departments()
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    text = (
        "Anlık notları takip edilen bölümler aşağıdadır: \n"
        "Herhangi bir bölümün takip edilen derslerini görmek ve o dersin bildirimlerini almak için o bölüme tıklabilirsiniz."
    )
    await message.answer(text, reply_markup=keyboard)


@router.message(Command("bildirimlerim"))
async def bildirimlerim_handler(message: Message) -> None:
    """
    This handler revieces messages with "/bildirimlerim" command.

    """
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=m.get_lecture_name(id), callback_data=f"lecture_{id}"
            )
        ]
        for id in m.get_user_notifications(message.from_user.id)
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    text = (
        "Bildirimlerini takip ettiğiniz bölümler aşağıdadır: \n"
        "Herhangi bir bölüme tıklayarak bildirimlerini almayı bırakabilirsiniz."
    )
    await message.answer(text, reply_markup=keyboard)


@router.callback_query()
async def callback_matcher(call: CallbackQuery):
    prefix = call.data[: call.data.find("_")]
    data = call.data[call.data.find("_") + 1 :]
    match prefix:
        case "dept":
            await dept_callback(call, data)
            await call.message.delete()
        case "lecture":
            await lecture_callback(call, data)
            await call.answer()


@router.message(Command("hakkinda"))
async def hakkinda_handler(message: Message) -> None:
    """
    This handler recieves messages with "/hakkinda" command
    """
    await message.answer("hakkinda")


@router.message(Command("ayarlar"))
async def ayarlar_handler(message: Message) -> None:
    """
    This handler recieves messages with "/ayarlar" command
    """
    await message.answer("ayarlar")


async def dept_callback(call: CallbackQuery, data: str):
    inline_keyboard = [
        [InlineKeyboardButton(text=name, callback_data=f"lecture_{id}")]
        for id, name in m.get_lectures(data)
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    text = (
        f"{html.bold(f"{m.get_department_name(data)}")} "
        "bölümünde takip edilen dersler aşağıdadır: \n"
        "İstediğiniz derse tıklayarak bu dersin not açıklanma bildirimini etkinleştirebilirsiniz."
    )
    await call.message.answer(text, reply_markup=keyboard)


async def lecture_callback(call: CallbackQuery, data: str):
    user_id = call.from_user.id
    if not m.does_user_follow_lecture(data, user_id):
        m.add_lecture_notification(data, user_id)
        await call.message.answer(
            f"{html.bold(m.get_lecture_name(data))} ders bildirim listenize eklendi! Bu derse yeni bir not girilince bildirim alacaksınız."
        )
    else:
        m.delete_lecture_notification(data, user_id)
        await call.message.answer(
            f"{html.bold(m.get_lecture_name(data))} ders bildirim listenizden çıkarıldı! Artık bu ders ile ilgili bildirimler almayacaksınız."
        )


async def send_mass_notifications(
    user_ids: list[str], lecture_name: str, exam_name: str
):
    for user_id in user_ids:
        await send_notification(user_id, lecture_name, exam_name)


async def send_notification(
    user_id: str,
    lecture_name: str,
    exam_name: str,
):
    text = f"{html.bold(lecture_name)} dersinde {html.bold(exam_name)} sınavına dair bilgi girildi."
    await Bot.send_message(chat_id=user_id, text=text)


async def start() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


async def set_bot_commands(bot: Bot):
    """Defines the list of commands available in the bot menu."""
    commands = [
        BotCommand(command="bolumler", description="OBS takibi yapılan bölümler"),
        BotCommand(
            command="bildirimlerim",
            description="Bildirimlerini takip ettiğiniz dersler",
        ),
        BotCommand(command="hakkinda", description="Bu bot hakkında bilgiler"),
        BotCommand(command="ayarlar", description="Bot ayarları"),
    ]
    await bot.set_my_commands(commands)


async def set_menu_button(bot: Bot):
    """Sets the menu button to show available commands."""
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())


async def menu():
    bot = Bot(token=BOT_TOKEN)

    # Set commands and menu button
    await set_bot_commands(bot)
    await set_menu_button(bot)

    print("Commands and menu button set successfully.")
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(start())
