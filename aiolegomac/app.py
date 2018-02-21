import asyncio
import datetime
import functools
import logging
import pathlib
import apigpio
import pytz
import yaml
from aiohttp import web
from .api import setup_routes
from .aioepd import Clock, EPD
from .middlewares import setup_middlewares


BUTTON_GPIO = 22
PROJECT_ROOT = pathlib.Path(__file__).parent
logger = logging.getLogger('aiohttp.server')


def on_input(app, gpio, level, tick):
    """Callback called when pressing the button on the e-paper display"""
    logger.info('on_input {} {} {}'.format(gpio, level, tick))
    if app['clock'].done():
        logger.info('restart clock')
        app['clock'] = app.loop.create_task(display_clock(app))


async def display_clock(app):
    """Background task to display clock every minute"""
    clock = Clock(app['epd'])
    first_start = True
    try:
        while True:
            while True:
                now = datetime.datetime.now(app['timezone'])
                if now.second == 0 or first_start:
                    first_start = False
                    break
                await asyncio.sleep(0.5)
            logger.debug('display clock')
            await clock.display(now)
    except asyncio.CancelledError:
        logger.debug('display clock cancel')


async def start_background_tasks(app):
    app['pi'] = apigpio.Pi(app.loop)
    address = (app['config']['pigpiod_host'], app['config']['pigpiod_port'])
    await app['pi'].connect(address)
    await app['pi'].set_mode(BUTTON_GPIO, apigpio.INPUT)
    app['cb'] = await app['pi'].add_callback(
            BUTTON_GPIO,
            edge=apigpio.RISING_EDGE,
            func=functools.partial(on_input, app))
    app['epd'] = await EPD.create(auto=True)
    app['clock'] = app.loop.create_task(display_clock(app))


async def cleanup_background_tasks(app):
    app['clock'].cancel()
    await app['clock']
    await app['pi'].stop()


def init_app():
    """Create and return the aiohttp Application object"""
    with open(PROJECT_ROOT / '..' / 'config' / 'legomac.yml') as f:
        config = yaml.load(f)
    app = web.Application()
    app['config'] = config
    app['timezone'] = pytz.timezone(config['timezone'])
    setup_routes(app)
    setup_middlewares(app)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    return app


def run():
    """Run the aiohttp server"""
    logging.basicConfig(level=logging.INFO)
    app = init_app()
    web.run_app(app, host=app['config']['host'], port=app['config']['port'])
