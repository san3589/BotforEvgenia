from aiogram import Router, types, F, Bot
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import pandas as pd
import gspread

from filters.chat_type import ChatTypeFilter
from kb.reply import del_kb, ReplyKeyboardFactory

gc = gspread.service_account(filename="nvis2024-b3995bc06efd.json")
wks = gc.open().sheet1


async def check_user_subscription(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Ошибка при проверке подписки: {e}")
        return False


def add_to_excel(data: dict):
    try:
        df = pd.read_excel('data.xlsx', engine='openpyxl')  # Указываем движок openpyxl
    except FileNotFoundError:
        # Если файла нет, создаём новый DataFrame
        df = pd.DataFrame(
            columns=["User ID", "Представитель компании или эксперт", "Название компании", "Ниша",
                     "Интересующие интеграции"])

        # Конвертируем входные данные в DataFrame
    new_df = pd.DataFrame([data])  # Добавляем [] вокруг data, чтобы создать DataFrame с одной строкой

    # Соединяем старые и новые данные
    df = pd.concat([df, new_df], ignore_index=True)
    wks.update([df.columns.values.tolist()] + df.values.tolist())

    # Сохраняем файл
    df.to_excel('data.xlsx', index=False, engine='openpyxl')


user_router = Router()
user_router.message.filter(ChatTypeFilter(['private']))

first_kb = ReplyKeyboardFactory.create_keyboard(["Эксперт", "Компания"])
second_kb = ReplyKeyboardFactory.create_keyboard(["ТВ", "Радио", "Кино и сериалы", "Мероприятия", "Интернет", "Все предложения"])
thi_kb = ReplyKeyboardFactory.create_keyboard(["ТВ", "Радио", "Кино и сериалы", "Мероприятия", "Интернет", "Все предложения"])


class ChatState(StatesGroup):
    choice = State()
    expert = State()
    integration_expert = State()
    company = State()
    company_name = State()
    integration_company = State()
    wait_for_subscribe_exp = State()
    wait_for_subscribe_company = State()


@user_router.message(State(None), F.text == "Заполнить анкету")
async def start_chat(message: types.Message, state: FSMContext):
    await message.answer(text="Вы представитель компании или эксперт?", reply_markup=first_kb)
    await state.set_state(ChatState.choice)


@user_router.message(ChatState.choice, F.text == "Эксперт")
async def second_question(message: types.Message, state: FSMContext):
    await state.update_data(choice=message.text)
    await message.answer(text="Ваша ниша:", reply_markup=del_kb)
    await state.set_state(ChatState.expert)


@user_router.message(ChatState.choice, F.text == "Компания")
async def second_question(message: types.Message, state: FSMContext):
    await state.update_data(choice=message.text)
    await message.answer(text="Ваша ниша:", reply_markup=del_kb)
    await state.set_state(ChatState.company)


@user_router.message(ChatState.expert, F.text)
async def second_question(message: types.Message, state: FSMContext):
    await state.update_data(type=message.text)
    await message.answer(text="Какие интеграции вам интересны? ", reply_markup=second_kb)
    await state.set_state(ChatState.integration_expert)


@user_router.message(ChatState.company, F.text)
async def second_question(message: types.Message, state: FSMContext):
    await state.update_data(type=message.text)
    await message.answer(text="Название компании:", reply_markup=del_kb)
    await state.set_state(ChatState.company_name)


@user_router.message(ChatState.company_name, F.text)
async def second_question(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(text="Какие интеграции вам интересны? ", reply_markup=second_kb)
    await state.set_state(ChatState.integration_company)


@user_router.message(ChatState.integration_company, F.text)
async def t_question_comp(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(integration_type=message.text)
    channel_link = "https://t.me/+UXg95B9mR3UzMGQy"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Проверить подписку", callback_data="check_subscription")]])
    await message.answer(text=f"Ваша ссылка на канал. [Подпишитесь]({channel_link}), чтобы получить подарок",
                         reply_markup=keyboard, parse_mode="Markdown")
    data = await state.get_data()
    table_data = {}
    table_data["User ID"] = message.from_user.id
    table_data["Представитель компании или эксперт"] = data["choice"]
    table_data["Название компании"] = data["name"]
    table_data["Ниша"] = data["type"]
    table_data["Интересующие интеграции"] = data["integration_type"]
    add_to_excel(table_data)
    await state.set_state(ChatState.wait_for_subscribe_company)


@user_router.callback_query(ChatState.wait_for_subscribe_company, F.data == "check_subscription")
async def get_message_chat_comp(query: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = query.from_user.id
    chat_id = -1002239802320
    if await check_user_subscription(bot, chat_id, user_id):
        digest = "https://t.me/c/2239802320/6"
        await query.message.answer(
            f"Спасибо за подписку!\nВот ваш [Дайджест]({digest}) предложений для экспертов",
            parse_mode="Markdown", reply_markup=del_kb
        )
        await state.clear()
    else:
        await query.message.answer("Подписка не подтверждена, попробуйте еще раз.")



@user_router.message(ChatState.integration_expert, F.text)
async def t_question_exp(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(integration_type=message.text)
    channel_link = "https://t.me/+UXg95B9mR3UzMGQy"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Проверить подписку", callback_data="check_subscription")]])
    await message.answer(text=f"Ваша ссылка на канал. [Подпишитесь]({channel_link}), чтобы получить подарок",
                         reply_markup=keyboard, parse_mode="Markdown")
    data = await state.get_data()
    table_data = {}
    table_data["User ID"] = message.from_user.id
    table_data["Представитель компании или эксперт"] = data["choice"]
    table_data["Ниша"] = data["type"]
    table_data["Интересующие интеграции"] = data["integration_type"]
    add_to_excel(table_data)
    await state.set_state(ChatState.wait_for_subscribe_exp)


@user_router.callback_query(ChatState.wait_for_subscribe_exp, F.data == "check_subscription")
async def get_message_chat_exp(query: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = query.from_user.id
    chat_id = -1002239802320  # Замените на ваш ID канала

    if await check_user_subscription(bot, chat_id, user_id):
        digest = "https://t.me/c/2239802320/5"
        await query.message.answer(
            f"Спасибо за подписку!\nВот ваш [Дайджест]({digest}) предложений для экспертов",
            parse_mode="Markdown", reply_markup=del_kb
        )
        await state.clear()
    else:
        await query.message.answer("Подписка не подтверждена. Попробуйте еще раз")





