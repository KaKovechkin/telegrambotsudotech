from aiogram.fsm.state import State, StatesGroup

class AddTask(StatesGroup):
    waiting_for_text = State()
    waiting_for_date = State()
    waiting_for_time = State()

class AIAssistant(StatesGroup):
    waiting_for_question = State()
