"""Optimization wizard FSM states."""

from aiogram.fsm.state import State, StatesGroup


class OptimizationForm(StatesGroup):
    select_account = State()
    select_weights = State()
    custom_weights = State()
    min_improvement = State()
    custom_improvement = State()
    select_preferences = State()
    confirm = State()
