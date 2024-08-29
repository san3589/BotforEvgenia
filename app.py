import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.strategy import FSMStrategy
from aiogram.filters.command import CommandStart
from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(find_dotenv())
from kb.reply import ReplyKeyboardFactory
from handlers.user_chat import user_router
from handlers.admin import admin_router


TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(fsm_strategy=FSMStrategy.USER_IN_CHAT)
dp.include_router(user_router)
dp.include_router(admin_router)


bot.my_admins_list = [os.getenv("ADMIN_ID")]

start_kb = ReplyKeyboardFactory.create_keyboard(["Заполнить анкету"])


@dp.message(CommandStart())
async def start_message(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(text="""Здравствуйте! 
🔥NVis private – закрытый канал для тех, кто интересуется нативными интеграциями. 

На канале мы размещаем анонсы проектов с реальными  данными, ценами, скидками. 

😎Эта информация не для широкой публики, поэтому мы просим потратить минуту своего времени и заполнить анкету. 

Так мы будем знать, что наши анонсы получают те, кто действительно интересуется интеграциями и сможем делать подборки, учитывая ваши интересы.""", reply_markup=start_kb)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

asyncio.run(main())
