import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from bot.config import settings
from bot.db.session import init_db
from bot.web.server import create_app

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def setup_routers(dp: Dispatcher) -> None:
    from bot.handlers.account import router as account_router
    from bot.handlers.admin.dispatcher import router as admin_dispatcher_router
    from bot.handlers.admin.droplets import router as admin_droplets_router
    from bot.handlers.admin.ipv6 import router as admin_ipv6_router
    from bot.handlers.admin.monitoring import router as admin_monitoring_router
    from bot.handlers.admin.system import router as admin_system_router
    from bot.handlers.audit import router as audit_router
    from bot.handlers.auth import router as auth_router
    from bot.handlers.common import router as common_router
    from bot.handlers.menu import router as menu_router
    from bot.handlers.optimization import router as optimization_router
    from bot.handlers.policies import router as policies_router
    from bot.handlers.rental import router as rental_router
    from bot.handlers.search import router as search_router
    from bot.handlers.settings import router as settings_router
    from bot.handlers.start import router as start_router
    from bot.handlers.subscriptions import router as subscriptions_router
    from bot.handlers.transfer import router as transfer_router
    from bot.handlers.vehicles import router as vehicles_router
    from bot.handlers.webhooks import router as webhooks_router

    dp.include_routers(
        start_router,
        auth_router,
        menu_router,
        account_router,
        rental_router,
        transfer_router,
        search_router,
        optimization_router,
        vehicles_router,
        common_router,
        webhooks_router,
        audit_router,
        policies_router,
        subscriptions_router,
        settings_router,
        admin_dispatcher_router,
        admin_droplets_router,
        admin_ipv6_router,
        admin_monitoring_router,
        admin_system_router,
    )


def setup_middlewares(dp: Dispatcher) -> None:
    from bot.middlewares.auth import AuthMiddleware
    from bot.middlewares.throttle import ThrottleMiddleware

    dp.message.middleware(ThrottleMiddleware())
    dp.callback_query.middleware(ThrottleMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())


async def main() -> None:
    logger.info("Starting Mashinato Bot...")

    await init_db()
    logger.info("Database initialized")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())
    setup_middlewares(dp)
    setup_routers(dp)

    # Start aiohttp web server (OAuth callback + webhook receiver + health)
    webapp = create_app(bot=bot)
    runner = web.AppRunner(webapp)
    await runner.setup()
    site = web.TCPSite(runner, settings.webhook_server_host, settings.webhook_server_port)
    await site.start()
    logger.info(
        "Web server started on %s:%s",
        settings.webhook_server_host,
        settings.webhook_server_port,
    )

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
