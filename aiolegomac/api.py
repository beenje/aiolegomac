import datetime
import logging
import jwt
from functools import wraps
from aiohttp import helpers, web

logger = logging.getLogger('aiohttp.server')


def login_required(func):
    @wraps(func)
    def wrapper(request):
        if request.user is None:
            return web.HTTPUnauthorized()
        return func(request)
    return wrapper


async def login(request):
    config = request.app['config']
    data = await request.json()
    try:
        user = data['username']
        passwd = data['password']
    except KeyError:
        return web.HTTPBadRequest(reason='Invalid arguments')
    # We have only one user hard-coded in the config file...
    if user != config['username'] or passwd != config['password']:
        return web.HTTPBadRequest(reason='Invalid credentials')
    payload = {
        'user_id': 1,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=config['jwt_exp_delta_seconds'])
    }
    jwt_token = jwt.encode(payload, config['jwt_secret'], config['jwt_algorithm'])
    logger.debug(f'JWT token created for {user}')
    return web.json_response({'token': jwt_token.decode('utf-8')})


@login_required
async def post_message(request):
    if request.content_type != 'application/json':
        return web.HTTPBadRequest()
    data = await request.json()
    try:
        message = data['message']
    except KeyError:
        return web.HTTPBadRequest()
    # cancel the display clock
    request.app['clock'].cancel()
    logger.debug(f'Message received from {request.user}: {message}')
    helpers.ensure_future(request.app['epd'].display_message(message, request.user))
    return web.json_response({'message': message}, status=201)


@login_required
async def index(request):
    return web.json_response({'message': 'Welcome to LegoMac {}!'.format(request.user)})


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_post('/login', login)
    app.router.add_post('/messages', post_message)
