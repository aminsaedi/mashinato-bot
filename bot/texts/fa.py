"""Persian (Farsi) UI strings - single source of truth for all bot text."""

# General
WELCOME = "🚗 به ربات ماشین‌اتو خوش آمدید!"
LOGIN_REQUIRED = "برای استفاده از ربات، ابتدا وارد شوید."
LOGIN_BUTTON = "🔑 ورود"
LOGIN_SUCCESS = "✅ با موفقیت وارد شدید!"
LOGIN_FAILED = "❌ خطا در ورود. لطفاً دوباره تلاش کنید."
LOGOUT_SUCCESS = "✅ با موفقیت خارج شدید."
LOGOUT_CONFIRM = "آیا مطمئنید که می‌خواهید خارج شوید؟"
SESSION_EXPIRED = "⏰ نشست شما منقضی شده است. لطفاً دوباره وارد شوید."

# Main Menu
MAIN_MENU_TITLE = "🚗 ماشین‌اتو"
ACTIVE_ACCOUNT = "حساب فعال: {account}"
MENU_RENTAL = "🚗 اجاره فعلی"
MENU_SEARCH = "🔍 جستجو"
MENU_OPTIMIZATION = "📊 بهینه‌سازی"
MENU_VEHICLES = "🚙 خودروها"
MENU_ACCOUNTS = "👤 حساب‌ها"
MENU_SETTINGS = "⚙️ تنظیمات"
MENU_ADMIN = "🔧 مدیریت سیستم"
MENU_HOME = "🏠 منوی اصلی"

# Account
SELECT_ACCOUNT = "حساب مورد نظر را انتخاب کنید:"
ACCOUNT_SWITCHED = "✅ حساب به {account} تغییر کرد."
ACCOUNT_STATUS_TITLE = "👤 وضعیت حساب: {account}"
NEXT_FREE_TIME = "⏰ زمان بعدی آزاد: {time}"
NO_ACCOUNTS = "هیچ حسابی در دسترس نیست."

# Search
SEARCH_TITLE = "🔍 جستجوی خودرو"
SEARCH_SEND_LOCATION = "📍 لوکیشن خود را ارسال کنید یا مختصات را وارد کنید."
SEARCH_SELECT_RADIUS = "📏 شعاع جستجو را انتخاب کنید:"
SEARCH_FILTERS_TITLE = "🔧 فیلترهای جستجو:"
SEARCH_FILTER_NO_PRIUS = "بدون پریوس"
SEARCH_FILTER_NO_EV = "بدون برقی"
SEARCH_FILTER_SNOW = "پروموشن برف"
SEARCH_START = "▶️ شروع جستجو"
SEARCH_STOP = "⏹ توقف جستجو"
SEARCH_CONFIRM = "تأیید و شروع جستجو"
SEARCH_CANCELLED = "❌ جستجو لغو شد."
SEARCH_STARTED = "✅ جستجو شروع شد."
SEARCH_STOPPED = "⏹ جستجو متوقف شد."
SEARCH_NO_ACTIVE = "جستجوی فعالی وجود ندارد."
SEARCH_STATUS_TITLE = "🔍 وضعیت جستجو"
SEARCH_STATUS_RUNNING = "در حال جستجو..."
SEARCH_STATUS_FOUND = "✅ خودرو پیدا شد!"
SEARCH_STATUS_STOPPED = "متوقف شده"
SEARCH_SUMMARY = "📍 موقعیت: {lat}, {lng}\n" "📏 شعاع: {radius} کیلومتر\n" "🔧 فیلترها: {filters}"
SEARCH_CUSTOM_RADIUS = "سفارشی..."
SEARCH_RADIUS_PROMPT = "شعاع را به متر وارد کنید:"

# Optimization
OPT_TITLE = "📊 بهینه‌سازی خودرو"
OPT_SELECT_WEIGHTS = "⚖️ نسبت وزن‌ها را انتخاب کنید:"
OPT_BALANCED = "⚖️ متعادل (50/50)"
OPT_DISTANCE = "📏 فاصله (70/30)"
OPT_PREFERENCE = "⭐ ترجیح (30/70)"
OPT_CUSTOM = "🔧 سفارشی"
OPT_MIN_IMPROVEMENT = "حداقل بهبود امتیاز را انتخاب کنید:"
OPT_PREFERENCES_TITLE = "ترجیحات بهینه‌سازی:"
OPT_AWD = "AWD"
OPT_MODEL = "مدل"
OPT_PROPULSION = "سوخت"
OPT_PROMOTIONS = "تبلیغات"
OPT_BATTERY = "باتری"
OPT_STARTED = "✅ بهینه‌سازی شروع شد."
OPT_STOPPED = "⏹ بهینه‌سازی متوقف شد."
OPT_NO_ACTIVE = "بهینه‌سازی فعالی وجود ندارد."
OPT_STATUS_TITLE = "📊 وضعیت بهینه‌سازی"

