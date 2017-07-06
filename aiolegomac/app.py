import logging
import pathlib
import yaml
from aiohttp import web
from .api import setup_routes
from .middlewares import setup_middlewares


PROJECT_ROOT = pathlib.Path(__file__).parent


def init_app():
    """Create and return the aiohttp Application object"""
    with open(PROJECT_ROOT / '..' / 'config' / 'legomac.yml') as f:
        config = yaml.load(f)
    app = web.Application()
    app['config'] = config
    setup_routes(app)
    setup_middlewares(app)
    return app


def run():
    """Run the aiohttp server"""
    logging.basicConfig(level=logging.DEBUG)
    app = init_app()
    web.run_app(app, host=app['config']['host'], port=app['config']['port'])
