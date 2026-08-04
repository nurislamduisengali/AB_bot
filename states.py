from aiogram.fsm.state import StatesGroup, State


class Submission(StatesGroup):
    waiting_for_content = State()     # собираем основной контент
    waiting_for_extra = State()       # для задачи: решение + источник