# Rental
RENTAL_TITLE = "🚗 اجاره فعال"
RENTAL_NO_ACTIVE = "اجاره فعالی ندارید."
RENTAL_VEHICLE = "خودرو: {model} #{number}"
RENTAL_START_TIME = "شروع: {time}"
RENTAL_END_TIME = "پایان: {time}"
RENTAL_STATUS = "وضعیت: {status}"
RENTAL_START_TRIP = "▶️ شروع سفر"
RENTAL_EXTEND = "⏰ تمدید"
RENTAL_FUEL_CARD = "⛽ کارت سوخت"
RENTAL_CANCEL = "❌ لغو"
RENTAL_TRANSFER = "🔄 انتقال"
RENTAL_CONTINUE = "➡️ ادامه"
RENTAL_CANCEL_CONFIRM = "آیا مطمئنید که می‌خواهید اجاره را لغو کنید؟"
RENTAL_CANCELLED = "✅ اجاره لغو شد."
RENTAL_EXTENDED = "✅ اجاره تمدید شد تا {time}."
RENTAL_TRIP_STARTED = "✅ سفر شروع شد."
RENTAL_TRIP_ENDED = "✅ سفر پایان یافت."
RENTAL_FUEL_PIN = "⛽ پین کارت سوخت: {pin}"
RENTAL_TRANSFERRED = "✅ اجاره به حساب {account} منتقل شد."
RENTAL_CONTINUED = "✅ اجاره از حساب {account} ادامه یافت."
RENTAL_END_TRIP = "⏹ پایان سفر"
RENTAL_EXTEND_PROMPT = "زمان پایان جدید را وارد کنید (مثلاً: 18:30):"
RENTAL_TRANSFER_SELECT = "حساب مقصد را انتخاب کنید:"

# Vehicles
VEHICLES_TITLE = "🚙 لیست خودروها"
VEHICLE_DETAIL = (
    "🚙 {model} #{number}\n" "📍 {location}\n" "⛽ {fuel_type}\n" "🔋 باتری: {battery}%"
)
VEHICLES_EMPTY = "خودرویی یافت نشد."

# Webhooks
WEBHOOK_TITLE = "🔔 وب‌هوک‌ها"
WEBHOOK_CREATE = "➕ ایجاد وب‌هوک"
WEBHOOK_EMPTY = "هیچ وب‌هوکی ثبت نشده."
WEBHOOK_NAME_PROMPT = "نام وب‌هوک را وارد کنید:"
WEBHOOK_URL_PROMPT = "آدرس URL وب‌هوک را وارد کنید:"
WEBHOOK_CREATED = "✅ وب‌هوک ایجاد شد."
WEBHOOK_DELETED = "✅ وب‌هوک حذف شد."
WEBHOOK_UPDATED = "✅ وب‌هوک به‌روزرسانی شد."
WEBHOOK_TEST_SENT = "✅ تست ارسال شد."

# Audit
AUDIT_TITLE = "📋 لاگ‌های حسابرسی"
AUDIT_EMPTY = "لاگی یافت نشد."
AUDIT_FILTER = "🔍 فیلتر"
AUDIT_DETAIL = (
    "📋 لاگ #{id}\n"
    "👤 کاربر: {user}\n"
    "📌 عملیات: {action}\n"
    "📅 زمان: {timestamp}\n"
    "📊 وضعیت: {status}"
)

# Policies
POLICIES_TITLE = "🛡️ سیاست‌های حساب"
POLICIES_EMPTY = "سیاستی تعریف نشده."

# Subscriptions
SUBSCRIPTIONS_TITLE = "💳 اشتراک‌ها"

# Settings
SETTINGS_TITLE = "⚙️ تنظیمات"
SETTINGS_WEBHOOKS = "🔔 وب‌هوک‌ها"
SETTINGS_AUDIT = "📋 لاگ‌ها"
SETTINGS_POLICIES = "🛡️ سیاست‌ها"
SETTINGS_SUBSCRIPTIONS = "💳 اشتراک"
SETTINGS_INTERVALS = "⏱️ فواصل زمانی"
SETTINGS_NOTIFICATIONS = "🔔 اعلان‌ها"

# Admin
ADMIN_TITLE = "🔧 مدیریت سیستم"
ADMIN_DISPATCHER = "📡 دیسپچر"
ADMIN_DROPLETS = "💧 دراپلت‌ها"
ADMIN_IPV6 = "🌐 IPv6"
ADMIN_MONITORING = "📊 مانیتورینگ"
ADMIN_HEALTH = "💚 سلامت"
ADMIN_VERSION = "📌 نسخه"
ADMIN_NOT_AUTHORIZED = "⛔ شما دسترسی ادمین ندارید."

# Notifications
NOTIF_SEARCH_COMPLETED = "✅ جستجو تکمیل شد!\n🚙 {vehicle}\n📍 {location}"
NOTIF_RENTAL_BOOKED = "✅ اجاره رزرو شد!\n🚙 {vehicle}"
NOTIF_OPTIMIZATION_SWAP = "🔄 خودرو بهتر پیدا شد!\n🚙 {vehicle}\n📊 امتیاز: {score}"

# Pagination
PAGE_PREV = "◀️ قبلی"
PAGE_NEXT = "بعدی ▶️"
PAGE_INFO = "{current} از {total}"

# Common
CONFIRM = "✅ تأیید"
CANCEL = "❌ انصراف"
BACK = "🔙 بازگشت"
YES = "بله"
NO = "خیر"
ERROR_GENERIC = "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید."
ERROR_API = "❌ خطا در ارتباط با سرور: {error}"
LOADING = "⏳ در حال بارگذاری..."
ENABLED = "✅"
DISABLED = "❌"
