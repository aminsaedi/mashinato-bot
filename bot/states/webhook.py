"""Webhook form FSM states."""

from aiogram.fsm.state import State, StatesGroup


class WebhookForm(StatesGroup):
    enter_name = State()
    enter_url = State()
    select_events = State()
    confirm = State()
