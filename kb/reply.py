from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


class ReplyKeyboardFactory:
    @staticmethod
    def create_keyboard(buttons: list[str]) -> ReplyKeyboardMarkup:

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=button) for button in buttons[i:i + 2]]
                for i in range(0, len(buttons), 2)
            ],
            resize_keyboard=True
        )
        return keyboard
del_kb = ReplyKeyboardRemove()