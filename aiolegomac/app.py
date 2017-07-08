import asyncio
import datetime
import logging
import pathlib
import yaml
from aiohttp import web
from .api import setup_routes
from .aioepd import Clock, EPD
from .middlewares import setup_middlewares


PROJECT_ROOT = pathlib.Path(__file__).parent
logger = logging.getLogger('aiohttp.server')


async def display_clock(app):
    """Background task to display clock every second"""
    clock = Clock(app['epd'])
    first_start = True
    try:
        while True:
            while True:
                now = datetime.datetime.today()
                if now.second == 0 or first_start:
                    first_start = False
                    break
                await asyncio.sleep(0.5)
            logger.debug('display clock')
            await clock.display(now)
    except asyncio.CancelledError:
        logger.debug('display clock cancel')


async def start_background_tasks(app):
    app['epd'] = await EPD.create(auto=True)
    app['clock'] = app.loop.create_task(display_clock(app))


async def cleanup_background_tasks(app):
    app['clock'].cancel()
    await app['clock']


def init_app():
    """Create and return the aiohttp Application object"""
    with open(PROJECT_ROOT / '..' / 'config' / 'legomac.yml') as f:
        config = yaml.load(f)
    app = web.Application()
    app['config'] = config
    setup_routes(app)
    setup_middlewares(app)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    return app


def run():
    """Run the aiohttp server"""
    logging.basicConfig(level=logging.DEBUG)
    app = init_app()
    web.run_app(app, host=app['config']['host'], port=app['config']['port'])
