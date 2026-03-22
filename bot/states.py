from aiogram.fsm.state import State, StatesGroup


class SetupStates(StatesGroup):
    waiting_start_language = State()
    waiting_api_key = State()
    waiting_model = State()
    waiting_base_url = State()
    waiting_custom_instruction_name = State()
    waiting_custom_instruction_name_update = State()
    waiting_custom_instructions = State()
    waiting_custom_instructions_update = State()
