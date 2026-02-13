"""Rental booking FSM states."""

from aiogram.fsm.state import State, StatesGroup


class BookingForm(StatesGroup):
    select_vehicle = State()
    confirm = State()


class ExtendForm(StatesGroup):
    enter_time = State()
