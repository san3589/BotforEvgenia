from aiogram import Router, types, F, Bot
from aiogram.exceptions import TelegramNetworkError
from aiogram.filters import Command, StateFilter
from aiogram.types import FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import pandas as pd

from filters.chat_type import ChatTypeFilter, IsAdmin
from kb.reply import ReplyKeyboardFactory, del_kb
from user_chat import thi_kb

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(['private']), IsAdmin())

adminkb = ReplyKeyboardFactory.create_keyboard(["Выгрузить таблицу", "Сделать рассылку"])


class AdminState(StatesGroup):
    choice = State()
    sender = State()
    message = State()


@admin_router.message(StateFilter(None), Command('admin'))
async def get_hello_admin(message: types.Message, state: FSMContext):
    await message.answer("Что вы хотите сделать?", reply_markup=adminkb)
    await state.set_state(AdminState.choice)


@admin_router.message(AdminState.choice, F.text == "Выгрузить таблицу")
async def get_table(message: types.Message, state: FSMContext):
    await message.answer(text="Вот выгрузка: ")
    try:
        document = FSInputFile('data.xlsx')
        await message.answer_document(document)
    except TelegramNetworkError:
        await message.answer(text="Файл не найден")

    await state.clear()


@admin_router.message(AdminState.choice, F.text == "Сделать рассылку")
async def get_cat(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста выберите интеграцию для рассылки", reply_markup=thi_kb)
    await state.set_state(AdminState.message)


@admin_router.message(AdminState.message, F.text)
async def get_message(message: types.Message, state: FSMContext):
    await state.update_data(type=message.text)
    await message.answer("Пожалуйста, введите сообщение для рассылки:", reply_markup=del_kb)
    await state.set_state(AdminState.sender)


@admin_router.message(AdminState.sender, F.text)
async def send_message(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(message=message.text)
    data = await state.get_data()
    type_users = data['type']
    df = pd.read_excel('data.xlsx')

    # Фильтрация данных
    filtered_df = df[df['Интересующие интеграции'] == type_users]

    # Отправка сообщений
    for _, row in filtered_df.iterrows():
        user_id = row['User ID']
        try:
            await bot.send_message(user_id, data["message"])
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    # Подтверждение
    await message.answer("Сообщения отправлены пользователям, соответствующим вашему запросу.")
    await state.clear()

