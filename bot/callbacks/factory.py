"""CallbackData factories for type-safe callback routing."""

from aiogram.filters.callback_data import CallbackData


class MenuCB(CallbackData, prefix="menu"):
    action: str


class AccountCB(CallbackData, prefix="acc"):
    action: str
    account: str = ""


class SearchCB(CallbackData, prefix="src"):
    action: str
    value: str = ""


class OptimizationCB(CallbackData, prefix="opt"):
    action: str
    value: str = ""


class RentalCB(CallbackData, prefix="rnt"):
    action: str
    account: str = ""


class TransferCB(CallbackData, prefix="trf"):
    action: str
    account: str = ""


class VehicleCB(CallbackData, prefix="veh"):
    action: str
    vehicle_id: int = 0


class WebhookCB(CallbackData, prefix="whk"):
    action: str
    webhook_id: int = 0


class AuditCB(CallbackData, prefix="aud"):
    action: str
    log_id: int = 0


class PolicyCB(CallbackData, prefix="pol"):
    action: str
    account: str = ""


class SubscriptionCB(CallbackData, prefix="sub"):
    action: str
    account: str = ""


class SettingsCB(CallbackData, prefix="set"):
    action: str


class AdminCB(CallbackData, prefix="adm"):
    action: str
    value: str = ""


class PageCB(CallbackData, prefix="pg"):
    section: str
    page: int = 0


class ConfirmCB(CallbackData, prefix="cfm"):
    action: str
    confirmed: bool = False
