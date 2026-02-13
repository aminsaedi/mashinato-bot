"""Search wizard FSM states."""

from aiogram.fsm.state import State, StatesGroup


class SearchForm(StatesGroup):
    select_account = State()
    send_location = State()
    select_radius = State()
    custom_radius = State()
    select_filters = State()
    confirm = State()
